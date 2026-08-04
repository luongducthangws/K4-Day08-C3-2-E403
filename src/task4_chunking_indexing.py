"""
Task 4 — Chunking & Indexing vào Vector Store.

Hướng dẫn:
    1. Đọc toàn bộ markdown files từ data/standardized/
    2. Chọn 1 chunking strategy (giải thích lý do)
    3. Chọn 1 embedding model (giải thích lý do)
    4. Index vào vector store (ChromaDB khuyến cáo — đơn giản, local, không cần Docker)

Chunking options (langchain-text-splitters):
    - RecursiveCharacterTextSplitter: an toàn, phổ biến — nhưng cắt theo số ký tự cố định,
      không biết ranh giới Điều/Khoản, dễ cắt đôi 1 Điều luật giữa 2 chunk khác nhau.
    - MarkdownHeaderTextSplitter: tốt cho file có heading (##) — phù hợp cho data/standardized/news/
      (bài viết crawl, không có cấu trúc Điều/Khoản).
    - SemanticChunker: dùng embedding để tách (nâng cao, tốn compute) — không cần thiết khi văn
      bản đã có ranh giới cấu trúc rõ ràng sẵn (như luật), phù hợp hơn cho văn bản prose tự do.
    - Chunk theo Điều/Khoản (custom, regex-based) — KHUYẾN NGHỊ cho data/standardized/legal/
      (Bộ luật Lao động, Nghị định...): mỗi chunk = 1 Điều (hoặc 1 Khoản nếu Điều quá dài).
      Lý do: Task 10 yêu cầu trích dẫn dạng "[Điều 25, Bộ luật Lao động 2019]" — chunk theo
      ranh giới Điều giữ nguyên vẹn 1 đơn vị pháp lý, tránh cắt đôi ý và trích dẫn sai/mơ hồ.
      Vì độ dài Điều rất lệch nhau, nên dùng HYBRID: parse theo "Điều N." làm đơn vị chính,
      nếu 1 Điều vượt CHUNK_SIZE thì chẻ tiếp theo Khoản ("1.", "2." con trong Điều đó) nhưng
      vẫn giữ dieu_number trong metadata để trích dẫn đúng.

Embedding model options (chọn 1, cân nhắc đánh đổi cài đặt nặng vs cần API key):
    - sentence-transformers/all-MiniLM-L6-v2 hoặc BAAI/bge-m3 — chạy local, không
      cần API key, nhưng cài nặng (~1-2GB vì kéo theo torch)
    - Google models/text-embedding-004 (768 dim) — nhẹ, cần GEMINI_API_KEY
    - OpenAI text-embedding-3-small (1536 dim) — nhẹ, cần OPENAI_API_KEY
    Gợi ý: đọc EMBEDDING_PROVIDER từ .env (os.getenv("EMBEDDING_PROVIDER", "sentence_transformers"))
    để cả nhóm có thể đổi provider mà không sửa code — nhớ đổi provider phải xoá
    chroma_db/ cũ và reindex vì dimension khác nhau (1024/768/1536) không tương thích ngược.

Vector store options:
    - ChromaDB (khuyến cáo: đơn giản, local persistent, không cần Docker)
    - Weaviate (hỗ trợ hybrid search built-in, cần Docker/Cloud)
    - FAISS (chỉ dense search)

Cài đặt:
    pip install langchain-text-splitters sentence-transformers chromadb

Lưu ý quan trọng: nếu sau này đổi corpus (đổi chủ đề, thêm/bớt tài liệu), phải XÓA
chroma_db/ cũ trước khi reindex — nếu không, chunk cũ và mới sẽ tồn tại lẫn lộn
trong cùng collection, retrieval sẽ trả về kết quả rác từ dữ liệu cũ.
"""

from pathlib import Path

STANDARDIZED_DIR = Path(__file__).parent.parent / "data" / "standardized"
CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn của bạn trong comment
# =============================================================================

# TODO: Chọn chunking strategy và giải thích vì sao
# Khuyến nghị: hybrid theo loại tài liệu —
#   type == "legal" (Bộ luật/Nghị định, có "Điều N.") → CHUNKING_METHOD = "legal_structure"
#   type == "news"  (bài viết crawl, không có Điều/Khoản) → "recursive" hoặc "markdown_header"
# CHUNK_SIZE ở đây đóng vai trò NGƯỠNG chẻ tiếp (không phải kích thước chunk cố định) khi
# dùng "legal_structure": nếu 1 Điều dài hơn CHUNK_SIZE ký tự thì chẻ theo Khoản bên trong.
CHUNK_SIZE = 800        # Vì sao 800 (không phải 500)? 1 Điều luật thường dài hơn 1 đoạn văn thường,
                        # ngưỡng 500 sẽ chẻ hầu hết các Điều ra dù không cần thiết.
CHUNK_OVERLAP = 50      # Vì sao chọn 50? ... (chỉ áp dụng cho nhánh recursive/news)
CHUNKING_METHOD = "legal_structure"  # "legal_structure" | "recursive" | "markdown_header" | "semantic"

# TODO: Chọn embedding model và giải thích
EMBEDDING_MODEL = "BAAI/bge-m3"  # Vì sao? Multilingual, tốt cho tiếng Việt lẫn tiếng Anh
EMBEDDING_DIM = 1024

# TODO: Chọn vector store
VECTOR_STORE = "chromadb"  # "chromadb" | "weaviate" | "faiss"
COLLECTION_NAME = "ecommerce_support_docs"


# =============================================================================
# IMPLEMENTATION
# =============================================================================

def load_documents() -> list[dict]:
    """
    Đọc toàn bộ markdown files từ data/standardized/.

    Returns:
        List of {'content': str, 'metadata': {'source': str, 'type': str}}
    """
    # TODO: Iterate qua STANDARDIZED_DIR, đọc .md files
    # documents = []
    # for md_file in STANDARDIZED_DIR.rglob("*.md"):
    #     content = md_file.read_text(encoding="utf-8")
    #     doc_type = "legal" if "legal" in str(md_file) else "news"
    #     documents.append({
    #         "content": content,
    #         "metadata": {"source": md_file.name, "type": doc_type}
    #     })
    # return documents
    raise NotImplementedError("Implement load_documents")


def chunk_documents(documents: list[dict]) -> list[dict]:
    """
    Chunk documents theo strategy đã chọn.

    Returns:
        List of {'content': str, 'metadata': dict} — mỗi item là 1 chunk
    """
    # TODO: Implement chunking
    #
    # Ví dụ HYBRID (khuyến nghị) — legal_structure cho type=="legal", recursive cho type=="news":
    # import re
    # from langchain_text_splitters import RecursiveCharacterTextSplitter
    #
    # DIEU_PATTERN = re.compile(r"^Điều\s+(\d+)\.", re.MULTILINE)
    #
    # def chunk_by_dieu(content: str, metadata: dict) -> list[dict]:
    #     matches = list(DIEU_PATTERN.finditer(content))
    #     if not matches:  # văn bản không có "Điều N." (vd. lời mở đầu) → fallback recursive
    #         return chunk_by_recursive(content, metadata)
    #     boundaries = [m.start() for m in matches] + [len(content)]
    #     chunks = []
    #     for i, m in enumerate(matches):
    #         dieu_text = content[boundaries[i]:boundaries[i + 1]].strip()
    #         dieu_num = m.group(1)
    #         if len(dieu_text) <= CHUNK_SIZE:
    #             chunks.append({
    #                 "content": dieu_text,
    #                 "metadata": {**metadata, "chunk_index": i, "dieu_number": dieu_num},
    #             })
    #         else:
    #             # Điều quá dài → chẻ tiếp theo Khoản, vẫn giữ dieu_number để trích dẫn đúng
    #             splitter = RecursiveCharacterTextSplitter(
    #                 chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
    #                 separators=["\n\d+\.\s", "\n\n", "\n", ". ", " "],
    #             )
    #             for j, sub in enumerate(splitter.split_text(dieu_text)):
    #                 chunks.append({
    #                     "content": sub,
    #                     "metadata": {**metadata, "chunk_index": f"{i}.{j}", "dieu_number": dieu_num},
    #                 })
    #     return chunks
    #
    # def chunk_by_recursive(content: str, metadata: dict) -> list[dict]:
    #     splitter = RecursiveCharacterTextSplitter(
    #         chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP,
    #         separators=["\n\n", "\n", ". ", " ", ""],
    #     )
    #     return [
    #         {"content": c, "metadata": {**metadata, "chunk_index": i}}
    #         for i, c in enumerate(splitter.split_text(content))
    #     ]
    #
    # chunks = []
    # for doc in documents:
    #     if doc["metadata"]["type"] == "legal":
    #         chunks.extend(chunk_by_dieu(doc["content"], doc["metadata"]))
    #     else:
    #         chunks.extend(chunk_by_recursive(doc["content"], doc["metadata"]))
    # return chunks
    #
    # Ví dụ THUẦN RecursiveCharacterTextSplitter (đơn giản hơn, nếu không muốn làm hybrid):
    # splitter = RecursiveCharacterTextSplitter(
    #     chunk_size=CHUNK_SIZE,
    #     chunk_overlap=CHUNK_OVERLAP,
    #     separators=["\n\n", "\n", ". ", " ", ""]
    # )
    # chunks = []
    # for doc in documents:
    #     splits = splitter.split_text(doc["content"])
    #     for i, chunk_text in enumerate(splits):
    #         chunks.append({
    #             "content": chunk_text,
    #             "metadata": {**doc["metadata"], "chunk_index": i}
    #         })
    # return chunks
    raise NotImplementedError("Implement chunk_documents")


def embed_chunks(chunks: list[dict]) -> list[dict]:
    """
    Embed toàn bộ chunks bằng model đã chọn.

    Returns:
        Mỗi chunk dict được thêm key 'embedding': list[float]
    """
    # TODO: Implement embedding
    #
    # Ví dụ với sentence-transformers (local, mặc định):
    # from sentence_transformers import SentenceTransformer
    #
    # model = SentenceTransformer(EMBEDDING_MODEL)
    # texts = [c["content"] for c in chunks]
    # embeddings = model.encode(texts, show_progress_bar=True)
    # for chunk, emb in zip(chunks, embeddings):
    #     chunk["embedding"] = emb.tolist()
    # return chunks
    #
    # Nâng cao (optional): nếu muốn cho cả nhóm chọn được provider qua .env, viết
    # 1 hàm embed_texts(texts) dispatch theo os.getenv("EMBEDDING_PROVIDER") sang
    # sentence-transformers | Google (genai.embed_content) | OpenAI (client.embeddings.create)
    # rồi gọi lại hàm đó ở đây và ở Task 5 — tránh viết logic embed lặp lại 2 nơi.
    raise NotImplementedError("Implement embed_chunks")


def index_to_vectorstore(chunks: list[dict]):
    """
    Lưu chunks vào vector store đã chọn.
    """
    # TODO: Implement indexing
    #
    # Ví dụ với ChromaDB:
    # import chromadb
    #
    # CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    # client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    # collection = client.get_or_create_collection(
    #     name=COLLECTION_NAME,
    #     metadata={"hnsw:space": "cosine"},
    # )
    #
    # ids = [f"{c['metadata']['source']}_chunk_{c['metadata']['chunk_index']}" for c in chunks]
    # collection.upsert(
    #     ids=ids,
    #     documents=[c["content"] for c in chunks],
    #     embeddings=[c["embedding"] for c in chunks],
    #     metadatas=[c["metadata"] for c in chunks],
    # )
    raise NotImplementedError("Implement index_to_vectorstore")


def run_pipeline():
    """Chạy toàn bộ pipeline: load → chunk → embed → index."""
    print("=" * 50)
    print("Task 4: Chunking & Indexing")
    print(f"  Chunking: {CHUNKING_METHOD} (size={CHUNK_SIZE}, overlap={CHUNK_OVERLAP})")
    print(f"  Embedding: {EMBEDDING_MODEL} (dim={EMBEDDING_DIM})")
    print(f"  Vector Store: {VECTOR_STORE}")
    print("=" * 50)

    docs = load_documents()
    print(f"\n✓ Loaded {len(docs)} documents")

    chunks = chunk_documents(docs)
    print(f"✓ Created {len(chunks)} chunks")

    chunks = embed_chunks(chunks)
    print(f"✓ Embedded {len(chunks)} chunks")

    index_to_vectorstore(chunks)
    print("✓ Indexed to vector store")


if __name__ == "__main__":
    run_pipeline()
