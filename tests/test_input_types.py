import pytest

from rag_framework.domain import PlanInput


def test_plan_input_rejects_wrong_primitive_type() -> None:
    with pytest.raises(ValueError, match="does not match"):
        PlanInput(input_id="top_k", name="top_k", type="integer", default_value="five")


def test_plan_input_accepts_unresolved_required_value() -> None:
    value = PlanInput(input_id="query", name="query", type="string", required=True)
    assert value.effective_value is None
