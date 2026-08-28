from pathlib import Path

import pytest

from rag_framework.config import load_settings


def test_openrouter_validation_requires_complete_settings(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.setenv("LLM_SMALL_MODEL", "small")
    monkeypatch.setenv("LLM_MEDIUM_MODEL", "medium")
    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        load_settings(tmp_path / ".env").validate_for(openrouter=True)


def test_jira_validation_requires_all_credentials(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_MCP_URL", "https://jira.example/mcp")
    monkeypatch.delenv("JIRA_EMAIL", raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    with pytest.raises(ValueError, match="JIRA_MCP_URL"):
        load_settings(tmp_path / ".env").validate_for(jira=True)


def test_retry_limit_is_bounded(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("MAX_RETRY_ATTEMPTS", "4")
    with pytest.raises(ValueError, match="between 1 and 3"):
        load_settings(tmp_path / ".env").validate_for()
