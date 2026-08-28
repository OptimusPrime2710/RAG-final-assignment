from pathlib import Path

import pytest

from rag_framework.config import load_settings
from rag_framework.domain import Plan
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.model_registry import ModelRegistry
from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


def test_model_registry_resolves_configured_size(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LLM_SMALL_MODEL", "small-model")
    settings = load_settings(tmp_path / ".env")
    assert ModelRegistry(settings).resolve("small").model == "small-model"


def test_tool_registry_discovers_and_dispatches() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDescriptor("echo", "echo", "Echo input", "python", capabilities=["test"]),
        lambda inputs: {"value": inputs["value"]},
    )
    assert registry.discover("test")[0].toolid == "echo"
    assert registry.execute("echo", {"value": 3}) == {"value": 3}


def test_plan_store_round_trip_is_json(tmp_path: Path) -> None:
    plan = Plan(plan_id="001")
    store = PlanStore(tmp_path)
    saved = store.save(plan)
    assert saved.exists()
    assert store.load("001").plan_id == "001"


def test_unknown_tool_is_rejected() -> None:
    with pytest.raises(KeyError):
        ToolRegistry().execute("missing", {})
