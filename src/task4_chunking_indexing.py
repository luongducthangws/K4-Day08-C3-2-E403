"""Task 4: load, chunk, embed, and index standardized Markdown documents."""
from __future__ import annotations

from functools import lru_cache
import os
from pathlib import Path
from typing import Final, Protocol, TypedDict

STANDARDIZED_DIR: Path = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR: Path = Path(__file__).parent.parent / "chroma_db"
CHUNK_SIZE: Final = 800
CHUNK_OVERLAP: Final = 100
CHUNKING_METHOD: Final = "recursive_character_separators"
SEPARATORS: Final = ["\n\n", "\n", ". ", " ", ""]
EMBEDDING_MODEL: Final = "BAAI/bge-m3"
EMBEDDING_DIM: Final = 1024
VECTOR_STORE: Final = "chromadb"
COLLECTION_NAME: Final = "ecommerce_support_docs"
INDEX_BATCH_SIZE: Final = 16


class Metadata(TypedDict, total=False):
    source: str
    type: str
    customer_role: str
    chunk_index: int


class Document(TypedDict):
    content: str
    metadata: Metadata
    embedding: list[float]


class Embedder(Protocol):
    def encode(self, texts: list[str], **kwargs: bool) -> list[list[float]]: ...


class Collection(Protocol):
    def upsert(self, *, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[Metadata]) -> None: ...
    def get(self, *, include: list[str]) -> dict[str, list[str]]: ...
    def delete(self, *, ids: list[str]) -> None: ...


def _customer_role(source: str, metadata: Metadata) -> str:
    """Resolve trusted role taxonomy while preserving valid incoming metadata."""
    incoming = metadata.get("customer_role")
    if incoming in {"buyer", "seller", "both", "unknown"}:
        return incoming
    normalized = source.lower()
    if "both" in normalized:
        return "both"
    if "seller" in normalized or "merchant" in normalized:
        return "seller"
    if "buyer" in normalized or "customer" in normalized:
        return "buyer"
    return "unknown"


def load_documents() -> list[Document]:
    """Load UTF-8 Markdown recursively with stable relative source metadata."""
    if not STANDARDIZED_DIR.exists():
        return []
    documents: list[Document] = []
    for path in sorted(STANDARDIZED_DIR.rglob("*.md")):
        relative = path.relative_to(STANDARDIZED_DIR).as_posix()
        document_type = relative.split("/", maxsplit=1)[0] if "/" in relative else "unknown"
        metadata: Metadata = {"source": relative, "type": document_type}
        metadata["customer_role"] = _customer_role(relative, metadata)
        documents.append({"content": path.read_text(encoding="utf-8"), "metadata": metadata, "embedding": []})
    return documents


def _recursive_parts(text: str, separators: list[str]) -> list[str]:
    if len(text) <= CHUNK_SIZE:
        return [text]
    if not separators:
        return [text[index : index + CHUNK_SIZE] for index in range(0, len(text), CHUNK_SIZE)]
    separator = separators[0]
    if separator and separator in text:
        pieces = text.split(separator)
        parts: list[str] = []
        current = ""
        for piece in pieces:
            candidate = piece if not current else current + separator + piece
            if len(candidate) <= CHUNK_SIZE:
                current = candidate
            else:
                if current:
                    parts.extend(_recursive_parts(current, separators[1:]))
                current = piece
        if current:
            parts.extend(_recursive_parts(current, separators[1:]))
        return parts
    return _recursive_parts(text, separators[1:])


def _split_text(text: str) -> list[str]:
    """Recursively split on paragraph, line, sentence, word, then character boundaries."""
    if not text:
        return []
    parts = _recursive_parts(text, SEPARATORS)
    normalized = "".join(parts)
    step = CHUNK_SIZE - CHUNK_OVERLAP
    return [normalized[start : start + CHUNK_SIZE] for start in range(0, len(normalized), step)]


def chunk_documents(documents: list[Document]) -> list[Document]:
    """Split documents into 800-character chunks with 100-character overlap."""
    chunks: list[Document] = []
    for document in documents:
        source = document["metadata"].get("source", "unknown")
        for index, content in enumerate(_split_text(document["content"])):
            metadata = {**document["metadata"], "source": source, "chunk_index": index}
            chunks.append({"content": content, "metadata": metadata, "embedding": []})
    return chunks


@lru_cache(maxsize=1)
def get_embedding_model() -> Embedder:
    """Return one lazily loaded shared BGE-M3 model."""
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed text using the shared cached local model."""
    if not texts:
        return []
    embeddings = get_embedding_model().encode(texts, normalize_embeddings=True)
    # ChromaDB validates Python ``float``/``int`` values.  SentenceTransformers
    # returns NumPy float32 scalars, which recent ChromaDB versions reject when
    # they are merely wrapped with ``list(vector)``.
    return [[float(value) for value in vector] for vector in embeddings]


def embed_chunks(chunks: list[Document]) -> list[Document]:
    """Add embeddings to chunks without changing their content or metadata."""
    embeddings = embed_texts([chunk["content"] for chunk in chunks])
    return [{**chunk, "embedding": embedding} for chunk, embedding in zip(chunks, embeddings, strict=True)]


def get_collection() -> Collection:
    """Open persistent cosine collection; kept injectable for tests."""
    import chromadb
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def index_to_vectorstore(chunks: list[Document]) -> None:
    """Upsert chunks with deterministic IDs based on source and chunk index."""
    if not chunks:
        return
    collection = get_collection()
    ids = [f"{chunk['metadata']['source']}::chunk-{chunk['metadata']['chunk_index']}" for chunk in chunks]
    existing = set(collection.get(include=[]).get("ids", []))
    stale_ids = sorted(existing - set(ids))
    if stale_ids:
        collection.delete(ids=stale_ids)
    collection.upsert(
        ids=ids,
        documents=[chunk["content"] for chunk in chunks],
        embeddings=[chunk["embedding"] for chunk in chunks],
        metadatas=[chunk["metadata"] for chunk in chunks],
    )


def run_pipeline(max_chunks: int | None = None) -> None:
    """Load, embed in bounded batches, and persist standardized documents.

    Batching avoids holding every BGE-M3 embedding in RAM and makes progress
    visible on CPU-only Windows machines. ``max_chunks`` is useful for a quick
    smoke-test index; normal runs leave it as ``None`` and index the full corpus.
    """
    chunks = chunk_documents(load_documents())
    if max_chunks is not None:
        chunks = chunks[:max(0, max_chunks)]
    if not chunks:
        return

    collection = get_collection()
    expected_ids = {
        f"{chunk['metadata']['source']}::chunk-{chunk['metadata']['chunk_index']}"
        for chunk in chunks
    }
    # Only prune when building the complete index. A smoke-test index must not
    # remove batches written by an earlier complete run.
    if max_chunks is None:
        existing = set(collection.get(include=[]).get("ids", []))
        stale_ids = sorted(existing - expected_ids)
        if stale_ids:
            collection.delete(ids=stale_ids)

    for start in range(0, len(chunks), INDEX_BATCH_SIZE):
        batch = embed_chunks(chunks[start : start + INDEX_BATCH_SIZE])
        collection.upsert(
            ids=[
                f"{item['metadata']['source']}::chunk-{item['metadata']['chunk_index']}"
                for item in batch
            ],
            documents=[item["content"] for item in batch],
            embeddings=[item["embedding"] for item in batch],
            metadatas=[item["metadata"] for item in batch],
        )
        print(f"Indexed {min(start + len(batch), len(chunks))}/{len(chunks)} chunks")


if __name__ == "__main__":
    max_chunks_env = os.getenv("INDEX_MAX_CHUNKS", "").strip()
    run_pipeline(int(max_chunks_env) if max_chunks_env else None)
