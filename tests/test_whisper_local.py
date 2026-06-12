from pathlib import Path

import pytest

from tinyvoice.config import AppConfig
from tinyvoice.whisper_local import WhisperService


class FakeBackend:
    def __init__(self):
        self.downloads = []
        self.transcriptions = []

    def download_rooted_model(self, model_name, download_root):
        self.downloads.append((model_name, download_root))
        return object()

    def transcribe(self, model_name, download_root, audio_path):
        self.transcriptions.append((model_name, download_root, audio_path))
        return "list files"


def test_status_and_download_marker(tmp_path):
    config = AppConfig(data_dir=tmp_path, model_name="tiny")
    backend = FakeBackend()
    service = WhisperService(config, backend)

    assert service.status().ready is False
    status = service.download()

    assert status.ready is True
    assert config.model_marker.exists()
    assert backend.downloads == [("tiny", config.models_dir)]


def test_transcribe_requires_ready_model(tmp_path):
    config = AppConfig(data_dir=tmp_path)
    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"fake")

    with pytest.raises(RuntimeError, match="not ready"):
        WhisperService(config, FakeBackend()).transcribe(audio)


def test_transcribe_after_download(tmp_path):
    config = AppConfig(data_dir=tmp_path)
    backend = FakeBackend()
    service = WhisperService(config, backend)
    audio = tmp_path / "sample.wav"
    audio.write_bytes(b"fake")

    service.download()
    transcript = service.transcribe(audio)

    assert transcript == "list files"
    assert backend.transcriptions == [("tiny", config.models_dir, audio)]
