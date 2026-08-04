"""
Luật Đi Làm — Trợ Lý Hỏi Đáp Luật Lao Động Cho Người Trẻ (Gen Z)
Streamlit Main Application Entrypoint.

Chạy:
    streamlit run app.py
"""

import os
import sys
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# Thêm Root directory vào Python Path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from models.chat import ChatMessage, Conversation, ResponseMode, RiskLevel
from services.chat_service import answer_question, stream_answer
from ui.components import (
    render_chat_message_item,
    render_disclaimer,
    render_header,
    render_risk_warning,
    render_sidebar,
    render_welcome_screen,
)
from ui.styles import get_custom_css

# =============================================================================
# PAGE CONFIGURATION
# =============================================================================

st.set_page_config(
    page_title="Luật Đi Làm — Trợ lý Luật Lao Động Gen Z",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# SESSION STATE INITIALIZATION
# =============================================================================

def init_session_state():
    if "conversations" not in st.session_state:
        # Initial default conversation
        default_conv = Conversation(
            id=str(uuid.uuid4()),
            title="Cuộc trò chuyện mới",
            created_at=datetime.now(),
            messages=[]
        )
        st.session_state.conversations = [default_conv]
        st.session_state.active_conv_id = default_conv.id

    if "active_conv_id" not in st.session_state or not st.session_state.active_conv_id:
        if st.session_state.conversations:
            st.session_state.active_conv_id = st.session_state.conversations[0].id

    if "response_mode" not in st.session_state:
        st.session_state.response_mode = ResponseMode.QUICK.value

    if "dark_mode" not in st.session_state:
        st.session_state.dark_mode = True

    if "pending_query" not in st.session_state:
        st.session_state.pending_query = None


init_session_state()

# =============================================================================
# CUSTOM CSS INJECTION
# =============================================================================

st.markdown(get_custom_css(dark_mode=st.session_state.dark_mode), unsafe_allow_html=True)

# =============================================================================
# CONVERSATION STATE HANDLERS
# =============================================================================

def get_active_conversation() -> Conversation:
    for conv in st.session_state.conversations:
        if conv.id == st.session_state.active_conv_id:
            return conv
    # Fallback if active conv not found
    if st.session_state.conversations:
        st.session_state.active_conv_id = st.session_state.conversations[0].id
        return st.session_state.conversations[0]
    # Create new
    new_conv = Conversation(id=str(uuid.uuid4()), title="Cuộc trò chuyện mới", messages=[])
    st.session_state.conversations.append(new_conv)
    st.session_state.active_conv_id = new_conv.id
    return new_conv


def handle_new_conversation():
    new_id = str(uuid.uuid4())
    new_conv = Conversation(
        id=new_id,
        title="Cuộc trò chuyện mới",
        created_at=datetime.now(),
        messages=[]
    )
    st.session_state.conversations.insert(0, new_conv)
    st.session_state.active_conv_id = new_id
    st.session_state.pending_query = None


def handle_select_conversation(conv_id: str):
    st.session_state.active_conv_id = conv_id
    st.session_state.pending_query = None


def handle_rename_conversation(conv_id: str, new_title: str):
    for conv in st.session_state.conversations:
        if conv.id == conv_id:
            conv.title = new_title.strip() or "Cuộc trò chuyện"
            break


def handle_delete_conversation(conv_id: str):
    st.session_state.conversations = [c for c in st.session_state.conversations if c.id != conv_id]
    if not st.session_state.conversations:
        handle_new_conversation()
    else:
        st.session_state.active_conv_id = st.session_state.conversations[0].id


def handle_toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode


def handle_change_mode(new_mode: str):
    st.session_state.response_mode = new_mode


def handle_clear_current_chat():
    active_conv = get_active_conversation()
    active_conv.messages = []
    active_conv.title = "Cuộc trò chuyện mới"
    st.session_state.pending_query = None
    st.rerun()


def handle_message_feedback(msg_id: str, fb_type: str):
    active_conv = get_active_conversation()
    for msg in active_conv.messages:
        if msg.id == msg_id:
            msg.feedback = fb_type
            st.toast(f"Cảm ơn phản hồi của bạn ({'Hữu ích' if fb_type == 'helpful' else 'Cần cải thiện'})!", icon="✨")
            break

# =============================================================================
# RENDER SIDEBAR & HEADER
# =============================================================================

render_sidebar(
    conversations=st.session_state.conversations,
    active_conv_id=st.session_state.active_conv_id,
    on_select_conv=handle_select_conversation,
    on_new_conv=handle_new_conversation,
    on_rename_conv=handle_rename_conversation,
    on_delete_conv=handle_delete_conversation,
    dark_mode=st.session_state.dark_mode,
    on_toggle_theme=handle_toggle_theme
)

render_header(
    response_mode=st.session_state.response_mode,
    on_change_mode=handle_change_mode,
    on_clear_chat=handle_clear_current_chat
)

active_conv = get_active_conversation()

# =============================================================================
# MAIN CHAT AREA OR WELCOME SCREEN
# =============================================================================

if not active_conv.messages:
    # Màn hình chào khi chưa có tin nhắn
    render_welcome_screen(on_select_suggestion=lambda q: setattr(st.session_state, "pending_query", q))
else:
    # Max risk level in current chat
    max_risk = RiskLevel.NORMAL
    for msg in active_conv.messages:
        if msg.risk_level == RiskLevel.URGENT:
            max_risk = RiskLevel.URGENT
            break
        elif msg.risk_level == RiskLevel.IMPORTANT and max_risk != RiskLevel.URGENT:
            max_risk = RiskLevel.IMPORTANT

    if max_risk != RiskLevel.NORMAL:
        render_risk_warning(max_risk)

    # Render tin nhắn trong lịch sử
    for msg in active_conv.messages:
        render_chat_message_item(
            msg_id=msg.id,
            role=msg.role,
            content=msg.content,
            timestamp=msg.timestamp,
            sources=msg.sources,
            suggested_questions=msg.suggested_questions,
            feedback=msg.feedback,
            on_feedback=handle_message_feedback,
            on_select_suggested=lambda q: setattr(st.session_state, "pending_query", q)
        )

# =============================================================================
# QUERY INPUT & PROCESSING
# =============================================================================

# File upload component
uploaded_files = st.file_uploader(
    "Đính kèm Hợp đồng / Tài liệu liên quan (PDF, DOCX, TXT, PNG, JPG):",
    type=["pdf", "docx", "txt", "png", "jpg", "jpeg"],
    accept_multiple_files=True,
    help="Hệ thống sẽ bảo mật dữ liệu và phân tích điều khoản hợp đồng của bạn."
)

chat_input_val = st.chat_input("Kể mình nghe vấn đề bạn đang gặp ở chỗ làm...")
query = chat_input_val or st.session_state.pending_query

if query:
    st.session_state.pending_query = None

    # Tự động đặt tên cuộc trò chuyện từ câu hỏi đầu tiên
    if not active_conv.messages or active_conv.title == "Cuộc trò chuyện mới":
        active_conv.title = query[:30] + ("..." if len(query) > 30 else "")

    # Append User message
    user_msg_id = str(uuid.uuid4())
    user_msg = ChatMessage(
        id=user_msg_id,
        role="user",
        content=query,
        timestamp=datetime.now().strftime("%H:%M")
    )
    active_conv.messages.append(user_msg)

    # Render User message immediately
    render_chat_message_item(
        msg_id=user_msg.id,
        role="user",
        content=query,
        timestamp=user_msg.timestamp
    )

    # Attach file info if uploaded
    file_note = ""
    if uploaded_files:
        filenames = [f.name for f in uploaded_files]
        file_note = f"\n\n📎 *Đã đính kèm {len(uploaded_files)} tệp:* `{', '.join(filenames)}`"

    # Call Service Adapter
    history_dicts = [{"role": m.role, "content": m.content} for m in active_conv.messages]
    
    with st.spinner("🔍 Đang tra cứu Bộ luật Lao động & tổng hợp câu trả lời..."):
        res = answer_question(
            question=query,
            chat_history=history_dicts,
            response_mode=st.session_state.response_mode,
            top_k=st.session_state.get("top_k", 5)
        )

    full_answer = res["answer"] + file_note
    sources = res["sources"]
    risk_level = res["risk_level"]
    suggested_q = res["suggested_questions"]

    # Stream Assistant message
    assistant_msg_id = str(uuid.uuid4())
    asst_timestamp = datetime.now().strftime("%H:%M")

    # Render assistant message wrapper and stream answer
    with st.container():
        st.markdown(f"""
        <div class="chat-row-assistant">
            <div class="chat-bubble-assistant">
                <div style="font-size: 0.78rem; font-weight: 700; color: #c084fc; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                    <span style="display: flex; align-items: center; gap: 6px;">⚖️ <span>Trợ lý Luật Lao Động</span></span>
                    <span style="color: #94a3b8; font-weight: 500;">{asst_timestamp}</span>
                </div>
                <div>
        """, unsafe_allow_html=True)

        st.write_stream(stream_answer(full_answer))

        st.markdown("</div></div></div>", unsafe_allow_html=True)

    # Save Assistant message to history
    asst_msg = ChatMessage(
        id=assistant_msg_id,
        role="assistant",
        content=full_answer,
        timestamp=asst_timestamp,
        sources=sources,
        risk_level=risk_level,
        suggested_questions=suggested_q
    )
    active_conv.messages.append(asst_msg)
    active_conv.updated_at = datetime.now()

    st.rerun()

# =============================================================================
# FOOTER & HELPER DISCLAIMS
# =============================================================================

st.caption("💡 *Enter để gửi • Shift + Enter để xuống dòng*")
render_disclaimer()
