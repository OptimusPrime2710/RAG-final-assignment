from pathlib import Path

from rag_framework.agents.validator import ValidatorAgent
from rag_framework.config import load_settings
from rag_framework.domain import SuccessCriterion, ValidatorRequest
from rag_framework.registry.model_registry import ModelRegistry


def test_model_validator_uses_configured_small_model(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("LLM_SMALL_MODEL", "provider/small")
    settings = load_settings(tmp_path / ".env")
    calls = []

    def model_call(model, messages):
        calls.append((model.model, messages))
        return {"status": "passed", "criteria": [{"criterion_id": "c1", "passed": True, "evidence": "matched"}], "reason": None, "retry_recommended": False, "_model_execution": {}}

    request = ValidatorRequest(
        plan_id="p", goal_id="g", task_id="t",
        success_criteria=[SuccessCriterion(criterion_id="c1", description="Done")],
        executor_result={"value": 1}, executor_validation={"status": "passed"},
    )
    response = ValidatorAgent(ModelRegistry(settings), model_call).validate(request)
    assert response.status == "passed"
    assert calls[0][0] == "provider/small"
