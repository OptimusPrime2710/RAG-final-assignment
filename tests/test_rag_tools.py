from pathlib import Path

from rag_framework.tools.chroma import ChromaStore, generate_embedding
from rag_framework.tools.document import index_directory


def test_indexing_is_incremental_and_retrievable(tmp_path: Path) -> None:
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "policy.md").write_text("Cancellation policy allows cancellation within thirty days.", encoding="utf-8")
    store = ChromaStore(tmp_path / "chroma")
    assert index_directory(documents, store) == {"processed": 1, "skipped": 0}
    assert index_directory(documents, store) == {"processed": 0, "skipped": 1}
    assert len(store.search_similar("cancellation policy", top_k=5)) == 1
    assert store.validate_collection()["valid"]


def test_embeddings_are_deterministic() -> None:
    assert generate_embedding("same") == generate_embedding("same")
