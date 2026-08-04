"""
Data models for Luật Đi Làm Streamlit Application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ResponseMode(str, Enum):
    QUICK = "quick"         # ⚡ Giải thích nhanh
    DETAILED = "detailed"   # 📊 Phân tích chi tiết
    AUDIT = "audit"         # 🛡️ Kiểm tra quyền lợi


class RiskLevel(str, Enum):
    NORMAL = "normal"       # Bình thường
    IMPORTANT = "important" # Quan trọng (cần chú ý)
    URGENT = "urgent"       # Khẩn cấp (tranh chấp/sa thải/vi phạm nghiêm trọng)


@dataclass
class LegalSource:
    title: str               # Tên văn bản (e.g. Bộ luật Lao động 2019)
    article: str             # Điều/Khoản liên quan (e.g. Điều 25, Khoản 1)
    effective_date: str      # Ngày hiệu lực hoặc phiên bản
    url: Optional[str] = None
    content_snippet: Optional[str] = None
    score: float = 0.0


@dataclass
class ChatMessage:
    id: str
    role: str                # 'user' | 'assistant'
    content: str
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M"))
    sources: List[LegalSource] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.NORMAL
    suggested_questions: List[str] = field(default_factory=list)
    feedback: Optional[str] = None  # 'helpful' | 'unhelpful' | None


@dataclass
class Conversation:
    id: str
    title: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    messages: List[ChatMessage] = field(default_factory=list)
