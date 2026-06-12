"""Allowlisted command preview and execution."""

from __future__ import annotations

import json
import os
import shlex
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


@dataclass(frozen=True)
class CommandIntent:
    phrase: str
    description: str
    argv: tuple[str, ...]
    auto_run_safe: bool = False

    @property
    def display_command(self) -> str:
        return shlex.join(self.argv)


@dataclass(frozen=True)
class CommandPreview:
    ok: bool
    transcript: str
    normalized: str
    command: str | None = None
    description: str | None = None
    auto_run_safe: bool = False
    error: str | None = None


@dataclass(frozen=True)
class CommandResult:
    ok: bool
    transcript: str
    command: str | None = None
    stdout: str = ""
    stderr: str = ""
    returncode: int | None = None
    error: str | None = None


_ALLOWED_INTENTS: tuple[CommandIntent, ...] = (
    CommandIntent("list files", "List files in the current working folder.", ("ls", "-la"), True),
    CommandIntent("show disk usage", "Show mounted filesystem disk usage.", ("df", "-h"), True),
    CommandIntent("show current folder", "Print the current working folder.", ("pwd",), True),
    CommandIntent("show date", "Print the current date and time.", ("date",), True),
    CommandIntent("show who am i", "Print the current Termux/Linux user.", ("whoami",), True),
)

_ALIAS_MAP: dict[str, str] = {
    "list file": "list files",
    "list the files": "list files",
    "show files": "list files",
    "what files are here": "list files",
    "disk usage": "show disk usage",
    "show storage": "show disk usage",
    "storage usage": "show disk usage",
    "current folder": "show current folder",
    "where am i": "show current folder",
    "print working directory": "show current folder",
    "pwd": "show current folder",
    "date": "show date",
    "what time is it": "show date",
    "who am i": "show who am i",
}


def normalize_transcript(transcript: str) -> str:
    """Normalize speech text for exact allowlist matching."""

    lowered = transcript.strip().lower()
    cleaned = "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in lowered)
    return " ".join(cleaned.split())


def allowed_phrases() -> list[str]:
    return [intent.phrase for intent in _ALLOWED_INTENTS]


def _find_intent(transcript: str) -> tuple[str, CommandIntent | None]:
    normalized = normalize_transcript(transcript)
    canonical = _ALIAS_MAP.get(normalized, normalized)
    for intent in _ALLOWED_INTENTS:
        if canonical == intent.phrase:
            return normalized, intent
    return normalized, None


def preview_command(transcript: str) -> CommandPreview:
    normalized, intent = _find_intent(transcript)
    if not intent:
        return CommandPreview(
            ok=False,
            transcript=transcript,
            normalized=normalized,
            error="Command not allowed. Try: " + ", ".join(allowed_phrases()) + ".",
        )
    return CommandPreview(
        ok=True,
        transcript=transcript,
        normalized=normalized,
        command=intent.display_command,
        description=intent.description,
        auto_run_safe=intent.auto_run_safe,
    )


def _write_audit(log_path: Path, event: str, payload: dict[str, object]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "time": datetime.now(timezone.utc).isoformat(),
        "event": event,
        **payload,
    }
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")


def read_audit(log_path: Path, limit: int = 25) -> list[dict[str, object]]:
    if not log_path.exists():
        return []
    lines = log_path.read_text(encoding="utf-8").splitlines()[-limit:]
    entries: list[dict[str, object]] = []
    for line in lines:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def run_allowed_command(
    transcript: str,
    *,
    audit_log: Path,
    timeout_seconds: int = 10,
    cwd: Path | None = None,
) -> CommandResult:
    normalized, intent = _find_intent(transcript)
    if not intent:
        result = CommandResult(ok=False, transcript=transcript, error=preview_command(transcript).error)
        _write_audit(audit_log, "rejected", asdict(result))
        return result

    safe_cwd = Path(cwd or os.getcwd()).resolve()
    _write_audit(
        audit_log,
        "proposed",
        {"transcript": transcript, "normalized": normalized, "command": intent.display_command},
    )
    try:
        completed = subprocess.run(
            list(intent.argv),
            cwd=safe_cwd,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
        result = CommandResult(
            ok=completed.returncode == 0,
            transcript=transcript,
            command=intent.display_command,
            stdout=completed.stdout,
            stderr=completed.stderr,
            returncode=completed.returncode,
        )
    except subprocess.TimeoutExpired as exc:
        result = CommandResult(
            ok=False,
            transcript=transcript,
            command=intent.display_command,
            stdout=exc.stdout or "",
            stderr=exc.stderr or "",
            error=f"Command timed out after {timeout_seconds} seconds.",
        )

    _write_audit(audit_log, "executed", asdict(result))
    return result
