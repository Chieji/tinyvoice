from pathlib import Path
from unittest.mock import patch

from tinyvoice.commands import preview_command, read_audit, run_allowed_command


def test_preview_allows_known_phrase():
    preview = preview_command("List the files!")

    assert preview.ok is True
    assert preview.command == "ls -la"
    assert preview.auto_run_safe is True


def test_preview_rejects_unknown_or_dangerous_phrase():
    preview = preview_command("delete everything with rm rf")

    assert preview.ok is False
    assert "Command not allowed" in preview.error
    assert preview.command is None


def test_run_allowed_command_uses_argv_without_shell(tmp_path):
    audit_log = tmp_path / "audit.log"

    with patch("tinyvoice.commands.subprocess.run") as run:
        run.return_value.returncode = 0
        run.return_value.stdout = "/tmp\n"
        run.return_value.stderr = ""
        result = run_allowed_command("show current folder", audit_log=audit_log, timeout_seconds=3, cwd=tmp_path)

    assert result.ok is True
    assert result.command == "pwd"
    run.assert_called_once()
    _, kwargs = run.call_args
    assert run.call_args.args[0] == ["pwd"]
    assert "shell" not in kwargs
    assert kwargs["timeout"] == 3
    assert kwargs["cwd"] == tmp_path.resolve()
    audit = read_audit(audit_log)
    assert [entry["event"] for entry in audit] == ["proposed", "executed"]


def test_run_rejected_command_is_audited(tmp_path):
    result = run_allowed_command("curl bad thing", audit_log=tmp_path / "audit.log")

    assert result.ok is False
    audit = read_audit(tmp_path / "audit.log")
    assert audit[-1]["event"] == "rejected"
