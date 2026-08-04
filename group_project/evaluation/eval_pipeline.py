"""
RAG Evaluation Pipeline.

Sử dụng DeepEval / RAGAS / TruLens để đánh giá chất lượng RAG pipeline.
Chọn 1 framework và implement đầy đủ.

Yêu cầu:
    1. Load golden_dataset.json (≥15 Q&A pairs)
    2. Chạy RAG pipeline trên từng question
    3. Evaluate với 4 metrics: faithfulness, relevance, context_recall, context_precision
    4. So sánh A/B ít nhất 2 configs
    5. Export results ra results.md

Lưu ý rate limit nếu dùng model OpenRouter ":free": RAGAS/DeepEval gọi LLM RẤT NHIỀU LẦN
(không phải 1 lần/câu hỏi mà nhiều lần/metric/câu hỏi). Model free của OpenRouter giới hạn
50 request/ngày CHO CẢ TÀI KHOẢN (không phải theo model hay theo API key — đổi model free
khác hay tạo key mới KHÔNG reset quota). Nếu chạy full 15+ câu hỏi mà bị rate limit giữa
chừng, thử giảm xuống subset 5 câu để chạy kịp trong buổi, hoặc nạp $10 credit để mở khóa
1000 request/ngày.
"""

import json
import os
from pathlib import Path

GOLDEN_DATASET_PATH = Path(__file__).parent / "golden_dataset.json"
RESULTS_PATH = Path(__file__).parent / "results.md"

FPT_BASE_URL = "https://mkp-api.fptcloud.com"
FPT_LLM_MODEL = "GLM-5.2"


def load_golden_dataset() -> list[dict]:
    """Load golden dataset từ JSON file."""
    with open(GOLDEN_DATASET_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# Option 1: DeepEval
# =============================================================================

def evaluate_with_deepeval(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng DeepEval.

    pip install deepeval
    """
    # TODO: Implement
    #
    # from deepeval import evaluate
    # from deepeval.metrics import (
    #     FaithfulnessMetric,
    #     AnswerRelevancyMetric,
    #     ContextualRecallMetric,
    #     ContextualPrecisionMetric,
    # )
    # from deepeval.test_case import LLMTestCase
    #
    # test_cases = []
    # for item in golden_dataset:
    #     result = rag_pipeline.generate_with_citation(item["question"])
    #     test_case = LLMTestCase(
    #         input=item["question"],
    #         actual_output=result["answer"],
    #         expected_output=item["expected_answer"],
    #         retrieval_context=[c["content"] for c in result["sources"]],
    #     )
    #     test_cases.append(test_case)
    #
    # metrics = [
    #     FaithfulnessMetric(threshold=0.7),
    #     AnswerRelevancyMetric(threshold=0.7),
    #     ContextualRecallMetric(threshold=0.7),
    #     ContextualPrecisionMetric(threshold=0.7),
    # ]
    #
    # results = evaluate(test_cases, metrics)
    # return results
    raise NotImplementedError("Implement evaluate_with_deepeval")


# =============================================================================
# Option 2: RAGAS
# =============================================================================

def _extract_citation(expected_context: str) -> str | None:
    """Return the 'Điều N' article reference from expected_context, if any."""
    import re

    match = re.search(r"Điều\s+\d+", expected_context)
    return match.group(0) if match else None


def evaluate_retrieval_hit_rate(golden_dataset: list[dict], top_k: int = 5) -> dict:
    """Deterministic, LLM-free retrieval quality: does the retrieved context
    actually contain the golden citation ('Điều N')? No LLM judge involved, so
    this is immune to the RAGAS/API 422 failures and cheap to run on the full
    dataset (only embedding + BM25 calls, no chat completions).

    Only questions whose expected_context names a 'Điều N' of Bộ luật Lao động
    2019 are scored — the other questions cite documents (Luật BHXH 2014,
    Thông tư 10/2020/TT-BLĐTBXH) that were never collected into this corpus,
    so no retriever could ever find them; scoring those would just measure a
    golden-dataset gap, not retrieval quality.
    """
    from src.task5_semantic_search import semantic_search
    from src.task9_retrieval_pipeline import retrieve

    configs = {"hybrid_rerank": retrieve, "dense_only": semantic_search}
    scored = [
        (item["question"], citation)
        for item in golden_dataset
        if (citation := _extract_citation(item["expected_context"]))
    ]

    summary = {}
    for config_name, search_fn in configs.items():
        hits_at_1 = hits_at_k = 0
        reciprocal_ranks = []
        for question, citation in scored:
            results = search_fn(question, top_k=top_k)
            rank = next(
                (i for i, r in enumerate(results, 1) if citation in r["content"]),
                None,
            )
            reciprocal_ranks.append(1 / rank if rank else 0.0)
            hits_at_k += rank is not None
            hits_at_1 += rank == 1
        n = len(scored)
        summary[config_name] = {
            "n": n,
            "top_k": top_k,
            "hit_rate_at_1": hits_at_1 / n,
            "hit_rate_at_k": hits_at_k / n,
            "mrr": sum(reciprocal_ranks) / n,
        }
    summary["skipped_out_of_corpus"] = len(golden_dataset) - len(scored)
    return summary


def _ragas_llm_and_embeddings():
    """RAGAS mặc định cần OPENAI_API_KEY thật. Nhóm dùng hạ tầng FPT AI
    Marketplace (OpenAI-compatible) nên bơm llm/embeddings riêng khi có
    FPT_API_KEY, thay vì để RAGAS tự gọi OpenAI mặc định."""
    if not os.getenv("FPT_API_KEY"):
        return None, None
    from langchain_openai import ChatOpenAI, OpenAIEmbeddings

    llm = ChatOpenAI(
        model=FPT_LLM_MODEL,
        openai_api_key=os.environ["FPT_API_KEY"],
        openai_api_base=FPT_BASE_URL,
        temperature=0,
    )
    embeddings = OpenAIEmbeddings(
        model=os.getenv("FPT_EMBEDDING_MODEL", "Vietnamese_Embedding"),
        openai_api_key=os.environ["FPT_API_KEY"],
        openai_api_base=FPT_BASE_URL,
    )
    return llm, embeddings


def evaluate_with_ragas(rag_pipeline, golden_dataset: list[dict], subset_size: int = 5):
    """Evaluate RAG pipeline sử dụng RAGAS."""
    from ragas import evaluate
    from ragas.metrics import (
        faithfulness,
        answer_relevancy,
        context_recall,
        context_precision,
    )
    from datasets import Dataset

    # Chuẩn bị dữ liệu đầu vào cho RAGAS
    eval_data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    # Do giới hạn Rate Limit của tài khoản free (nếu dùng OpenRouter free)
    # Bạn nên test thử trước với subset 3-5 câu hỏi trước khi chạy toàn bộ 15-20 câu.
    subset = golden_dataset[:subset_size]

    for item in subset:
        # Gọi RAG pipeline của bạn
        result = rag_pipeline(item["question"])

        eval_data["question"].append(item["question"])
        eval_data["answer"].append(result["answer"])
        # Định dạng contexts là list of strings
        eval_data["contexts"].append([c["content"] for c in result["sources"]])
        eval_data["ground_truth"].append(item["expected_answer"])

    dataset = Dataset.from_dict(eval_data)

    llm, embeddings = _ragas_llm_and_embeddings()

    # Tiến hành đánh giá
    result = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
        llm=llm,
        embeddings=embeddings,
    )

    # Trả về kết quả
    return result


# =============================================================================
# Option 3: TruLens
# =============================================================================

def evaluate_with_trulens(rag_pipeline, golden_dataset: list[dict]) -> dict:
    """
    Evaluate RAG pipeline sử dụng TruLens.

    pip install trulens
    """
    # TODO: Implement
    #
    # from trulens.apps.custom import TruCustomApp
    # from trulens.core import Feedback
    # from trulens.providers.openai import OpenAI as TruOpenAI
    #
    # provider = TruOpenAI()
    #
    # f_faithfulness = Feedback(provider.groundedness_measure_with_cot_reasons).on_output()
    # f_relevance = Feedback(provider.relevance).on_input_output()
    # f_context_relevance = Feedback(provider.context_relevance).on_input()
    #
    # tru_rag = TruCustomApp(
    #     rag_pipeline,
    #     app_name="EcommerceSupport_RAG",
    #     feedbacks=[f_faithfulness, f_relevance, f_context_relevance],
    # )
    #
    # with tru_rag as recording:
    #     for item in golden_dataset:
    #         rag_pipeline.generate_with_citation(item["question"])
    #
    # # Dashboard: from trulens.dashboard import run_dashboard; run_dashboard()
    raise NotImplementedError("Implement evaluate_with_trulens")


# =============================================================================
# A/B Comparison
# =============================================================================

def compare_configs(rag_pipeline, golden_dataset: list[dict]):
    """
    So sánh A/B giữa ít nhất 2 configs.

    Gợi ý configs để so sánh:
    - Config A: hybrid search + reranking
    - Config B: dense-only (không reranking)
    - Config C: hybrid search + PageIndex fallback
    """
    from unittest.mock import patch

    from src import task10_generation as task10
    from src.task5_semantic_search import semantic_search

    def _dense_only_retrieve(query: str, top_k: int = 5, **_kwargs) -> list[dict]:
        results = semantic_search(query, top_k=top_k)
        for item in results:
            item["source"] = "hybrid"
        return results

    def _dense_only_pipeline(question: str) -> dict:
        with patch.object(task10, "retrieve", _dense_only_retrieve):
            return task10.generate_with_citation(question)

    configs = {
        "hybrid_rerank": rag_pipeline,
        "dense_only": _dense_only_pipeline,
    }

    results = {}
    for config_name, pipeline in configs.items():
        results[config_name] = evaluate_with_ragas(pipeline, golden_dataset)
    return results


# =============================================================================
# Export Results
# =============================================================================

METRICS = ["faithfulness", "answer_relevancy", "context_recall", "context_precision"]
METRIC_LABELS = {
    "faithfulness": "Faithfulness",
    "answer_relevancy": "Answer Relevance",
    "context_recall": "Context Recall",
    "context_precision": "Context Precision",
}


def _fmt(value) -> str:
    return "N/A" if value is None or value != value else f"{value:.3f}"


def _average(row: dict) -> float:
    scores = [row[m] for m in METRICS if row.get(m) == row.get(m)]
    return sum(scores) / len(scores) if scores else 0.0


def export_results(comparison: dict, retrieval_hit_rate: dict | None = None):
    """Export A/B RAGAS evaluation results (hybrid_rerank vs dense_only) to results.md."""
    config_a = comparison["hybrid_rerank"]
    config_b = comparison["dense_only"]

    content = "# RAG Evaluation Results\n\n"
    content += "## Framework sử dụng\n\nRAGAS (0.1.21) — LLM/embeddings qua FPT AI Marketplace.\n\n---\n\n"

    if retrieval_hit_rate is not None:
        rr_a = retrieval_hit_rate["hybrid_rerank"]
        rr_b = retrieval_hit_rate["dense_only"]
        content += (
            f"## Retrieval Hit-Rate (citation-based, không cần LLM, n={rr_a['n']} câu "
            f"có trích dẫn 'Điều N' trong Bộ luật Lao động 2019)\n\n"
        )
        content += "| Metric | Config A (hybrid + rerank) | Config B (dense-only) |\n"
        content += "|--------|---------------------------|----------------------|\n"
        content += f"| Hit Rate@1 | {rr_a['hit_rate_at_1']:.3f} | {rr_b['hit_rate_at_1']:.3f} |\n"
        content += f"| Hit Rate@{rr_a['top_k']} | {rr_a['hit_rate_at_k']:.3f} | {rr_b['hit_rate_at_k']:.3f} |\n"
        content += f"| MRR | {rr_a['mrr']:.3f} | {rr_b['mrr']:.3f} |\n\n"
        if retrieval_hit_rate.get("skipped_out_of_corpus"):
            content += (
                f"> {retrieval_hit_rate['skipped_out_of_corpus']} câu hỏi trong golden dataset trích dẫn "
                "văn bản không có trong corpus đã thu thập (vd. Luật Bảo hiểm xã hội 2014, "
                "Thông tư 10/2020/TT-BLĐTBXH) nên bị loại khỏi phép đo này — không retriever nào "
                "có thể tìm thấy bằng chứng không tồn tại trong dữ liệu.\n\n"
            )
        content += "---\n\n"

    content += "## Overall Scores (RAGAS, LLM-judged)\n\n"
    content += "| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |\n"
    content += "|--------|---------------------------|----------------------|---|\n"
    avg_a_values, avg_b_values = [], []
    for metric in METRICS:
        a_val, b_val = config_a[metric], config_b[metric]
        if a_val == a_val:  # exclude NaN (failed metric, e.g. API error)
            avg_a_values.append(a_val)
        if b_val == b_val:
            avg_b_values.append(b_val)
        delta = a_val - b_val
        content += f"| {METRIC_LABELS[metric]} | {_fmt(a_val)} | {_fmt(b_val)} | {delta:+.3f} |\n"
    avg_a = sum(avg_a_values) / len(avg_a_values) if avg_a_values else float("nan")
    avg_b = sum(avg_b_values) / len(avg_b_values) if avg_b_values else float("nan")
    content += f"| **Average** | **{_fmt(avg_a)}** | **{_fmt(avg_b)}** | **{avg_a - avg_b:+.3f}** |\n\n---\n\n"

    winner = "Config A (hybrid + rerank)" if avg_a >= avg_b else "Config B (dense-only)"
    content += "## A/B Comparison Analysis\n\n"
    content += "**Config A:** hybrid search (semantic + BM25 lexical, merge bằng RRF) + rerank.\n\n"
    content += "**Config B:** chỉ semantic search (dense-only), không lexical, không rerank.\n\n"
    content += (
        f"**Kết luận:** {winner} có điểm trung bình cao hơn "
        f"({max(avg_a, avg_b):.3f} so với {min(avg_a, avg_b):.3f}). "
        "Chênh lệch lớn nhất nằm ở metric có Δ tuyệt đối cao nhất trong bảng trên "
        "— cho thấy phần đóng góp chính của lexical search + rerank tới chất lượng retrieval.\n\n---\n\n"
    )

    df_a = config_a.to_pandas()
    df_a["avg_score"] = df_a.apply(lambda row: _average(row.to_dict()), axis=1)
    worst = df_a.sort_values("avg_score").head(3)
    content += "## Worst Performers (Bottom 3, Config A)\n\n"
    content += "| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |\n"
    content += "|---|----------|-------------|-----------|--------|---------------|------------|\n"
    for rank, (_, row) in enumerate(worst.iterrows(), 1):
        weakest_metric = min(METRICS, key=lambda m: row[m] if row[m] == row[m] else 1.0)
        stage = "Retrieval" if weakest_metric in ("context_recall", "context_precision") else "Generation"
        question = str(row["question"])[:60]
        content += (
            f"| {rank} | {question} | {_fmt(row['faithfulness'])} | {_fmt(row['answer_relevancy'])} | "
            f"{_fmt(row['context_recall'])} | {stage} | Điểm {METRIC_LABELS[weakest_metric]} thấp nhất |\n"
        )
    content += "\n---\n\n"

    content += "## Recommendations\n\n"
    content += (
        "### Cải tiến 1\n**Action:** Calibrate lại `SCORE_THRESHOLD` trong "
        "`task9_retrieval_pipeline.py` bằng điểm cosine thật đo trên câu hỏi liên quan/lạc đề.\n"
        "**Expected impact:** Fallback PageIndex kích hoạt đúng lúc hơn, tăng Context Recall.\n\n"
    )
    content += (
        "### Cải tiến 2\n**Action:** Tăng `top_k` khi retrieval trả context_precision thấp "
        "cho câu hỏi nhiều Điều/Khoản liên quan.\n"
        "**Expected impact:** Tăng Context Recall, đổi lại Context Precision có thể giảm nhẹ.\n\n"
    )
    content += (
        "### Cải tiến 3\n**Action:** Với các câu Faithfulness thấp, siết prompt "
        "(`SYSTEM_PROMPT` trong `task10_generation.py`) yêu cầu trích dẫn Điều/Khoản cụ thể hơn.\n"
        "**Expected impact:** Giảm câu trả lời suy diễn ngoài context, tăng Faithfulness.\n"
    )

    if any(config[m] != config[m] for config in (config_a, config_b) for m in METRICS):
        content += (
            "\n---\n\n> **Ghi chú:** một số giá trị `N/A` do RAGAS gặp lỗi API "
            "(vd. `422 Unprocessable Entity` từ FPT AI Marketplace khi tính "
            "Answer Relevance) — không phải do pipeline retrieval/generation.\n"
        )

    RESULTS_PATH.write_text(content, encoding="utf-8")
    print(f"Results written to {RESULTS_PATH.name}")


if __name__ == "__main__":
    import sys

    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from src.task10_generation import generate_with_citation

    golden_dataset = load_golden_dataset()
    print(f"Loaded {len(golden_dataset)} test cases")

    retrieval_hit_rate = evaluate_retrieval_hit_rate(golden_dataset)
    comparison = compare_configs(generate_with_citation, golden_dataset)
    export_results(comparison, retrieval_hit_rate)
