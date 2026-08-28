import json
from pathlib import Path

from rag_framework.cli import main


def test_cli_goal_retriggers_existing_goal(tmp_path: Path, capsys) -> None:
    plans = tmp_path / "plans"
    source = tmp_path / "case.md"
    source.write_text("# Search\nLoad documents and retrieve similar results.", encoding="utf-8")
    main(["plan", str(source), "--plan-id", "goal", "--plans-dir", str(plans)])
    capsys.readouterr()
    main(["goal", "goal", "Find relevant documents", "--plans-dir", str(plans)])
    assert json.loads(capsys.readouterr().out)["status"] == "completed"
