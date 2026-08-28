from pathlib import Path

import pytest

from rag_framework.cli import _apply_user_inputs
from rag_framework.domain import Plan, PlanInput


def test_cli_input_override_converts_declared_type() -> None:
    plan = Plan(plan_id="inputs", inputs=[PlanInput(input_id="top_k", name="top_k", type="integer", default_value=5)])
    _apply_user_inputs(plan, ["top_k=12"])
    assert plan.inputs[0].effective_value == 12
    assert plan.inputs[0].source == "user"


def test_cli_rejects_unknown_or_malformed_input() -> None:
    plan = Plan(plan_id="inputs", inputs=[PlanInput(input_id="top_k", name="top_k", type="integer", default_value=5)])
    with pytest.raises(ValueError, match="unknown"):
        _apply_user_inputs(plan, ["query=policy"])
    with pytest.raises(ValueError, match="name=value"):
        _apply_user_inputs(plan, ["top_k"])
