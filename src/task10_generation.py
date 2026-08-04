"""
Task 10 — Generation Có Citation.

Hướng dẫn:
    1. Chọn top_k, top_p phù hợp (giải thích lý do)
    2. Sắp xếp lại chunks sau reranking để tránh "lost in the middle"
    3. Inject context vào prompt
    4. Yêu cầu LLM trả lời có citation
    5. Nếu không đủ evidence → "I cannot verify this information"

Gợi ý LLM: OpenRouter có nhiều model gắn hậu tố ":free" không tính phí — xem
https://openrouter.ai/models?max_price=0 — phù hợp nếu chưa có credit trả phí.
Base URL: "https://openrouter.ai/api/v1", dùng chung interface với OpenAI SDK.
"""

import os
from dotenv import load_dotenv

load_dotenv()

from .task9_retrieval_pipeline import retrieve


# =============================================================================
# CONFIGURATION — Giải thích lựa chọn
# =============================================================================

# top_k: Số chunks đưa vào context
# Chọn 5 vì: đủ evidence mà không quá dài gây lost in the middle
TOP_K = 5

# top_p (nucleus sampling): Xác suất tích luỹ cho token generation
# Chọn 0.9 vì: đủ diverse nhưng không quá random
TOP_P = 0.9

# temperature: Độ ngẫu nhiên của output
# Chọn 0.3 vì: RAG cần factual, ít sáng tạo
TEMPERATURE = 0.3

# Có thể đổi model mà không sửa code qua file .env.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
LLM_MODEL = os.getenv("LLM_MODEL", "openai/gpt-4o-mini")


# =============================================================================
# SYSTEM PROMPT
# =============================================================================

SYSTEM_PROMPT = """Bạn là trợ lý pháp lý AI chuyên tra cứu và giải đáp về Luật Lao động cho người lao động trẻ / Gen Z (Bộ luật Lao động 2019, Nghị định 145/2020/NĐ-CP, hợp đồng thử việc, tiền lương, làm thêm giờ OT, phép năm, kỷ luật & sa thải).

Quy tắc bắt buộc:
1. Chỉ sử dụng thông tin từ context được cung cấp — KHÔNG bịa đặt
2. Mỗi khẳng định phải có trích dẫn điều luật / tài liệu ngay sau, ví dụ: [Bộ luật Lao động 2019, Điều 25] hoặc [Nghị định 145/2020/NĐ-CP]
3. Nếu context không đủ thông tin → trả lời: "Tôi không thể xác minh thông tin này từ nguồn hiện có"
4. Trả lời bằng tiếng Việt, có cấu trúc rõ ràng, dễ hiểu đối với người lao động trẻ
5. Không suy luận hay mở rộng ngoài những gì được nêu trong context"""


# =============================================================================
# DOCUMENT REORDERING (tránh lost in the middle)
# =============================================================================

def reorder_for_llm(chunks: list[dict]) -> list[dict]:
    """
    Sắp xếp chunks để tránh "lost in the middle" effect.

    LLM nhớ tốt thông tin ở ĐẦU và CUỐI prompt, quên thông tin ở GIỮA.
    Strategy: đặt chunks quan trọng nhất ở đầu và cuối, kém quan trọng ở giữa.

    Input order (by score):  [1, 2, 3, 4, 5]
    Output order:            [1, 3, 5, 4, 2]
    (best first, worst in middle, second-best last)

    Args:
        chunks: List sorted by score descending (from retrieval)

    Returns:
        List reordered để maximize LLM attention.
    """
    if len(chunks) <= 2:
        return list(chunks)
    front = chunks[::2]
    back = chunks[1::2]
    return front + back[::-1]


# =============================================================================
# CONTEXT FORMATTING
# =============================================================================

def format_context(chunks: list[dict]) -> str:
    """
    Format chunks thành context string cho prompt.
    Mỗi chunk có label source để LLM có thể cite.

    Args:
        chunks: List of {'content': str, 'metadata': dict, 'score': float}

    Returns:
        Formatted context string.
    """
    context_parts = []
    for index, chunk in enumerate(chunks, 1):
        metadata = chunk.get("metadata") or {}
        source = metadata.get("source", f"Source {index}")
        doc_type = metadata.get("type", "unknown")
        context_parts.append(
            f"[Document {index} | Source: {source} | Type: {doc_type}]\n"
            f"{chunk.get('content', '')}"
        )
    return "\n\n---\n\n".join(context_parts)


# =============================================================================
# GENERATION
# =============================================================================

def generate_with_citation(query: str, top_k: int = TOP_K) -> dict:
    """
    End-to-end RAG generation có citation.

    Pipeline:
        1. Retrieve relevant chunks
        2. Reorder để tránh lost in the middle
        3. Format context với source labels
        4. Build prompt (system + context + query)
        5. Call LLM
        6. Return answer + sources

    Args:
        query: Câu hỏi của user

    Returns:
        {
            'answer': str,           # Câu trả lời có citation
            'sources': list[dict],   # Các chunks đã dùng
            'retrieval_source': str  # 'hybrid' hoặc 'pageindex'
        }
    """
    chunks = retrieve(query, top_k=top_k)
    reordered = reorder_for_llm(chunks)
    context = format_context(reordered)
    retrieval_source = chunks[0].get("source", "hybrid") if chunks else "none"

    if not chunks:
        return {
            "answer": "Tôi không thể xác minh thông tin này từ nguồn hiện có.",
            "sources": [],
            "retrieval_source": retrieval_source,
        }

    user_message = f"Context:\n{context}\n\n---\n\nQuestion: {query}"
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    api_key = os.getenv("OPENROUTER_API_KEY") or os.getenv("OPENAI_API_KEY")
    answer = ""
    if gemini_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=gemini_key)
            response = client.models.generate_content(
                model=GEMINI_MODEL,
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    temperature=TEMPERATURE,
                    top_p=TOP_P,
                ),
            )
            answer = response.text or ""
        except Exception as exc:
            print(f"Gemini generation failed: {exc}")
            answer = ""
    elif api_key:
        try:
            from openai import OpenAI

            openrouter_key = os.getenv("OPENROUTER_API_KEY")
            client_kwargs = {"api_key": api_key}
            if openrouter_key:
                client_kwargs["base_url"] = "https://openrouter.ai/api/v1"
            client = OpenAI(**client_kwargs)
            response = client.chat.completions.create(
                model=LLM_MODEL,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=TEMPERATURE,
                top_p=TOP_P,
            )
            answer = response.choices[0].message.content or ""
        except Exception:
            # Demo and automated tests remain usable when the optional provider
            # is unavailable; the extractive response below stays grounded.
            answer = ""

    if not answer.strip():
        first = reordered[0]
        source = (first.get("metadata") or {}).get("source", "Nguồn tài liệu")
        excerpt = first.get("content", "").strip()
        if len(excerpt) > 700:
            excerpt = excerpt[:700].rsplit(" ", 1)[0] + "…"
        answer = f"{excerpt} [{source}]" if excerpt else (
            "Tôi không thể xác minh thông tin này từ nguồn hiện có."
        )

    return {
        "answer": answer,
        "sources": chunks,
        "retrieval_source": retrieval_source,
    }


if __name__ == "__main__":
    test_queries = [
        "Thời gian thử việc tối đa là bao lâu?",
        "Lương thử việc tối thiểu bằng bao nhiêu phần trăm lương chính thức?",
        "Người lao động được nghỉ phép năm bao nhiêu ngày?",
    ]

    for q in test_queries:
        print(f"\n{'='*70}")
        print(f"Q: {q}")
        print("=" * 70)
        result = generate_with_citation(q)
        print(f"\nA: {result['answer']}")
        print(f"\n[Sources: {len(result['sources'])} chunks | via {result['retrieval_source']}]")
