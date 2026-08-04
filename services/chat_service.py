"""
Chat Service Adapter connecting UI to RAG pipeline or fallback mock service.
"""

import os
import re
from typing import Dict, List
from models.chat import LegalSource, ResponseMode, RiskLevel
from services.mock_service import get_mock_response, mock_stream_response

# Từ khóa kích hoạt cảnh báo rủi ro cao (Urgent Risk Keywords)
URGENT_KEYWORDS = [
    "sa thải", "đuổi việc", "quấy rối", "đánh đập", "hành hung", "cưỡng ép",
    "giữ bằng gốc", "tịch thu", "nợ lương kéo dài", "tai nạn lao động", "bắt đền",
    "bạo lực", "đe dọa", "phạt tiền", "trừ lương"
]


def detect_risk_level(query: str) -> RiskLevel:
    """Analyze query content to determine if it involves high-risk labor disputes or emergency."""
    query_lower = query.lower()
    urgent_matches = [kw for kw in URGENT_KEYWORDS if kw in query_lower]
    if len(urgent_matches) >= 2 or any(kw in query_lower for kw in ["đánh đập", "quấy rối", "hành hung", "giữ bằng"]):
        return RiskLevel.URGENT
    elif len(urgent_matches) >= 1:
        return RiskLevel.IMPORTANT
    return RiskLevel.NORMAL


def answer_question(
    question: str,
    chat_history: list[dict],
    response_mode: str = "quick",
    top_k: int = 5
) -> dict:
    """
    Core Service API mapping user query to RAG Pipeline or fallback mock adapter.

    Returns:
    {
        "answer": str,
        "sources": List[LegalSource],
        "risk_level": RiskLevel,
        "suggested_questions": List[str]
    }
    """
    risk_level = detect_risk_level(question)

    try:
        # Check if RAG Task 10 generation can be called
        from src.task10_generation import generate_with_citation
        
        # Call Task 10 generation
        rag_res = generate_with_citation(question, top_k=top_k)
        answer_text = rag_res.get("answer", "")
        raw_sources = rag_res.get("sources", [])

        sources = []
        for src in raw_sources:
            meta = src.get("metadata", {})
            sources.append(LegalSource(
                title=meta.get("source", "Bộ luật Lao động 2019"),
                article=meta.get("article", "Văn bản liên quan"),
                effective_date=meta.get("effective_date", "01/01/2021"),
                url=meta.get("url", None),
                content_snippet=src.get("content", "")[:250],
                score=src.get("score", 0.0)
            ))

        return {
            "answer": answer_text,
            "sources": sources,
            "risk_level": risk_level,
            "suggested_questions": [
                "Tôi nên làm gì tiếp theo?",
                "Có được khiếu nại lên Thanh tra Lao động không?",
                "Thời hạn giải quyết tranh chấp là bao lâu?"
            ]
        }

    except (ImportError, NotImplementedError, Exception) as e:
        # Fallback to realistic mock service when RAG pipeline is not configured or fails
        mock_data = get_mock_response(question)
        
        # Override risk level if detected keywords are higher priority
        final_risk = risk_level if risk_level != RiskLevel.NORMAL else mock_data.get("risk_level", RiskLevel.NORMAL)

        # Modify structure according to response_mode
        answer_text = mock_data["answer"]
        if response_mode == ResponseMode.QUICK.value:
            # Extract first 2 sections
            parts = answer_text.split("---")
            if len(parts) >= 2:
                answer_text = "---".join(parts[:2])
        elif response_mode == ResponseMode.AUDIT.value:
            answer_text = "🛡️ **[KIỂM TRA QUYỀN LỢI NGHỀ NGHIỆP]**\n\n" + answer_text

        return {
            "answer": answer_text,
            "sources": mock_data["sources"],
            "risk_level": final_risk,
            "suggested_questions": mock_data["suggested_questions"]
        }


def stream_answer(answer_text: str, delay: float = 0.015):
    """Utility helper for Streamlit st.write_stream."""
    return mock_stream_response(answer_text, delay=delay)
