import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class ServerSettings:
    model: str
    n_predict: int = 4096
    threads: int = 2
    ctx_size: int = 2048
    temperature: float = 0.8
    host: str = "127.0.0.1"
    port: int = 8080


class ServerManager:
    """Manage lifecycle of run_inference_server.py subprocess."""

    def __init__(self) -> None:
        self.process: Optional[subprocess.Popen] = None
        self.settings: Optional[ServerSettings] = None
        # Path to run_inference_server.py at repository root
        self._script = Path(__file__).resolve().parents[2] / "run_inference_server.py"

    def start(self, settings: ServerSettings) -> None:
        """Start the inference server with the given settings."""
        self.stop()
        cmd = [
            sys.executable,
            str(self._script),
            "--model",
            settings.model,
            "--n-predict",
            str(settings.n_predict),
            "--threads",
            str(settings.threads),
            "--ctx-size",
            str(settings.ctx_size),
            "--temperature",
            str(settings.temperature),
            "--host",
            settings.host,
            "--port",
            str(settings.port),
        ]
        self.process = subprocess.Popen(cmd)
        self.settings = settings

    def stop(self) -> None:
        """Terminate the running server if any."""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None

    def restart(self, settings: ServerSettings) -> None:
        """Restart server with new settings."""
        self.start(settings)

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def current_settings(self) -> Optional[dict]:
        return asdict(self.settings) if self.settings else None


manager = ServerManager()
