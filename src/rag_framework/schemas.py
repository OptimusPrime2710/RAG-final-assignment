"""JSON Schema validation for public contracts."""

from typing import Any

from jsonschema import Draft202012Validator


EXECUTOR_REQUEST_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "required": ["request_id", "plan_id", "goal_id", "task_id", "executor_type", "task", "model_requirement"],
    "properties": {
        "request_id": {"type": "string", "minLength": 1},
        "plan_id": {"type": "string", "minLength": 1},
        "goal_id": {"type": "string", "minLength": 1},
        "task_id": {"type": "string", "minLength": 1},
        "subtask_id": {"type": ["string", "null"], "minLength": 1},
        "executor_type": {"type": "string", "minLength": 1},
        "task": {"type": "object"},
        "inputs": {"type": "object"},
        "tools": {"type": "array", "items": {"type": "string"}},
        "model_requirement": {
            "type": "object",
            "required": ["required", "size"],
            "properties": {"required": {"type": "boolean"}, "size": {"type": ["string", "null"]}},
        },
        "attempt": {"type": "integer", "minimum": 1},
        "max_attempts": {"type": "integer", "minimum": 1},
    },
}

STATUS_SCHEMA = {"type": "string", "enum": ["pending", "ready", "running", "completed", "failed", "blocked", "skipped", "paused"]}
MODEL_REQUIREMENT_SCHEMA = {
    "type": "object", "required": ["required", "size"],
    "properties": {"required": {"type": "boolean"}, "size": {"type": ["string", "null"], "enum": ["small", "medium", None]}},
}
CRITERION_SCHEMA = {"type": "object", "required": ["criterion_id", "description", "achieved"], "properties": {"criterion_id": {"type": "string", "minLength": 1}, "description": {"type": "string"}, "achieved": {"type": "boolean"}}}
SUBTASK_SCHEMA = {"type": "object", "required": ["subtask_id", "task", "status", "dependencies"], "properties": {"subtask_id": {"type": "string", "minLength": 1}, "task": {"type": "string"}, "description": {"type": "string"}, "status": STATUS_SCHEMA, "dependencies": {"type": "array", "items": {"type": "string"}}, "inputs": {"type": "object"}, "tool_required": {"type": "array", "items": {"type": "string"}}, "execution": {"type": "object"}}}
TASK_SCHEMA = {"type": "object", "required": ["task_id", "task", "status", "dependencies", "model_requirement", "retry"], "properties": {"task_id": {"type": "string", "minLength": 1}, "task": {"type": "string"}, "description": {"type": "string"}, "status": STATUS_SCHEMA, "critical": {"type": "boolean"}, "dependencies": {"type": "array", "items": {"type": "string"}}, "inputs": {"type": "object"}, "expected_output": {"type": "object"}, "output_mapping": {"type": "object", "additionalProperties": {"type": "string"}}, "model_requirement": MODEL_REQUIREMENT_SCHEMA, "tool_required": {"type": "array", "items": {"type": "string"}}, "subtasks": {"type": "array", "items": SUBTASK_SCHEMA}, "retry": {"type": "object"}, "execution": {"type": "object"}}}
GOAL_SCHEMA = {"type": "object", "required": ["goal_id", "goal", "status", "success_criteria", "tasks"], "properties": {"goal_id": {"type": "string", "minLength": 1}, "goal": {"type": "string"}, "description": {"type": "string"}, "status": STATUS_SCHEMA, "critical": {"type": "boolean"}, "success_criteria": {"type": "array", "items": CRITERION_SCHEMA}, "tasks": {"type": "array", "items": TASK_SCHEMA}}}
PLAN_SCHEMA = {"$schema": "https://json-schema.org/draft/2020-12/schema", "title": "Plan", "type": "object", "required": ["plan_id", "version", "status", "source", "use_case", "inputs", "goals"], "properties": {"plan_id": {"type": "string", "minLength": 1}, "version": {"type": "integer", "minimum": 1}, "status": STATUS_SCHEMA, "source": {"type": "object"}, "use_case": {"type": "object"}, "inputs": {"type": "array"}, "goals": {"type": "array", "items": GOAL_SCHEMA}}}
EXECUTOR_RESPONSE_SCHEMA = {"type": "object", "required": ["request_id", "status", "result", "output_for_next_executor", "validation", "retry"], "properties": {"request_id": {"type": "string", "minLength": 1}, "status": {"type": "string", "enum": ["success", "failure"]}, "result": {"type": "object"}, "output_for_next_executor": {"type": "object"}, "validation": {"type": "object"}, "error": {"type": ["string", "null"]}, "retry": {"type": "object"}}}
VALIDATOR_REQUEST_SCHEMA = {"type": "object", "required": ["plan_id", "goal_id", "task_id", "success_criteria", "executor_result", "executor_validation"], "properties": {"plan_id": {"type": "string", "minLength": 1}, "goal_id": {"type": "string", "minLength": 1}, "task_id": {"type": "string", "minLength": 1}, "success_criteria": {"type": "array", "items": CRITERION_SCHEMA}, "executor_result": {"type": "object"}, "executor_validation": {"type": "object"}}}
VALIDATOR_RESPONSE_SCHEMA = {"type": "object", "required": ["status", "criteria", "retry_recommended"], "properties": {"status": {"type": "string", "enum": ["passed", "failed"]}, "criteria": {"type": "array"}, "reason": {"type": ["string", "null"]}, "retry_recommended": {"type": "boolean"}}}
TRANSFORMED_INPUT_SCHEMA = {"type": "object", "required": ["inputs"], "properties": {"inputs": {"type": "object"}}}


def validate_json(instance: dict[str, Any], schema: dict[str, Any]) -> None:
    """Raise jsonschema.ValidationError when a contract is invalid."""
    Draft202012Validator(schema).validate(instance)
