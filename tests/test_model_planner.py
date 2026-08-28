from pathlib import Path

import pytest

from rag_framework.agents.planner import PlannerAgent
from rag_framework.config import load_settings
from rag_framework.registry.model_registry import ModelRegistry


def test_model_planner_validates_structured_plan(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LLM_MEDIUM_MODEL", "provider/medium")
    settings = load_settings(tmp_path / ".env")
    calls = []

    def model_call(model, messages):
        calls.append((model.model, messages))
        return {
            "source": {"format": ".md"},
            "use_case": {"title": "Modeled case"},
            "inputs": [],
            "goals": [],
            "_model_execution": {"model": model.model},
        }

    source = tmp_path / "case.md"
    source.write_text("Plan this case", encoding="utf-8")
    plan = PlannerAgent(ModelRegistry(settings), model_call).create_plan(source, "modeled")
    assert plan.plan_id == "modeled"
    assert plan.source["model_execution"]["model"] == "provider/medium"
    assert calls[0][0] == "provider/medium"


def test_planner_rejects_unsupported_file(tmp_path: Path) -> None:
    source = tmp_path / "case.json"
    source.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match=".txt"):
        PlannerAgent().create_plan(source, "invalid")
