# BitNet WebUI Setup

This guide explains how to run the experimental WebUI for BitNet.

## Quick start
Place a GGUF model inside the `models/` directory and run:

```bash
python one_click.py
```

The script builds the BitNet binaries, installs WebUI dependencies, and launches the backend at [http://localhost:8000/](http://localhost:8000/).
You can check server status at [http://localhost:8000/settings](http://localhost:8000/settings).

## Manual setup
### Prerequisites
* Python 3.9+
* Built BitNet binaries via `python setup_env.py -m <model>`

### Install WebUI dependencies
```bash
pip install -r webui/requirements.txt
```

### Launch the backend API
The backend manages the lifetime of `run_inference_server.py` and serves the WebUI.
```bash
uvicorn webui.backend.api:app --reload
```

After the server starts, open your browser to [http://localhost:8000/](http://localhost:8000/) to use the WebUI.

## Features
* **Model switching** – choose any GGUF model detected under `models/`.
* **Parameter configuration** – adjust temperature and maximum tokens before chatting.
* **Conversation management** – create multiple chats, switch between them, and delete when done.

## Shutdown
Stopping the API server will terminate the BitNet inference server.
