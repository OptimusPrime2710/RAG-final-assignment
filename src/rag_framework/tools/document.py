"""Document discovery and incremental indexing helpers."""

import hashlib
from pathlib import Path

from rag_framework.tools.chroma import ChromaStore


def load_document(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def chunk_text(text: str, chunk_size: int = 1000) -> list[str]:
    return [text[index:index + chunk_size] for index in range(0, len(text), chunk_size)] or [""]


def index_directory(directory: str | Path, store: ChromaStore) -> dict[str, int]:
    processed = 0
    skipped = 0
    records = getattr(store, "records", [])
    known = {record["metadata"].get("path"): record["hash"] for record in records}
    for path in sorted(Path(directory).rglob("*")):
        if path.suffix.lower() not in {".txt", ".md", ".markdown"}:
            continue
        text = load_document(path)
        document_id = str(path.resolve())
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if known.get(document_id) == digest:
            skipped += 1
            continue
        for index, chunk in enumerate(chunk_text(text)):
            store.store_embedding(f"{document_id}#{index}", chunk, {"path": document_id, "chunk": index})
        processed += 1
    return {"processed": processed, "skipped": skipped}
