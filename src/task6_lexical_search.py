"""
Task 6 — Lexical Search Module (BM25 + TF-IDF char n-gram fallback).

Role 4 — Sparse Retrieval & Fallback Dev.

BM25 hoạt động thế nào:
    - Term Frequency (TF): từ xuất hiện nhiều trong document → điểm cao
    - Inverse Document Frequency (IDF): từ hiếm → quan trọng hơn
    - Document length normalization: document dài không bị ưu tiên quá mức
    - score(q,d) = Σ IDF(qi) * (tf(qi,d) * (k1+1)) / (tf(qi,d) + k1*(1-b+b*|d|/avgdl))
    - k1=1.5 (term saturation), b=0.75 (length normalization)
Cài đặt:
    pip install rank-bm25 scikit-learn numpy
"""

from __future__ import annotations

import importlib
import os
import re
import sys
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

STANDARDIZED_DIR = PROJECT_ROOT / "data" / "standardized"
FIXTURE_DIR = PROJECT_ROOT / "myrole" / "fixtures" / "sample_corpus"
DEFAULT_CHROMA_DIR = PROJECT_ROOT / "chroma_db"
DEFAULT_COLLECTION = "ecommerce_support_docs"

# =============================================================================
# CONFIGURATION
# =============================================================================

# Khớp tham số chunking của Task 4 (LAB_GUIDE: size=800, overlap=100) để chunk
# tự cắt ở đây trùng với chunk trong ChromaDB khi phải fallback đọc markdown.
CHUNK_SIZE = 800
CHUNK_OVERLAP = 100

BM25_K1 = 1.5           # term saturation
BM25_B = 0.75           # length normalization
MIN_SCORE = 1e-6        # dưới ngưỡng này coi như không match
CHAR_FALLBACK_SCALE = 0.1   # scale điểm TF-IDF char n-gram cho nhỏ hơn thang BM25

# Stopword tối thiểu — bỏ từ nối để BM25 chấm điểm dựa trên từ mang nghĩa.
STOPWORDS = {
    # tiếng Việt
    "và", "là", "của", "các", "có", "cho", "được", "trong", "với", "khi", "thì",
    "đã", "này", "đó", "một", "những", "tại", "về", "theo", "hoặc", "nếu", "bị",
    "do", "từ", "đến", "như", "mà", "ở", "ra", "vào", "bao", "nhiêu", "gì", "nào",
    "tôi", "bạn", "không", "để", "sẽ", "còn", "cũng", "hơn", "rồi",
    # tiếng Anh (corpus có thể lẫn tài liệu song ngữ)
    "the", "a", "an", "of", "and", "or", "to", "for", "in", "on", "is", "are",
    "what", "how", "do", "does", "i", "my", "it",
}

CORPUS: list[dict] = []  # List of {'content': str, 'metadata': dict} — nạp lazy

# Cache module-level
_BM25 = None
_TFIDF = None               # (vectorizer, matrix)
_CORPUS_SOURCE = "chưa nạp"
_CORPUS_CHUNKER = "-"       # "task4" = chunk khớp ChromaDB, "role4" = splitter nội bộ


# =============================================================================
# TEXT UTILS
# =============================================================================

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def fold_diacritics(text: str) -> str:
    """Bỏ dấu tiếng Việt: 'nghỉ phép' → 'nghi phep', 'đơn' → 'don'."""
    text = text.replace("đ", "d").replace("Đ", "D")
    decomposed = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def has_diacritics(text: str) -> bool:
    """True nếu chuỗi có ít nhất 1 ký tự tiếng Việt có dấu."""
    return fold_diacritics(text) != text


# STOPWORDS lưu dạng có dấu; bản bỏ dấu dùng cho lớp token đã fold.
_STOPWORDS_FOLDED = {fold_diacritics(w) for w in STOPWORDS}


def _tokenize(text: str, drop_stopwords: bool = True) -> list[str]:
    """Chuẩn hoá NFC → lowercase → tách token unicode → bỏ stopword."""
    text = unicodedata.normalize("NFC", text).lower()
    tokens = _WORD_RE.findall(text)
    if drop_stopwords:
        kept = [t for t in tokens if t not in STOPWORDS]
        # Query toàn stopword ("cái gì thế nào") → giữ nguyên còn hơn thành rỗng
        if kept:
            return kept
    return tokens


def _index_tokens(text: str) -> list[str]:
    """
    Token dùng để INDEX: token có dấu + biến thể bỏ dấu (chỉ khi khác nhau).

    Nhờ vậy một chunk chứa 'nghỉ hằng năm' match được cả query 'nghỉ hằng năm'
    lẫn 'nghi hang nam' mà không phải build 2 index riêng.
    """
    tokens = _tokenize(text)
    folded = [
        f for t in tokens
        if (f := fold_diacritics(t)) != t and f not in _STOPWORDS_FOLDED
    ]
    return tokens + folded


def _query_tokens(query: str) -> list[str]:
    """
    Token dùng để QUERY.

    - Query có dấu → giữ nguyên (match chính xác, không nhiễu sang từ đồng âm).
    - Query không dấu → bỏ dấu luôn để bắt vào lớp token đã fold của index, và lọc
      stopword lần nữa trên dạng đã bỏ dấu (STOPWORDS lưu dạng có dấu nên 'nhieu',
      'cua' sẽ lọt lưới nếu chỉ lọc một lần).
    """
    tokens = _tokenize(query)
    if has_diacritics(query):
        return tokens
    folded = [fold_diacritics(t) for t in tokens]
    kept = [t for t in folded if t not in _STOPWORDS_FOLDED]
    return kept or folded


# =============================================================================
# CORPUS LOADING
# =============================================================================

def _split_text(text: str) -> list[str]:
    """Cắt text thành chunk ~CHUNK_SIZE ký tự, overlap CHUNK_OVERLAP."""
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )
        return [c for c in splitter.split_text(text) if c.strip()]
    except ImportError:
        pass

    # Fallback không cần langchain: gom đoạn cho đến khi chạm CHUNK_SIZE
    chunks: list[str] = []
    buffer = ""
    for para in text.split("\n\n"):
        if len(buffer) + len(para) + 2 <= CHUNK_SIZE:
            buffer = f"{buffer}\n\n{para}" if buffer else para
            continue
        if buffer:
            chunks.append(buffer.strip())
        buffer = (chunks[-1][-CHUNK_OVERLAP:] + "\n\n" + para) if chunks else para
    if buffer.strip():
        chunks.append(buffer.strip())
    return [c for c in chunks if c.strip()]


def _chroma_config() -> tuple[Path, str]:
    """Lấy cấu hình Chroma của Role 3 (Task 4) nếu import được, không thì mặc định."""
    chroma_dir, collection = DEFAULT_CHROMA_DIR, DEFAULT_COLLECTION
    try:
        task4 = importlib.import_module("src.task4_chunking_indexing")
        chroma_dir = Path(getattr(task4, "CHROMA_DIR", chroma_dir))
        collection = getattr(task4, "COLLECTION_NAME", collection)
    except Exception:
        pass
    # Env luôn thắng — để đổi nhanh lúc demo mà không sửa code
    return (
        Path(os.getenv("CHROMA_DIR", str(chroma_dir))),
        os.getenv("CHROMA_COLLECTION", collection),
    )


def _load_from_chroma() -> list[dict]:
    """Đọc thẳng chunk đã index ra khỏi ChromaDB (nguồn ưu tiên số 1)."""
    chroma_dir, collection_name = _chroma_config()
    if not chroma_dir.exists():
        return []
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(chroma_dir))
        try:
            collection = client.get_collection(collection_name)
        except Exception:
            # Role 3 đổi tên collection → lấy collection nhiều dữ liệu nhất
            candidates = client.list_collections()
            if not candidates:
                return []
            collection = max(
                (client.get_collection(c.name) for c in candidates),
                key=lambda c: c.count(),
            )
        data = collection.get(include=["documents", "metadatas"])
    except Exception as exc:  # chromadb chưa cài / DB hỏng / dimension mismatch
        print(f"  ⚠ Không đọc được ChromaDB ({type(exc).__name__}: {exc})")
        return []

    documents = data.get("documents") or []
    metadatas = data.get("metadatas") or [{}] * len(documents)
    return [
        {"content": doc, "metadata": dict(meta or {})}
        for doc, meta in zip(documents, metadatas)
        if doc and doc.strip()
    ]


def _load_from_task4() -> list[dict]:
    """
    Chunk `data/standardized/` bằng CHÍNH hàm của Task 4 (Role 3).

    Dùng lại `load_documents()` + `chunk_documents()` thay vì tự cắt: chunk sinh ra
    trùng từng ký tự và trùng metadata (kể cả `customer_role`) với thứ nằm trong
    ChromaDB, nên khoá fusion `source#chunk_index` của RRF khớp ngay cả khi chưa
    build `chroma_db/`.
    """
    try:
        task4 = importlib.import_module("src.task4_chunking_indexing")
        chunks = task4.chunk_documents(task4.load_documents())
    except Exception as exc:
        print(f"  ⚠ Không dùng được chunker Task 4 ({type(exc).__name__}: {exc})")
        return []
    return [
        {"content": c["content"], "metadata": dict(c["metadata"])}
        for c in chunks
        if c.get("content", "").strip()
    ]


def _load_from_markdown(directory: Path, doc_type_default: str = "unknown") -> list[dict]:
    """Đọc *.md trong thư mục rồi chunk theo đúng tham số của Task 4."""
    if not directory.exists():
        return []
    corpus: list[dict] = []
    for md_file in sorted(directory.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        parts = str(md_file).replace("\\", "/").lower()
        doc_type = (
            "legal" if "/legal" in parts
            else "news" if "/news" in parts
            else doc_type_default
        )
        for i, chunk_text in enumerate(_split_text(text)):
            corpus.append({
                "content": chunk_text,
                "metadata": {
                    "source": md_file.name,
                    "type": doc_type,
                    "chunk_index": i,
                },
            })
    return corpus


def load_corpus(force_reload: bool = False) -> list[dict]:
    """
    Nạp corpus theo thứ tự ưu tiên, dừng ở nguồn đầu tiên có dữ liệu:
        1. ChromaDB — chunk y hệt semantic search đang dùng
        2. data/standardized/ chunk bằng hàm của Task 4 — vẫn khớp ChromaDB
        3. data/standardized/ chunk bằng splitter nội bộ — khi Task 4 chưa import được
        4. myrole/fixtures/sample_corpus/ — dữ liệu dev, chỉ để chạy thử

    Returns:
        List of {'content': str, 'metadata': dict}
    """
    global CORPUS, _CORPUS_SOURCE, _CORPUS_CHUNKER
    if CORPUS and not force_reload:
        return CORPUS

    for source_name, chunker, loader in (
        ("chroma", "task4", _load_from_chroma),
        ("standardized", "task4", _load_from_task4),
        ("standardized", "role4", lambda: _load_from_markdown(STANDARDIZED_DIR)),
        ("fixtures", "role4", lambda: _load_from_markdown(FIXTURE_DIR, "legal")),
    ):
        corpus = loader()
        if corpus:
            CORPUS, _CORPUS_SOURCE, _CORPUS_CHUNKER = corpus, source_name, chunker
            return CORPUS

    CORPUS, _CORPUS_SOURCE, _CORPUS_CHUNKER = [], "trống", "-"
    return CORPUS


def get_corpus_info() -> dict:
    """Thông tin corpus đang dùng — để demo/README in ra cho rõ."""
    corpus = load_corpus()
    return {
        "source": _CORPUS_SOURCE,
        "chunker": _CORPUS_CHUNKER,
        "n_chunks": len(corpus),
        "n_documents": len({c["metadata"].get("source") for c in corpus}),
    }


def reset_index() -> None:
    """Xoá cache corpus + index (dùng trong test hoặc sau khi reindex Chroma)."""
    global CORPUS, _BM25, _TFIDF, _CORPUS_SOURCE, _CORPUS_CHUNKER
    CORPUS, _BM25, _TFIDF = [], None, None
    _CORPUS_SOURCE, _CORPUS_CHUNKER = "chưa nạp", "-"


# =============================================================================
# INDEX
# =============================================================================

def build_bm25_index(corpus: list[dict]):
    """
    Xây dựng BM25 index từ corpus.

    Args:
        corpus: List of {'content': str, 'metadata': dict}

    Returns:
        BM25Okapi index (None nếu corpus rỗng).
    """
    if not corpus:
        return None
    from rank_bm25 import BM25Okapi

    tokenized_corpus = [_index_tokens(doc["content"]) for doc in corpus]
    return BM25Okapi(tokenized_corpus, k1=BM25_K1, b=BM25_B)


def _get_bm25():
    global _BM25
    if _BM25 is None:
        _BM25 = build_bm25_index(load_corpus())
    return _BM25


def _get_tfidf():
    """Vectorizer char n-gram (3-5) trên toàn corpus — dựng lazy vì chỉ dùng khi cần."""
    global _TFIDF
    if _TFIDF is None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        corpus = load_corpus()
        if not corpus:
            return None
        texts = [fold_diacritics(c["content"].lower()) for c in corpus]
        vectorizer = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=1)
        matrix = vectorizer.fit_transform(texts)
        _TFIDF = (vectorizer, matrix)
    return _TFIDF


# =============================================================================
# SEARCH
# =============================================================================

def _char_tfidf_search(query: str, top_k: int) -> list[dict]:
    """
    Fallback khi BM25 không match token nào: so khớp theo char n-gram (TF-IDF).

    Bắt được sai chính tả / viết tắt / khác ngôn ngữ vì không cần trùng nguyên từ,
    chỉ cần trùng chuỗi 3–5 ký tự.
    """
    tfidf = _get_tfidf()
    if tfidf is None:
        return []
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity

    vectorizer, matrix = tfidf
    query_vec = vectorizer.transform([fold_diacritics(query.lower())])
    sims = cosine_similarity(query_vec, matrix)[0]

    corpus = load_corpus()
    order = np.argsort(sims)[::-1][:top_k]
    results = []
    for idx in order:
        score = float(sims[idx]) * CHAR_FALLBACK_SCALE
        if score <= MIN_SCORE:
            continue
        results.append({
            "content": corpus[idx]["content"],
            "score": round(score, 6),
            "metadata": {**corpus[idx]["metadata"], "retriever": "tfidf_char"},
        })
    return results


def lexical_search(
    query: str,
    top_k: int = 10,
    min_score: float = MIN_SCORE,
    use_char_fallback: bool = True,
) -> list[dict]:
    """
    Tìm kiếm từ khóa sử dụng BM25 (fallback TF-IDF char n-gram khi BM25 trắng tay).

    Args:
        query: Câu truy vấn
        top_k: Số lượng kết quả tối đa
        min_score: Ngưỡng điểm tối thiểu để giữ kết quả
        use_char_fallback: Bật lớp TF-IDF char n-gram khi BM25 không match gì

    Returns:
        List of {'content': str, 'score': float, 'metadata': dict}
        Sorted by score descending.
    """
    corpus = load_corpus()
    if not corpus or not query.strip():
        return []

    bm25 = _get_bm25()
    if bm25 is None:
        return []

    import numpy as np

    scores = bm25.get_scores(_query_tokens(query))
    order = np.argsort(scores)[::-1][:top_k]

    results = []
    for idx in order:
        score = float(scores[idx])
        if score <= min_score:
            continue
        results.append({
            "content": corpus[idx]["content"],
            "score": round(score, 4),
            "metadata": {**corpus[idx]["metadata"], "retriever": "bm25"},
        })

    if not results and use_char_fallback:
        return _char_tfidf_search(query, top_k)
    return results


if __name__ == "__main__":
    info = get_corpus_info()
    print(f"Corpus: {info['n_chunks']} chunks / {info['n_documents']} tài liệu "
          f"(nguồn: {info['source']})\n")

    for q in [
        "thời gian thử việc tối đa là bao lâu",
        "lương thử việc ít nhất bao nhiêu phần trăm",
        "nghi hang nam duoc bao nhieu ngay",   # không dấu → lớp token đã fold
        "làm thêm giờ tối đa trong một năm",
        "công thức nấu phở bò",                # lạc đề → điểm rất thấp / rơi xuống TF-IDF
    ]:
        print(f"Query: {q}")
        for r in lexical_search(q, top_k=3):
            retriever = r["metadata"].get("retriever")
            print(f"  [{r['score']:.3f}] ({retriever}) "
                  f"{r['metadata'].get('source')} :: {r['content'][:70]}...")
        print()
