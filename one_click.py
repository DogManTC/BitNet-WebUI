#!/usr/bin/env python3
"""One-click installer and launcher for the BitNet WebUI."""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
MODELS_DIR = REPO_ROOT / "models"


def ensure_model() -> Path:
    """Return the first GGUF model under models/ or exit with instructions."""
    models = sorted(MODELS_DIR.glob("*.gguf"))
    if not models:
        print("No GGUF model found in 'models/'.")
        print("Download a model and place it in the 'models' directory before running this script.")
        sys.exit(1)
    if len(models) > 1:
        print(f"Multiple models found. Using {models[0].name} by default.")
    else:
        print(f"Using model {models[0].name}.")
    return models[0]


def run(cmd: list[str]):
    """Run a command and stream output."""
    print("$", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def main():
    model = ensure_model()
    run([sys.executable, "setup_env.py", "-m", str(model)])
    run([sys.executable, "-m", "pip", "install", "-r", "webui/requirements.txt"])
    run([sys.executable, "-m", "uvicorn", "webui.backend.api:app", "--host", "0.0.0.0", "--port", "8000"])


if __name__ == "__main__":
    main()
