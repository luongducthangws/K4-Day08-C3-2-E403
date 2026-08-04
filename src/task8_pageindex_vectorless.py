"""
Task 8 — PageIndex Vectorless RAG (fallback khi hybrid search yếu).

Role 4 — Sparse Retrieval & Fallback Dev.

Cài đặt:
    pip install pageindex fpdf2
"""

from __future__ import annotations

import json
import os
import re
import time
import unicodedata
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STANDARDIZED_DIR = PROJECT_ROOT / "data" / "standardized"
FIXTURE_DIR = PROJECT_ROOT / "myrole" / "fixtures" / "sample_corpus"
PDF_DIR = PROJECT_ROOT / "pageindex_pdfs"          # đã có trong .gitignore
DOC_ID_CACHE = PROJECT_ROOT / "pageindex_doc_ids.json"  # đã có trong .gitignore

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY", "")
PAGEINDEX_MODE = os.getenv("PAGEINDEX_MODE", "auto").lower()  # auto | api | local
DEBUG_RAW = os.getenv("DEBUG_RAW", "") == "1"

POLL_TIMEOUT_S = 90
POLL_INTERVAL_S = 2.0
DOC_READY_TIMEOUT_S = 300   # dựng cây mục lục cho văn bản luật vài trăm KB khá lâu
PAGEINDEX_MAX_DOCS = 3      # chặn số tài liệu query mỗi lần để fallback không quá chậm

_READY_DOCS: set[str] = set()   # doc_id đã xác nhận sẵn sàng, khỏi poll lại mỗi query
MAX_SECTION_CHARS = 2000    # cắt bớt section quá dài trước khi đưa vào context LLM

# Font Unicode cho fpdf2 — font core của fpdf2 là latin-1, để nguyên thì toàn bộ
# tiếng Việt có dấu sẽ thành ký tự rác trong PDF gửi lên PageIndex.
UNICODE_FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("C:/Windows/Fonts/times.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]

# "## Điều 25. Thời gian thử việc" hoặc "Điều 25." đứng đầu dòng
_HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.+?)\s*$")
_ARTICLE_RE = re.compile(r"^\s*(Điều\s+\d+[a-z]?\s*[.:].*)$", re.IGNORECASE)
_WORD_RE = re.compile(r"\w+", re.UNICODE)


# =============================================================================
# Utils
# =============================================================================

def _fold(text: str) -> str:
    """Lowercase + bỏ dấu — dùng cho so khớp ở mức section."""
    text = text.lower().replace("đ", "d")
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text) if not unicodedata.combining(ch)
    )


def _tokens(text: str) -> list[str]:
    return _WORD_RE.findall(_fold(unicodedata.normalize("NFC", text)))


def _source_dir() -> Path | None:
    """Thư mục tài liệu: ưu tiên dữ liệu thật của Role 2, chưa có thì dùng fixture."""
    for directory in (STANDARDIZED_DIR, FIXTURE_DIR):
        if directory.exists() and any(directory.rglob("*.md")):
            return directory
    return None


def _resolve_mode() -> str:
    if PAGEINDEX_MODE in ("api", "local"):
        return PAGEINDEX_MODE
    return "api" if PAGEINDEX_API_KEY else "local"


# =============================================================================
# Chế độ LOCAL — vectorless theo cấu trúc tài liệu
# =============================================================================

def split_into_sections(text: str, source: str) -> list[dict]:
    """
    Cắt markdown thành section theo heading (#) và theo mẫu "Điều <số>.".

    Giữ nguyên section thay vì chunk theo ký tự — đó chính là điểm khác biệt của
    vectorless retrieval so với Task 4/5.
    """
    sections: list[dict] = []
    title = f"{source} (mở đầu)"
    buffer: list[str] = []

    def flush():
        body = "\n".join(buffer).strip()
        if body:
            sections.append({"title": title, "content": f"{title}\n\n{body}"})

    for line in text.splitlines():
        heading = _HEADING_RE.match(line) or _ARTICLE_RE.match(line)
        if heading:
            flush()
            title = heading.group(1).strip()
            buffer = []
            continue
        buffer.append(line)
    flush()
    return sections


def load_sections() -> list[dict]:
    """Đọc toàn bộ tài liệu và cắt thành section (có cache theo lần chạy)."""
    directory = _source_dir()
    if directory is None:
        return []

    sections: list[dict] = []
    for md_file in sorted(directory.rglob("*.md")):
        text = md_file.read_text(encoding="utf-8").strip()
        if not text:
            continue
        path_str = str(md_file).replace("\\", "/").lower()
        doc_type = "legal" if "/legal" in path_str else "news" if "/news" in path_str else "legal"
        for sec in split_into_sections(text, md_file.stem):
            sections.append({
                "content": sec["content"][:MAX_SECTION_CHARS],
                "metadata": {
                    "source": md_file.name,
                    "section": sec["title"],
                    "type": doc_type,
                    "engine": "local_structural",
                },
            })
    return sections


def local_structural_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval không cần API: chấm điểm ở mức SECTION thay vì chunk.

    Dùng BM25 trên toàn bộ section (không có rank_bm25 thì rơi về đếm từ khoá
    trùng nhau), điểm được normalize về 0–1 để Task 9 dễ so sánh.
    """
    sections = load_sections()
    if not sections or not query.strip():
        return []

    tokenized = [_tokens(s["content"]) for s in sections]
    query_tokens = _tokens(query)
    if not query_tokens:
        return []

    try:
        from rank_bm25 import BM25Okapi

        scores = list(BM25Okapi(tokenized).get_scores(query_tokens))
    except ImportError:
        scores = [
            sum(doc_tokens.count(t) for t in set(query_tokens)) / (len(doc_tokens) or 1)
            for doc_tokens in tokenized
        ]

    best = max(scores) if scores else 0.0
    if best <= 0:
        return []

    ranked = sorted(range(len(sections)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [
        {
            "content": sections[i]["content"],
            "score": round(float(scores[i]) / best, 4),   # 1.0 cho section tốt nhất
            "metadata": sections[i]["metadata"],
            "source": "pageindex",
        }
        for i in ranked
        if scores[i] > 0
    ]


# =============================================================================
# Chế độ API — PageIndex SDK thật
# =============================================================================

def _get_client():
    """Khởi tạo PageIndexClient (SDK có 2 đường import tuỳ phiên bản)."""
    if not PAGEINDEX_API_KEY:
        raise RuntimeError("Thiếu PAGEINDEX_API_KEY trong .env")
    try:
        from pageindex.client import PageIndexClient
    except ImportError:
        from pageindex import PageIndexClient  # type: ignore
    return PageIndexClient(api_key=PAGEINDEX_API_KEY)


def _unicode_font() -> Path:
    for font in UNICODE_FONT_CANDIDATES:
        if font.exists():
            return font
    raise RuntimeError(
        "Không tìm thấy font TTF Unicode để render PDF tiếng Việt. "
        "Tải DejaVuSans.ttf rồi thêm đường dẫn vào UNICODE_FONT_CANDIDATES."
    )


def markdown_to_pdf(md_path: Path, out_dir: Path = PDF_DIR) -> Path:
    """
    Convert markdown → PDF (PageIndex nhận PDF, không nhận .md).

    Bắt buộc add_font TTF Unicode, nếu dùng font core latin-1 của fpdf2 thì chữ
    tiếng Việt có dấu sẽ hỏng hoàn toàn trong PDF gửi lên.
    """
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_path = out_dir / f"{md_path.stem}.pdf"

    font_path = _unicode_font()
    pdf = FPDF()
    pdf.add_font("uni", "", str(font_path))
    pdf.set_font("uni", size=11)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    for line in md_path.read_text(encoding="utf-8").splitlines():
        # new_x=LMARGIN bắt buộc: mặc định fpdf2 để con trỏ ở lề PHẢI sau multi_cell,
        # dòng kế tiếp sẽ ném "Not enough horizontal space to render a single character".
        pdf.multi_cell(
            0, 6, line if line.strip() else " ",
            new_x=XPos.LMARGIN, new_y=YPos.NEXT,
        )
    pdf.output(str(pdf_path))
    return pdf_path


def _load_doc_ids() -> dict:
    if DOC_ID_CACHE.exists():
        return json.loads(DOC_ID_CACHE.read_text(encoding="utf-8"))
    return {}


def upload_documents(force: bool = False) -> dict:
    """
    Upload toàn bộ tài liệu lên PageIndex (md → PDF → submit_document).

    Trả về mapping {tên file: doc_id}, cache trong pageindex_doc_ids.json để lần
    sau khỏi upload lại (mỗi lần upload đều tốn quota).
    """
    directory = _source_dir()
    if directory is None:
        print("⚠ Chưa có tài liệu nào trong data/standardized/ — chờ Role 2 (Task 3).")
        return {}

    client = _get_client()
    doc_ids = {} if force else _load_doc_ids()

    for md_file in sorted(directory.rglob("*.md")):
        if md_file.name in doc_ids and not force:
            print(f"  • Bỏ qua (đã upload): {md_file.name}")
            continue
        pdf_path = markdown_to_pdf(md_file)
        resp = client.submit_document(str(pdf_path))
        if DEBUG_RAW:
            print(json.dumps(resp, ensure_ascii=False, indent=2, default=str))
        doc_id = resp.get("doc_id") or resp.get("id")
        if not doc_id:
            print(f"  ✗ Không lấy được doc_id cho {md_file.name}: {resp}")
            continue
        doc_ids[md_file.name] = doc_id
        print(f"  ✓ Uploaded: {md_file.name} -> {doc_id}")

    DOC_ID_CACHE.write_text(
        json.dumps(doc_ids, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return doc_ids


def _wait_until_ready(client, doc_id: str) -> bool:
    """
    Chờ PageIndex xử lý xong tài liệu trước khi cho phép truy vấn.

    `submit_document()` trả `doc_id` NGAY LẬP TỨC nhưng cây mục lục còn đang dựng —
    submit_query() lúc đó sẽ lỗi hoặc trả rỗng. SDK có sẵn `is_retrieval_ready(doc_id)`
    cho đúng việc này; văn bản luật vài trăm KB có thể mất vài phút.
    """
    if doc_id in _READY_DOCS:
        return True
    deadline = time.time() + DOC_READY_TIMEOUT_S
    while time.time() < deadline:
        try:
            if client.is_retrieval_ready(doc_id):
                _READY_DOCS.add(doc_id)
                return True
        except Exception as exc:
            print(f"  ⚠ Không kiểm tra được trạng thái {doc_id}: {exc}")
            return False
        time.sleep(POLL_INTERVAL_S)
    print(f"  ⚠ Tài liệu {doc_id} chưa sẵn sàng sau {DOC_READY_TIMEOUT_S}s")
    return False


def _poll_retrieval(client, retrieval_id: str) -> dict:
    """Chờ PageIndex xử lý xong truy vấn (có timeout để không treo demo)."""
    deadline = time.time() + POLL_TIMEOUT_S
    while time.time() < deadline:
        retrieval = client.get_retrieval(retrieval_id)
        status = str(retrieval.get("status", "")).lower()
        if status in ("completed", "success", "done", "finished"):
            return retrieval
        if status in ("failed", "error"):
            raise RuntimeError(f"PageIndex retrieval thất bại: {retrieval}")
        time.sleep(POLL_INTERVAL_S)
    raise TimeoutError(f"PageIndex không trả kết quả trong {POLL_TIMEOUT_S}s")


def _api_search(query: str, top_k: int = 5) -> list[dict]:
    """Query PageIndex thật trên các document đã upload."""
    doc_ids = _load_doc_ids()
    if not doc_ids:
        doc_ids = upload_documents()
    if not doc_ids:
        return []

    client = _get_client()
    results: list[dict] = []

    for file_name, doc_id in list(doc_ids.items())[:PAGEINDEX_MAX_DOCS]:
        if not _wait_until_ready(client, doc_id):
            continue
        submitted = client.submit_query(doc_id=doc_id, query=query)
        retrieval_id = submitted.get("retrieval_id") or submitted.get("id")
        if not retrieval_id:
            continue
        retrieval = _poll_retrieval(client, retrieval_id)
        if DEBUG_RAW:
            print(json.dumps(retrieval, ensure_ascii=False, indent=2, default=str))

        # retrieved_nodes[].relevant_contents[][] — in DEBUG_RAW để đối chiếu schema
        for node in retrieval.get("retrieved_nodes", []):
            for group in node.get("relevant_contents", []):
                for item in group:
                    content = (item or {}).get("relevant_content", "")
                    if not content.strip():
                        continue
                    results.append({
                        "content": content[:MAX_SECTION_CHARS],
                        "score": 0.0,   # PageIndex không trả score → gán theo rank bên dưới
                        "metadata": {
                            "source": file_name,
                            "section": item.get("section_title"),
                            "node_id": node.get("node_id"),
                            "engine": "pageindex_api",
                        },
                        "source": "pageindex",
                    })
        if len(results) >= top_k:
            break

    # PageIndex trả theo thứ tự liên quan giảm dần → quy đổi rank thành score
    for rank, item in enumerate(results[:top_k]):
        item["score"] = round(1.0 - 0.05 * rank, 4)
    return results[:top_k]


# =============================================================================
# Entry point dùng cho Task 9
# =============================================================================

def pageindex_search(query: str, top_k: int = 5) -> list[dict]:
    """
    Vectorless retrieval — fallback khi hybrid search không đủ bằng chứng.

    KHÔNG BAO GIỜ raise: hết key, hết quota, chưa có tài liệu → trả [] để pipeline
    Task 9 tự quyết định dùng kết quả hybrid hay báo "không đủ căn cứ trả lời".

    Returns:
        List of {'content', 'score', 'metadata', 'source': 'pageindex'}
    """
    mode = _resolve_mode()

    if mode == "api":
        try:
            results = _api_search(query, top_k)
            if results:
                return results
            print("  ⚠ PageIndex API không có kết quả → thử chế độ local")
        except Exception as exc:
            print(f"  ⚠ PageIndex API lỗi ({type(exc).__name__}: {exc}) → chuyển sang local")
        if PAGEINDEX_MODE == "api":   # bị ép chế độ api thì không tự ý đổi
            return []

    try:
        return local_structural_search(query, top_k)
    except Exception as exc:
        print(f"  ⚠ Local structural search lỗi ({type(exc).__name__}: {exc})")
        return []


if __name__ == "__main__":
    print(f"Chế độ: {_resolve_mode()} (PAGEINDEX_MODE={PAGEINDEX_MODE}, "
          f"có API key: {bool(PAGEINDEX_API_KEY)})")
    directory = _source_dir()
    print(f"Tài liệu: {directory if directory else 'chưa có'}\n")

    for q in [
        "công ty sa thải nhân viên trái luật thì phải bồi thường thế nào",
        "thử việc tối đa bao nhiêu ngày",
    ]:
        print(f"Query: {q}")
        for r in pageindex_search(q, top_k=3):
            print(f"  [{r['score']:.3f}] ({r['metadata'].get('engine')}) "
                  f"{r['metadata'].get('section')} — {r['content'][:70]}...")
        print()
