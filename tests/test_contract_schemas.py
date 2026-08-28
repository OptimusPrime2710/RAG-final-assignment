import pytest
from jsonschema import ValidationError

from rag_framework.domain import Plan
from rag_framework.schemas import (
    EXECUTOR_RESPONSE_SCHEMA,
    PLAN_SCHEMA,
    VALIDATOR_RESPONSE_SCHEMA,
    validate_json,
)


def test_plan_model_dump_matches_public_schema() -> None:
    validate_json(Plan(plan_id="schema").model_dump(), PLAN_SCHEMA)


def test_response_schemas_reject_invalid_status() -> None:
    with pytest.raises(ValidationError):
        validate_json({"request_id": "r", "status": "unknown", "result": {}, "output_for_next_executor": {}, "validation": {}, "retry": {}}, EXECUTOR_RESPONSE_SCHEMA)
    with pytest.raises(ValidationError):
        validate_json({"status": "unknown", "criteria": [], "retry_recommended": False}, VALIDATOR_RESPONSE_SCHEMA)
