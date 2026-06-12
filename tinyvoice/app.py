"""Flask application factory for the TinyVoice side-panel prototype."""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from uuid import uuid4

from flask import Flask, jsonify, request, send_from_directory

from .commands import allowed_phrases, preview_command, read_audit, run_allowed_command
from .config import AppConfig
from .whisper_local import WhisperService


def _json_error(message: str, status: int = 400):
    return jsonify({"ok": False, "error": message}), status


def create_app(config: AppConfig | None = None, whisper_service: WhisperService | None = None) -> Flask:
    app_config = config or AppConfig.from_env()
    app_config.ensure_dirs()
    speech = whisper_service or WhisperService(app_config)

    app = Flask(__name__, static_folder="static")
    app.config["TINYVOICE_CONFIG"] = app_config

    @app.get("/")
    def index():
        return send_from_directory(app.static_folder, "index.html")

    @app.get("/api/status")
    def status():
        return jsonify(
            {
                "ok": True,
                "model": asdict(speech.status()),
                "allowed_phrases": allowed_phrases(),
                "audit": read_audit(app_config.audit_log),
            }
        )

    @app.post("/api/model/download")
    def download_model():
        try:
            return jsonify({"ok": True, "model": asdict(speech.download())})
        except Exception as exc:  # runtime boundary: convert setup failures into UI messages
            return _json_error(str(exc), 500)

    @app.post("/api/intent")
    def intent():
        data = request.get_json(silent=True) or {}
        transcript = str(data.get("transcript", ""))
        preview = preview_command(transcript)
        return jsonify({"ok": preview.ok, "preview": asdict(preview)}), 200 if preview.ok else 400

    @app.post("/api/run")
    def run():
        data = request.get_json(silent=True) or {}
        transcript = str(data.get("transcript", ""))
        confirm = bool(data.get("confirm", False))
        preview = preview_command(transcript)
        if not preview.ok:
            return jsonify({"ok": False, "preview": asdict(preview), "error": preview.error}), 400
        if not confirm:
            return jsonify({"ok": False, "preview": asdict(preview), "error": "Confirmation required."}), 409
        result = run_allowed_command(
            transcript,
            audit_log=app_config.audit_log,
            timeout_seconds=app_config.command_timeout_seconds,
            cwd=Path.cwd(),
        )
        return jsonify({"ok": result.ok, "result": asdict(result), "audit": read_audit(app_config.audit_log)})

    @app.post("/api/transcribe")
    def transcribe():
        if "audio" not in request.files:
            return _json_error("Upload an audio file field named 'audio'.")
        uploaded = request.files["audio"]
        suffix = Path(uploaded.filename or "audio.webm").suffix or ".webm"
        audio_path = app_config.uploads_dir / f"{uuid4().hex}{suffix}"
        uploaded.save(audio_path)
        try:
            transcript = speech.transcribe(audio_path)
            preview = preview_command(transcript)
            return jsonify(
                {
                    "ok": True,
                    "transcript": transcript,
                    "preview": asdict(preview),
                    "audio_file": str(audio_path),
                }
            )
        except Exception as exc:
            return _json_error(str(exc), 500)

    @app.get("/api/audit")
    def audit():
        return jsonify({"ok": True, "audit": read_audit(app_config.audit_log)})

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=8765)
