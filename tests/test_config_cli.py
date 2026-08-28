import json
from pathlib import Path

import pytest

from rag_framework.cli import main


def test_config_check_reports_paths_without_secrets(tmp_path: Path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("PLANS_DIRECTORY", str(tmp_path / "plans"))
    monkeypatch.setenv("CHROMA_PERSIST_DIRECTORY", str(tmp_path / "chroma"))
    assert main(["config-check"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is True
    assert result["plans_directory"] == str(tmp_path / "plans")
    assert "api_key" not in result
    assert "token" not in result


def test_config_check_requires_requested_integration(monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        main(["config-check", "--openrouter"])
