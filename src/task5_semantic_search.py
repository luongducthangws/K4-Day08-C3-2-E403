"""Task 5: cosine semantic search over Task 4's shared collection."""
from __future__ import annotations

from collections.abc import Callable
from typing import Final, TypedDict

from . import task4_chunking_indexing as task4


class SearchResult(TypedDict):
    content: str
    score: float
    metadata: task4.Metadata

HydeProvider = Callable[[str], str]
DEFAULT_TOP_K: Final = 10


def semantic_search(query: str, top_k: int = DEFAULT_TOP_K, hyde_provider: HydeProvider | None = None) -> list[SearchResult]:
    """Return descending cosine-similarity results, optionally using HyDE text."""
    if not query.strip() or top_k <= 0:
        return []
    search_query = query
    if hyde_provider is not None:
        hypothetical = hyde_provider(query).strip()
        if hypothetical:
            search_query = hypothetical
    try:
        collection = task4.get_collection()
    except ModuleNotFoundError:
        return []
    try:
        query_embedding = task4.embed_texts([search_query])[0]
    except ModuleNotFoundError:
        return []
    raw = collection.query(query_embeddings=[query_embedding], n_results=top_k, include=["documents", "metadatas", "distances"])
    documents = raw.get("documents", [[]])[0]
    metadatas = raw.get("metadatas", [[]])[0]
    distances = raw.get("distances", [[]])[0]
    results: list[SearchResult] = []
    for document, metadata, distance in zip(documents, metadatas, distances, strict=True):
        if isinstance(document, str) and isinstance(metadata, dict) and isinstance(distance, (int, float)):
            results.append({"content": document, "score": round(max(0.0, 1.0 - float(distance)), 4), "metadata": metadata})
    results.sort(key=lambda result: result["score"], reverse=True)
    return results[:top_k]


if __name__ == "__main__":
    for result in semantic_search("quy định trả hàng hoàn tiền shopee", top_k=5):
        print(f"[{result['score']:.3f}] {result['content'][:100]}...")
