"""Local Whisper model management and transcription.

This module keeps heavyweight optional dependencies behind runtime calls so the
prototype can be installed and tested before Android-specific setup is complete.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .config import AppConfig


class WhisperBackend(Protocol):
    def download_rooted_model(self, model_name: str, download_root: Path) -> object:
        ...

    def transcribe(self, model_name: str, download_root: Path, audio_path: Path) -> str:
        ...


@dataclass(frozen=True)
class ModelStatus:
    model_name: str
    ready: bool
    marker: str
    models_dir: str
    message: str


class OpenAIWhisperBackend:
    """Backend adapter for the optional `openai-whisper` package."""

    def _module(self):
        try:
            return importlib.import_module("whisper")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "The openai-whisper package is not installed. Run `pip install -r requirements.txt` "
                "inside your Termux virtual environment, then download the model."
            ) from exc

    def download_rooted_model(self, model_name: str, download_root: Path) -> object:
        whisper = self._module()
        return whisper.load_model(model_name, download_root=str(download_root))

    def transcribe(self, model_name: str, download_root: Path, audio_path: Path) -> str:
        model = self.download_rooted_model(model_name, download_root)
        result = model.transcribe(str(audio_path))
        return str(result.get("text", "")).strip()


class WhisperService:
    def __init__(self, config: AppConfig, backend: WhisperBackend | None = None) -> None:
        self.config = config
        self.backend = backend or OpenAIWhisperBackend()

    def status(self) -> ModelStatus:
        ready = self.config.model_marker.exists()
        if ready:
            message = f"Whisper model '{self.config.model_name}' is ready."
        else:
            message = "Speech model is not downloaded yet. Tap Download before transcribing."
        return ModelStatus(
            model_name=self.config.model_name,
            ready=ready,
            marker=str(self.config.model_marker),
            models_dir=str(self.config.models_dir),
            message=message,
        )

    def download(self) -> ModelStatus:
        self.config.ensure_dirs()
        self.backend.download_rooted_model(self.config.model_name, self.config.models_dir)
        self.config.model_marker.write_text(
            f"model={self.config.model_name}\nstatus=ready\n",
            encoding="utf-8",
        )
        return self.status()

    def transcribe(self, audio_path: Path) -> str:
        if not self.config.model_marker.exists():
            raise RuntimeError("Whisper model is not ready. Download it first from the setup panel.")
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file does not exist: {audio_path}")
        return self.backend.transcribe(self.config.model_name, self.config.models_dir, audio_path)
