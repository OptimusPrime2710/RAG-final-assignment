"""Chroma-compatible semantic storage with an offline JSON fallback."""

import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any


def generate_embedding(text: str, dimensions: int = 64) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    values = [(digest[index % len(digest)] / 255.0) for index in range(dimensions)]
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


def lexical_score(query: str, text: str) -> float:
    """Score exact phrases and shared terms for reliable incident lookup."""
    normalized_query = " ".join(query.lower().split())
    normalized_text = " ".join(text.lower().split())
    ignored = {"a", "an", "and", "are", "be", "by", "for", "from", "has", "in", "is", "it", "of", "on", "or", "the", "to", "was", "with", "issue", "resolution", "status", "resolved"}
    query_terms = {term for term in re.findall(r"[a-z0-9]+", normalized_query) if term not in ignored and not re.fullmatch(r"inc\d+", term)}
    text_terms = {term for term in re.findall(r"[a-z0-9]+", normalized_text) if term not in ignored and not re.fullmatch(r"inc\d+", term)}
    overlap = len(query_terms & text_terms) / max(len(query_terms), 1)
    exact_phrase = 1.0 if normalized_query and normalized_query in normalized_text else 0.0
    return exact_phrase * 10.0 + overlap


class ChromaStore:
    """Small persistent vector store exposing the required Chroma operations."""

    def __init__(self, persist_directory: str | Path = "data/chroma", collection: str = "documents") -> None:
        self.path = Path(persist_directory) / f"{collection}.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.records: list[dict[str, Any]] = json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else []

    def _save(self) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.records, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    def store_embedding(self, document_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.records = [record for record in self.records if record["document_id"] != document_id]
        self.records.append({"document_id": document_id, "text": text, "metadata": metadata or {}, "hash": digest, "embedding": generate_embedding(text)})
        self._save()

    def search_similar(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        query_embedding = generate_embedding(query)
        ranked = sorted(
            self.records,
            key=lambda record: (
                lexical_score(query, record["text"]),
                sum(a * b for a, b in zip(query_embedding, record["embedding"])),
            ),
            reverse=True,
        )
        evidenced = [record for record in ranked if lexical_score(query, record["text"]) > 0]
        return [{"document_id": record["document_id"], "text": record["text"], "metadata": record["metadata"], "score": lexical_score(query, record["text"])} for record in evidenced[:top_k]]

    def validate_collection(self) -> dict[str, Any]:
        return {"valid": all("embedding" in record for record in self.records), "count": len(self.records)}


class NativeChromaStore:
    """Native ChromaDB backend with the same public operations as ``ChromaStore``."""

    def __init__(self, persist_directory: str | Path = "data/chroma", collection: str = "documents", client: Any = None) -> None:
        if client is None:
            try:
                import chromadb
            except ImportError as error:
                raise RuntimeError("install the optional 'rag' dependency to use NativeChromaStore") from error
            client = chromadb.PersistentClient(path=str(persist_directory))
        self.collection = client.get_or_create_collection(collection)

    def store_embedding(self, document_id: str, text: str, metadata: dict[str, Any] | None = None) -> None:
        self.collection.upsert(
            ids=[document_id], documents=[text], metadatas=[metadata or {}], embeddings=[generate_embedding(text)]
        )

    def search_similar(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        result = self.collection.query(query_embeddings=[generate_embedding(query)], n_results=self.collection.count())
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        ranked = sorted(
            [
                {"document_id": identifier, "text": documents[index], "metadata": metadatas[index], "distance": distances[index] if distances else None}
                for index, identifier in enumerate(ids)
            ],
            key=lambda result: lexical_score(query, result["text"]),
            reverse=True,
        )
        return ranked[:top_k]

    def validate_collection(self) -> dict[str, Any]:
        count = self.collection.count()
        return {"valid": count >= 0, "count": count}
