import json
from pathlib import Path
from typing import List

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .server_manager import ServerSettings, manager
from .conversations import Message, store

app = FastAPI(title="BitNet WebUI Backend")

MODELS_DIR = Path(__file__).resolve().parents[2] / "models"
FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"


def _list_models() -> List[str]:
    if not MODELS_DIR.exists():
        return []
    return [str(p.relative_to(MODELS_DIR)) for p in MODELS_DIR.rglob("*.gguf")]


@app.get("/models")
async def get_models():
    """Return available GGUF models under the models directory."""
    return {"models": _list_models()}


class SettingsRequest(BaseModel):
    model: str
    n_predict: int = 4096
    threads: int = 2
    ctx_size: int = 2048
    temperature: float = 0.8
    host: str = "127.0.0.1"
    port: int = 8080


@app.post("/settings")
async def update_settings(req: SettingsRequest):
    settings = ServerSettings(**req.dict())
    manager.restart(settings)
    return {"status": "restarted"}


@app.get("/settings")
def get_settings():
    return {
        "settings": manager.current_settings(),
        "running": manager.is_running(),
    }


class ChatRequest(BaseModel):
    prompt: str
    stream: bool = True


@app.post("/chat")
async def chat(req: ChatRequest):
    if not manager.is_running():
        raise HTTPException(status_code=503, detail="Inference server not running")

    server_url = f"http://{manager.settings.host}:{manager.settings.port}/v1/chat/completions"
    payload = {
        "messages": [{"role": "user", "content": req.prompt}],
        "stream": req.stream,
    }

    if req.stream:
        async def event_stream():
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", server_url, json=payload) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            yield f"{line}\n\n"
        return StreamingResponse(event_stream(), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(server_url, json=payload)
            return resp.json()


class ConversationCreate(BaseModel):
    title: str = "New Conversation"


@app.post("/conversations")
def create_conversation(req: ConversationCreate):
    conv = store.create(req.title)
    return {"id": conv.id, "title": conv.title}


@app.get("/conversations")
def list_conversations():
    return {
        "conversations": [
            {"id": c.id, "title": c.title} for c in store.list()
        ]
    }


@app.get("/conversations/{cid}")
def get_conversation(cid: str):
    conv = store.get(cid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return {
        "id": conv.id,
        "title": conv.title,
        "messages": [m.__dict__ for m in conv.messages],
    }


@app.delete("/conversations/{cid}")
def delete_conversation(cid: str):
    store.delete(cid)
    return {"status": "deleted"}


class MessageRequest(BaseModel):
    content: str
    stream: bool = True


@app.post("/conversations/{cid}/messages")
async def add_message(cid: str, req: MessageRequest):
    if not manager.is_running():
        raise HTTPException(status_code=503, detail="Inference server not running")

    conv = store.get(cid)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conv.messages.append(Message(role="user", content=req.content))

    server_url = f"http://{manager.settings.host}:{manager.settings.port}/v1/chat/completions"
    payload = {
        "messages": [m.__dict__ for m in conv.messages],
        "stream": req.stream,
    }

    if req.stream:
        async def event_stream():
            assistant_reply = ""
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", server_url, json=payload) as resp:
                    async for line in resp.aiter_lines():
                        if line:
                            yield f"{line}\n\n"
                            if line.startswith("data:"):
                                data_str = line[5:].strip()
                                if data_str == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    token = (
                                        data["choices"][0]["delta"].get("content", "")
                                    )
                                    assistant_reply += token
                                except Exception:
                                    pass
            conv.messages.append(Message(role="assistant", content=assistant_reply))

        return StreamingResponse(event_stream(), media_type="text/event-stream")
    else:
        async with httpx.AsyncClient(timeout=None) as client:
            resp = await client.post(server_url, json=payload)
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
        conv.messages.append(Message(role="assistant", content=content))
        return {"content": content}


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
