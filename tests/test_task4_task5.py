from pathlib import Path
from typing import Final

import pytest

from src import task4_chunking_indexing as task4
from src import task5_semantic_search as task5


class FakeEmbedder:
    def encode(self, texts: list[str], **kwargs: bool) -> list[list[float]]:
        return [[float(len(text)), 1.0] for text in texts]


class FakeCollection:
    def __init__(self, existing_ids: list[str] | None = None) -> None:
        self.upserted: dict[str, str] = {}
        self.existing_ids = set(existing_ids or [])
        self.deleted_ids: list[str] = []

    def upsert(self, *, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict[str, str | int]]) -> None:
        self.upserted = {chunk_id: document for chunk_id, document in zip(ids, documents, strict=True)}
        self.existing_ids.update(ids)

    def get(self, *, include: list[str]) -> dict[str, list[str]]:
        return {"ids": sorted(self.existing_ids)}

    def delete(self, *, ids: list[str]) -> None:
        self.deleted_ids.extend(ids)
        self.existing_ids.difference_update(ids)

    def query(self, *, query_embeddings: list[list[float]], n_results: int, include: list[str]) -> dict[str, list[list[str | float | dict[str, str | int]]]]:
        return {
            "documents": [["short", "long"][:n_results]],
            "metadatas": [[{"source": "a.md"}, {"source": "b.md"}][:n_results]],
            "distances": [[0.4, 0.1][:n_results]],
        }


ROOT: Final[Path] = Path(__file__).parent.parent


def test_load_and_chunk_preserve_relative_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "standardized" / "legal" / "policy.md"
    source.parent.mkdir(parents=True)
    source.write_text("x" * 1_000, encoding="utf-8")
    monkeypatch.setattr(task4, "STANDARDIZED_DIR", tmp_path / "standardized")

    documents = task4.load_documents()
    chunks = task4.chunk_documents(documents)

    assert documents[0]["metadata"] == {"source": "legal/policy.md", "type": "legal", "customer_role": "unknown"}
    assert len(chunks) > 1
    assert all(len(chunk["content"]) <= task4.CHUNK_SIZE for chunk in chunks)
    assert chunks[0]["metadata"]["chunk_index"] == 0


def test_index_uses_deterministic_ids_and_injectable_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    collection = FakeCollection()
    monkeypatch.setattr(task4, "get_collection", lambda: collection)
    chunks = [{"content": "hello", "metadata": {"source": "legal/policy.md", "chunk_index": 0}, "embedding": [1.0, 2.0]}]

    task4.index_to_vectorstore(chunks)

    assert list(collection.upserted) == ["legal/policy.md::chunk-0"]


def test_index_removes_stale_ids_without_recreating_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    collection = FakeCollection(["old.md::chunk-0", "legal/policy.md::chunk-0"])
    monkeypatch.setattr(task4, "get_collection", lambda: collection)
    chunks = [{"content": "hello", "metadata": {"source": "legal/policy.md", "chunk_index": 0}, "embedding": [1.0, 2.0]}]

    task4.index_to_vectorstore(chunks)

    assert collection.deleted_ids == ["old.md::chunk-0"]


def test_roles_are_derived_from_taxonomy_and_preserved() -> None:
    assert task4._customer_role("seller/policy.md", {}) == "seller"
    assert task4._customer_role("buyer/guide.md", {}) == "buyer"
    assert task4._customer_role("both/guide.md", {}) == "both"
    assert task4._customer_role("other/guide.md", {"customer_role": "seller"}) == "seller"
    assert task4._customer_role("other/guide.md", {}) == "unknown"


def test_recursive_chunking_uses_configured_overlap() -> None:
    document = {"content": "alpha\n\nbeta " * 300, "metadata": {"source": "x.md"}, "embedding": []}

    chunks = task4.chunk_documents([document])

    assert all(len(chunk["content"]) <= task4.CHUNK_SIZE for chunk in chunks)
    assert chunks[0]["content"][-task4.CHUNK_OVERLAP:] == chunks[1]["content"][:task4.CHUNK_OVERLAP]


def test_semantic_search_returns_descending_bounded_results_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    collection = FakeCollection()
    monkeypatch.setattr(task4, "get_collection", lambda: collection)
    monkeypatch.setattr(task4, "embed_texts", lambda texts: [[1.0, 0.0] for _ in texts])

    results = task5.semantic_search("payment", top_k=2)

    assert [result["content"] for result in results] == ["long", "short"]
    assert results[0]["score"] == 0.9
    assert set(results[0]) == {"content", "score", "metadata"}


def test_semantic_search_handles_empty_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(task4, "get_collection", lambda: pytest.fail("empty query must not query collection"))

    assert task5.semantic_search("", top_k=3) == []
    assert task5.semantic_search("query", top_k=0) == []


def test_semantic_search_returns_empty_when_chromadb_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing_chromadb() -> task4.Collection:
        raise ModuleNotFoundError("No module named 'chromadb'")

    monkeypatch.setattr(task4, "get_collection", missing_chromadb)

    assert task5.semantic_search("payment", top_k=3) == []


def test_hyde_provider_text_is_embedded(monkeypatch: pytest.MonkeyPatch) -> None:
    collection = FakeCollection()
    embedded: list[str] = []
    monkeypatch.setattr(task4, "get_collection", lambda: collection)
    monkeypatch.setattr(task4, "embed_texts", lambda texts: (embedded.extend(texts) or [[1.0, 0.0] for _ in texts]))

    task5.semantic_search("payment", top_k=2, hyde_provider=lambda _: "hypothetical payment policy")

    assert embedded == ["hypothetical payment policy"]


def test_semantic_search_returns_empty_when_embedding_dependency_is_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(task4, "get_collection", lambda: FakeCollection())
    monkeypatch.setattr(task4, "embed_texts", lambda texts: (_ for _ in ()).throw(ModuleNotFoundError("sentence_transformers")))

    assert task5.semantic_search("payment", top_k=2) == []
