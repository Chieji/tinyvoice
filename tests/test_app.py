from io import BytesIO

import pytest

pytest.importorskip("flask")

from tinyvoice.app import create_app
from tinyvoice.config import AppConfig
from tinyvoice.whisper_local import WhisperService


class FakeBackend:
    def download_rooted_model(self, model_name, download_root):
        return object()

    def transcribe(self, model_name, download_root, audio_path):
        assert audio_path.exists()
        return "show current folder"


def make_client(tmp_path):
    config = AppConfig(data_dir=tmp_path)
    service = WhisperService(config, FakeBackend())
    app = create_app(config, service)
    app.config.update(TESTING=True)
    return app.test_client(), config


def test_index_and_status(tmp_path):
    client, _ = make_client(tmp_path)

    index = client.get("/")
    status = client.get("/api/status")

    assert index.status_code == 200
    assert b"TinyVoice" in index.data
    assert status.status_code == 200
    assert status.get_json()["model"]["ready"] is False


def test_intent_preview_endpoint(tmp_path):
    client, _ = make_client(tmp_path)

    ok = client.post("/api/intent", json={"transcript": "pwd"})
    bad = client.post("/api/intent", json={"transcript": "rm everything"})

    assert ok.status_code == 200
    assert ok.get_json()["preview"]["command"] == "pwd"
    assert bad.status_code == 400


def test_run_requires_confirmation(tmp_path):
    client, _ = make_client(tmp_path)

    response = client.post("/api/run", json={"transcript": "show current folder"})

    assert response.status_code == 409
    assert "Confirmation required" in response.get_json()["error"]


def test_run_confirmed_command(tmp_path):
    client, _ = make_client(tmp_path)

    response = client.post("/api/run", json={"transcript": "show current folder", "confirm": True})

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ok"] is True
    assert payload["result"]["command"] == "pwd"
    assert payload["audit"]


def test_transcribe_requires_model_then_accepts_upload(tmp_path):
    client, config = make_client(tmp_path)

    missing = client.post(
        "/api/transcribe",
        data={"audio": (BytesIO(b"fake audio"), "sample.wav")},
        content_type="multipart/form-data",
    )
    assert missing.status_code == 500
    assert "Download" in missing.get_json()["error"]

    client.post("/api/model/download")
    response = client.post(
        "/api/transcribe",
        data={"audio": (BytesIO(b"fake audio"), "sample.wav")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload["transcript"] == "show current folder"
    assert payload["preview"]["command"] == "pwd"
