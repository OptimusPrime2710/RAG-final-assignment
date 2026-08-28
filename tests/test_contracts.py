import pytest
from jsonschema import ValidationError

from rag_framework.domain import ModelRequirement, PlanInput
from rag_framework.schemas import EXECUTOR_REQUEST_SCHEMA, validate_json


def test_user_input_overrides_default() -> None:
    value = PlanInput(
        input_id="top_k", name="top_k", type="integer", default_value=5, user_value=10
    )
    assert value.effective_value == 10
    assert value.source == "user"


def test_required_model_requires_supported_size() -> None:
    with pytest.raises(ValueError):
        ModelRequirement(required=True, size="large")


def test_executor_schema_rejects_missing_identity() -> None:
    with pytest.raises(ValidationError):
        validate_json({"task": {}}, EXECUTOR_REQUEST_SCHEMA)


def test_executor_schema_accepts_tool_only_request() -> None:
    validate_json(
        {
            "request_id": "req_1",
            "plan_id": "plan_1",
            "goal_id": "goal_1",
            "task_id": "task_1",
            "executor_type": "task_executor",
            "task": {"name": "index", "description": "Index files"},
            "model_requirement": {"required": False, "size": None},
        },
        EXECUTOR_REQUEST_SCHEMA,
    )
