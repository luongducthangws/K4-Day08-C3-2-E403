"""
Task 7 — Reranking Module (RRF là phương pháp chính).

Role 4 — Sparse Retrieval & Fallback Dev.

RRF (Reciprocal Rank Fusion, Cormack et al. 2009):

    RRF(d) = Σ_r  1 / (k + rank_r(d))        với k = 60

Vì sao chọn RRF: hai ranker (semantic cosine và BM25) có thang điểm hoàn toàn khác
nhau (0–1 vs 0–20+), không thể cộng trực tiếp cũng không normalize được ổn định.
RRF chỉ dùng THỨ HẠNG nên miễn nhiễm với chênh lệch thang điểm, không cần API key,
không cần model, và tài liệu được cả hai ranker xếp hạng cao sẽ tự động lên đầu.
"""

from __future__ import annotations

import hashlib
import math
import os

RRF_K = 60          # smoothing constant (paper Cormack et al. 2009)
JINA_MODEL = "jina-reranker-v2-base-multilingual"


# =============================================================================
# Helpers
# =============================================================================

def _fusion_key(item: dict) -> str:
    """
    Khoá để nhận ra "cùng một chunk" giữa các ranked list khác nhau.

    Ưu tiên source + chunk_index (ổn định, ngắn); không có metadata thì hash nội dung.
    Nếu dense và sparse không sinh ra cùng khoá thì RRF không fuse được gì —
    đó là lý do Task 6 đọc chunk thẳng từ ChromaDB.
    """
    meta = item.get("metadata") or {}
    source, chunk_index = meta.get("source"), meta.get("chunk_index")
    if source is not None and chunk_index is not None:
        return f"{source}#{chunk_index}"
    content = item.get("content", "")
    return hashlib.sha1(content.encode("utf-8")).hexdigest()


def _as_ranked_lists(candidates) -> list[list[dict]]:
    """Chấp nhận cả 1 ranked list lẫn list-of-ranked-lists."""
    if not candidates:
        return []
    if isinstance(candidates[0], dict):
        return [list(candidates)]
    return [list(lst) for lst in candidates if lst]


def _cosine(vec_a, vec_b) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# =============================================================================
# RRF — phương pháp chính
# =============================================================================

def rerank_rrf(
    ranked_lists: list[list[dict]],
    top_k: int = 5,
    k: int = RRF_K,
    list_names: list[str] | None = None,
) -> list[dict]:
    """
    Reciprocal Rank Fusion — gộp kết quả từ nhiều ranker.

        RRF(d) = Σ 1 / (k + rank_r(d))

    Args:
        ranked_lists: Danh sách các ranked list (mỗi list từ 1 ranker), đã sort sẵn
        top_k: Số lượng kết quả cuối cùng
        k: Smoothing constant (default=60)
        list_names: Tên từng ranker, ví dụ ["dense", "sparse"]. Dùng để giữ lại
            điểm gốc trong `source_scores` — đặt tên "dense" thì điểm cosine gốc
            được bơm thêm vào key `dense_score` cho Task 9 dùng làm ngưỡng fallback.

    Returns:
        List of top_k candidates sorted by RRF score descending. Mỗi item giữ
        nguyên dict gốc và được bổ sung: score (= RRF), rrf_score, ranks,
        source_scores, và dense_score (nếu có).
    """
    lists = _as_ranked_lists(ranked_lists)
    if not lists:
        return []
    names = list_names or [f"ranker_{i}" for i in range(len(lists))]

    fused: dict[str, dict] = {}
    for name, ranked_list in zip(names, lists):
        for rank, item in enumerate(ranked_list, start=1):
            key = _fusion_key(item)
            entry = fused.get(key)
            if entry is None:
                entry = {**item, "ranks": {}, "source_scores": {}}
                fused[key] = entry
                entry["rrf_score"] = 0.0
            entry["rrf_score"] += 1.0 / (k + rank)
            entry["ranks"][name] = rank
            entry["source_scores"][name] = item.get("score")

    results = []
    for entry in fused.values():
        entry["score"] = round(entry["rrf_score"], 6)
        if "dense" in entry["source_scores"] and entry["source_scores"]["dense"] is not None:
            entry["dense_score"] = entry["source_scores"]["dense"]
        results.append(entry)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


# =============================================================================
# MMR — chọn kết quả vừa liên quan vừa đa dạng
# =============================================================================

def rerank_mmr(
    query_embedding: list[float],
    candidates: list[dict],
    top_k: int = 5,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Maximal Marginal Relevance.

        MMR = λ * sim(query, doc) - (1-λ) * max(sim(doc, selected_docs))

    Args:
        query_embedding: Vector embedding của query
        candidates: List of {'content', 'score', 'embedding', 'metadata'}
        top_k: Số lượng kết quả
        lambda_param: 1.0 = chỉ quan tâm relevance, 0.0 = chỉ quan tâm diversity

    Returns:
        List of top_k candidates đã chọn theo MMR (score = điểm MMR).
    """
    if not candidates:
        return []
    missing = [c for c in candidates if not c.get("embedding")]
    if missing:
        raise ValueError(
            "rerank_mmr cần mỗi candidate có key 'embedding'. "
            "Lấy embedding từ Task 4/5 (Chroma query include=['embeddings']) trước khi gọi."
        )

    candidates = [dict(c) for c in candidates]   # không sửa list của caller
    selected: list[int] = []
    remaining = list(range(len(candidates)))

    while remaining and len(selected) < top_k:
        best_idx, best_score = None, float("-inf")
        for idx in remaining:
            relevance = _cosine(query_embedding, candidates[idx]["embedding"])
            max_sim_selected = max(
                (_cosine(candidates[idx]["embedding"], candidates[s]["embedding"])
                 for s in selected),
                default=0.0,
            )
            mmr = lambda_param * relevance - (1 - lambda_param) * max_sim_selected
            if mmr > best_score:
                best_idx, best_score = idx, mmr
        selected.append(best_idx)
        remaining.remove(best_idx)
        candidates[best_idx] = {**candidates[best_idx], "score": round(best_score, 6)}

    return [candidates[i] for i in selected]


# =============================================================================
# Cross-encoder (Jina API) — tuỳ chọn, cần JINA_API_KEY
# =============================================================================

def rerank_cross_encoder(query: str, candidates: list[dict], top_k: int = 5) -> list[dict]:
    """
    Rerank bằng cross-encoder đa ngữ của Jina (chấm trực tiếp cặp query–document).

    Chính xác hơn RRF vì đọc cả query lẫn document cùng lúc, nhưng cần API key và
    tốn 1 lượt gọi mạng cho mỗi truy vấn.
    """
    api_key = os.getenv("JINA_API_KEY", "")
    if not api_key:
        raise RuntimeError("Thiếu JINA_API_KEY trong .env — không dùng được cross-encoder.")
    if not candidates:
        return []

    import requests

    flat = [c for lst in _as_ranked_lists(candidates) for c in lst]
    response = requests.post(
        "https://api.jina.ai/v1/rerank",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": JINA_MODEL,
            "query": query,
            "documents": [c["content"] for c in flat],
            "top_n": top_k,
        },
        timeout=30,
    )
    response.raise_for_status()
    return [
        {**flat[r["index"]], "score": r["relevance_score"], "reranker": "jina_cross_encoder"}
        for r in response.json()["results"]
    ]


# =============================================================================
# Main rerank interface
# =============================================================================

def rerank(
    query: str,
    candidates,
    top_k: int = 5,
    method: str = "rrf",
    query_embedding: list[float] | None = None,
    lambda_param: float = 0.7,
) -> list[dict]:
    """
    Interface thống nhất cho reranking.

    Args:
        query: Câu truy vấn
        candidates: MỘT ranked list, hoặc list-of-ranked-lists (nhiều ranker)
        top_k: Số lượng kết quả sau rerank
        method: "rrf" (mặc định) | "cross_encoder" | "mmr"
        query_embedding: Bắt buộc cho method="mmr"
        lambda_param: Trade-off relevance/diversity của MMR

    Returns:
        List of top_k candidates đã rerank, luôn có key 'score'.

    Ghi chú: truyền 1 list vào method "rrf" là hợp lệ — RRF trên một ranker chỉ
    chuyển thứ hạng thành điểm 1/(k+rank), giữ nguyên thứ tự. Nhờ vậy pipeline
    không bao giờ vỡ khi chỉ có một nguồn kết quả.
    """
    if not candidates:
        return []

    if method == "rrf":
        return rerank_rrf(candidates, top_k=top_k)

    if method == "cross_encoder":
        try:
            return rerank_cross_encoder(query, candidates, top_k)
        except Exception as exc:
            print(f"  ⚠ Cross-encoder lỗi ({exc}) → tự chuyển sang RRF")
            return rerank_rrf(candidates, top_k=top_k)

    if method == "mmr":
        flat = [c for lst in _as_ranked_lists(candidates) for c in lst]
        if query_embedding is None:
            raise ValueError("method='mmr' cần truyền query_embedding.")
        return rerank_mmr(query_embedding, flat, top_k=top_k, lambda_param=lambda_param)

    raise ValueError(f"Unknown rerank method: {method}")


if __name__ == "__main__":
    dense = [
        {"content": "Điều 25. Thời gian thử việc không quá 60 ngày với trình độ cao đẳng trở lên",
         "score": 0.71, "metadata": {"source": "01_thu_viec.md", "chunk_index": 3}},
        {"content": "Điều 26. Tiền lương thử việc ít nhất bằng 85% mức lương của công việc",
         "score": 0.64, "metadata": {"source": "01_thu_viec.md", "chunk_index": 5}},
        {"content": "Điều 113. Nghỉ hằng năm 12 ngày làm việc",
         "score": 0.32, "metadata": {"source": "04_nghi_phep.md", "chunk_index": 2}},
    ]
    sparse = [
        {"content": "Điều 26. Tiền lương thử việc ít nhất bằng 85% mức lương của công việc",
         "score": 8.42, "metadata": {"source": "01_thu_viec.md", "chunk_index": 5}},
        {"content": "Điều 90. Tiền lương là số tiền trả cho người lao động theo thỏa thuận",
         "score": 5.10, "metadata": {"source": "02_tien_luong.md", "chunk_index": 1}},
    ]

    print("RRF fuse dense + sparse:")
    for i, r in enumerate(rerank_rrf([dense, sparse], top_k=4,
                                     list_names=["dense", "sparse"]), 1):
        print(f"  {i}. rrf={r['score']:.5f}  ranks={r['ranks']}  "
              f"dense_score={r.get('dense_score')}  {r['content'][:55]}...")

    print("\nBẫy: top-1 RRF luôn ≈ 1/(60+1) =", round(1 / 61, 5),
          "→ không dùng điểm này so với ngưỡng fallback ở Task 9.")
