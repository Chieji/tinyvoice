"""Configuration helpers for TinyVoice."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Runtime paths and defaults.

    The defaults are intentionally inside the user's home directory so the app
    can run from a cloned repo in Termux without needing write access to the
    package directory.
    """

    data_dir: Path
    model_name: str = "tiny"
    command_timeout_seconds: int = 10

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"

    @property
    def uploads_dir(self) -> Path:
        return self.data_dir / "uploads"

    @property
    def audit_log(self) -> Path:
        return self.data_dir / "audit.log"

    @property
    def model_marker(self) -> Path:
        return self.models_dir / f"whisper-{self.model_name}.ready"

    @classmethod
    def from_env(cls) -> "AppConfig":
        data_dir = Path(os.environ.get("TINYVOICE_DATA_DIR", "~/.tinyvoice")).expanduser()
        model_name = os.environ.get("TINYVOICE_WHISPER_MODEL", "tiny")
        timeout = int(os.environ.get("TINYVOICE_COMMAND_TIMEOUT", "10"))
        return cls(data_dir=data_dir, model_name=model_name, command_timeout_seconds=timeout)

    def ensure_dirs(self) -> None:
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
