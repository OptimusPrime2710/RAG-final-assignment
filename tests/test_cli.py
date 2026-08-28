import json
from pathlib import Path

from rag_framework.cli import main


def test_cli_plan_persists_json(tmp_path: Path, capsys) -> None:
    source = tmp_path / "case.md"
    source.write_text("# Search\nRetrieve similar documents.", encoding="utf-8")
    assert main(["plan", str(source), "--plan-id", "cli", "--plans-dir", str(tmp_path / "plans")]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["plan_id"] == "cli"
    assert Path(output["path"]).exists()


def test_cli_search_uses_top_k(tmp_path: Path, capsys) -> None:
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "one.md").write_text("Cancellation policy", encoding="utf-8")
    assert main(["index", str(documents), "--chroma-dir", str(tmp_path / "chroma")]) == 0
    capsys.readouterr()
    assert main(["search", "cancellation", "--top-k", "1", "--chroma-dir", str(tmp_path / "chroma")]) == 0
    assert len(json.loads(capsys.readouterr().out)) == 1
