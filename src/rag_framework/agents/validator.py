"""Independent executor-result validation."""

import json
from typing import Any, Callable

from rag_framework.domain import ValidatorRequest, ValidatorResponse
from rag_framework.registry.model_registry import ModelRegistry
from rag_framework.schemas import VALIDATOR_RESPONSE_SCHEMA, validate_json


class ValidatorAgent:
    def __init__(self, models: ModelRegistry | None = None, model_call: Callable[..., dict[str, Any]] | None = None, model_size: str = "small") -> None:
        self.models = models
        self.model_call = model_call
        self.model_size = model_size

    def validate(self, request: ValidatorRequest) -> ValidatorResponse:
        if self.models is not None and self.model_call is not None:
            model = self.models.resolve(self.model_size)
            result = self.model_call(model, [{
                "role": "system",
                "content": "Return only JSON with status, criteria, reason, and retry_recommended.",
            }, {"role": "user", "content": json.dumps(request.model_dump())}])
            result.pop("_model_execution", None)
            response = ValidatorResponse.model_validate(result)
            validate_json(response.model_dump(), VALIDATOR_RESPONSE_SCHEMA)
            return response
        passed = request.executor_result is not None and request.executor_validation.get("status") == "passed"
        criteria = [
            {"criterion_id": criterion.criterion_id, "passed": passed, "evidence": "executor self-validation passed" if passed else "executor validation failed"}
            for criterion in request.success_criteria
        ]
        response = ValidatorResponse(
            status="passed" if passed else "failed",
            criteria=criteria,
            reason=None if passed else "executor validation did not pass",
            retry_recommended=not passed,
        )
        validate_json(response.model_dump(), VALIDATOR_RESPONSE_SCHEMA)
        return response
