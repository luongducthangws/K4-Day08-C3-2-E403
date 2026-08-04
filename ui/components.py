"""
Modular UI Components for Luật Đi Làm Streamlit Application.
"""

from datetime import datetime, timedelta
from typing import Callable, List, Optional

import streamlit as st
from models.chat import Conversation, LegalSource, ResponseMode, RiskLevel


def render_sidebar_brand():
    """Render Logo & Brand Name in Sidebar."""
    st.markdown("""
    <div class="sidebar-brand">
        <div class="brand-icon">⚖️💬</div>
        <div>
            <h2 class="brand-title">Luật Đi Làm</h2>
            <p class="brand-tagline">Hiểu luật dễ hơn — đi làm tự tin hơn</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


def group_conversations(conversations: List[Conversation]) -> dict:
    """Group conversations into Today, Last 7 Days, and Older."""
    now = datetime.now()
    today_start = datetime(now.year, now.month, now.day)
    seven_days_ago = today_start - timedelta(days=7)

    grouped = {
        "Hôm nay": [],
        "7 ngày gần đây": [],
        "Cũ hơn": []
    }

    for conv in conversations:
        if conv.created_at >= today_start:
            grouped["Hôm nay"].append(conv)
        elif conv.created_at >= seven_days_ago:
            grouped["7 ngày gần đây"].append(conv)
        else:
            grouped["Cũ hơn"].append(conv)

    return grouped


def render_sidebar(
    conversations: List[Conversation],
    active_conv_id: str,
    on_select_conv: Callable[[str], None],
    on_new_conv: Callable[[], None],
    on_rename_conv: Callable[[str, str], None],
    on_delete_conv: Callable[[str], None],
    dark_mode: bool,
    on_toggle_theme: Callable[[], None]
):
    """Render complete Left Sidebar according to design specifications."""
    with st.sidebar:
        render_sidebar_brand()

        # Nút nổi bật: + Cuộc trò chuyện mới
        if st.button("➕ Cuộc trò chuyện mới", use_container_width=True, type="primary"):
            on_new_conv()

        st.markdown("<div style='margin-top: 12px;'></div>", unsafe_allow_html=True)

        # Ô tìm kiếm lịch sử hội thoại
        search_query = st.text_input("🔍 Tìm lịch sử...", value="", placeholder="Gõ từ khóa tìm kiếm...")

        st.divider()

        # Lọc danh sách trò chuyện theo search_query
        filtered_convs = conversations
        if search_query.strip():
            sq = search_query.strip().lower()
            filtered_convs = [c for c in conversations if sq in c.title.lower()]

        # Nhóm lịch sử trò chuyện
        grouped = group_conversations(filtered_convs)

        has_any = False
        for group_name, conv_list in grouped.items():
            if conv_list:
                has_any = True
                st.caption(f"**{group_name}**")
                for conv in conv_list:
                    is_active = (conv.id == active_conv_id)
                    button_label = f"{'💬 ' if is_active else '📄 '}{conv.title[:24]}" + ("..." if len(conv.title) > 24 else "")
                    
                    col_btn, col_menu = st.columns([0.82, 0.18])
                    with col_btn:
                        if st.button(
                            button_label,
                            key=f"conv_btn_{conv.id}",
                            use_container_width=True,
                            type="secondary" if not is_active else "primary"
                        ):
                            on_select_conv(conv.id)
                    
                    with col_menu:
                        with st.popover("⋮", use_container_width=True):
                            st.markdown(f"**Quản lý cuộc trò chuyện**")
                            new_name = st.text_input("Đổi tên", value=conv.title, key=f"rename_in_{conv.id}")
                            if st.button("💾 Lưu tên mới", key=f"save_rename_{conv.id}", use_container_width=True):
                                on_rename_conv(conv.id, new_name)
                                st.rerun()
                            if st.button("🗑️ Xóa", key=f"del_conv_{conv.id}", use_container_width=True):
                                on_delete_conv(conv.id)
                                st.rerun()

        if not has_any:
            st.caption("*(Chưa có cuộc trò chuyện nào)*")

        st.divider()

        st.subheader("⚙️ Cấu hình RAG & Retrieval")
        top_k_val = st.slider(
            "Số chunks retrieval (top_k)",
            min_value=1,
            max_value=10,
            value=st.session_state.get("top_k", 5),
            key="top_k_slider"
        )
        st.session_state["top_k"] = top_k_val

        use_reranking_val = st.toggle(
            "Bật RRF Reranker",
            value=st.session_state.get("use_reranking", True),
            key="use_rerank_toggle"
        )
        st.session_state["use_reranking"] = use_reranking_val

        use_pageindex_val = st.toggle(
            "Bật PageIndex Fallback",
            value=st.session_state.get("use_pageindex", True),
            key="use_pageindex_toggle"
        )
        st.session_state["use_pageindex"] = use_pageindex_val

        st.divider()

        # Sidebar Footer: Kho kiến thức, Giới thiệu & Switch Dark/Light Mode
        with st.expander("📚 Kho kiến thức & Nguồn luật"):
            st.markdown("""
            - **Bộ luật Lao động 2019** (Luật số 45/2019/QH14)
            - **Nghị định 145/2020/NĐ-CP** (Hướng dẫn BLLĐ)
            - **Nghị định 12/2022/NĐ-CP** (Xử phạt vi phạm)
            - **Thông tư 16/2025/TT-BNV**
            """)

        with st.expander("ℹ️ Giới thiệu"):
            st.markdown("""
            **Luật Đi Làm** là trợ lý AI thông minh giúp thế hệ trẻ (Gen Z) nắm vững quyền và nghĩa vụ lao động tại Việt Nam bằng ngôn ngữ trực quan, dễ hiểu và trích dẫn chuẩn xác.
            """)

        st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
        theme_label = "🌙 Dark Mode (Tối)" if dark_mode else "☀️ Light Mode (Sáng)"
        if st.button(theme_label, use_container_width=True):
            on_toggle_theme()


def render_header(
    response_mode: str,
    on_change_mode: Callable[[str], None],
    on_clear_chat: Callable[[], None]
):
    """Render App Header Bar with Active Assistant Status & Mode Selector."""
    st.markdown("""
    <div class="app-header">
        <div class="header-title-box">
            <span style="font-size: 1.6rem;">⚖️</span>
            <div>
                <h3 style="margin: 0; font-size: 1.15rem; font-weight: 800; display: flex; align-items: center; gap: 8px;">
                    Trợ lý Luật Lao Động <span class="status-dot" title="Đang hoạt động"></span>
                </h3>
                <p style="margin: 0; font-size: 0.8rem; color: #94a3b8;">Trực tuyến 24/7 • Tra cứu theo Bộ luật Lao động 2019</p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_mode, col_clear = st.columns([0.78, 0.22])
    with col_mode:
        selected_mode = st.radio(
            "Chế độ trả lời:",
            options=[ResponseMode.QUICK.value, ResponseMode.DETAILED.value, ResponseMode.AUDIT.value],
            format_func=lambda x: {
                ResponseMode.QUICK.value: "⚡ Giải thích nhanh",
                ResponseMode.DETAILED.value: "📊 Phân tích chi tiết",
                ResponseMode.AUDIT.value: "🛡️ Kiểm tra quyền lợi"
            }[x],
            index=[ResponseMode.QUICK.value, ResponseMode.DETAILED.value, ResponseMode.AUDIT.value].index(response_mode),
            horizontal=True,
            label_visibility="collapsed"
        )
        if selected_mode != response_mode:
            on_change_mode(selected_mode)

    with col_clear:
        if st.button("🗑️ Xóa cuộc trò chuyện", use_container_width=True):
            on_clear_chat()


def render_welcome_screen(on_select_suggestion: Callable[[str], None]):
    """Render Welcome Hero Screen with 6 interactive suggestion cards when chat is empty."""
    st.markdown("""
    <div class="welcome-hero">
        <div class="welcome-avatar">⚖️</div>
        <h1 class="welcome-title">Hôm nay bạn gặp chuyện gì ở chỗ làm?</h1>
        <p class="welcome-subtitle">
            Hỏi về hợp đồng, thử việc, lương, tăng ca, nghỉ phép hoặc nghỉ việc. Mình sẽ giải thích theo cách dễ hiểu và dẫn nguồn để bạn kiểm tra.
        </p>
    </div>
    """, unsafe_allow_html=True)

    suggestions = [
        "Thử việc 2 tháng có đúng luật không?",
        "Công ty giữ bằng gốc của mình có được không?",
        "Nghỉ việc có cần báo trước 30 ngày?",
        "Làm thêm cuối tuần được tính lương thế nào?",
        "Không ký hợp đồng thì có được đóng BHXH không?",
        "Bị công ty nợ lương thì phải làm gì?"
    ]

    col1, col2 = st.columns(2)
    for idx, sug in enumerate(suggestions):
        target_col = col1 if idx % 2 == 0 else col2
        with target_col:
            if st.button(f"👉 {sug}", key=f"welcome_sug_{idx}", use_container_width=True):
                on_select_suggestion(sug)


def render_sources_section(sources: List[LegalSource]):
    """Render expandable legal reference sources with chips and details."""
    if not sources:
        return

    with st.expander(f"📚 Căn cứ pháp lý & Nguồn trích dẫn ({len(sources)} tài liệu)"):
        for i, src in enumerate(sources, 1):
            st.markdown(f"**[{i}] {src.title}** — `{src.article}`")
            st.caption(f"🗓️ Ngày hiệu lực/Phiên bản: {src.effective_date} | Độ tương đồng: `{src.score:.2f}`")
            if src.content_snippet:
                st.info(src.content_snippet)
            if src.url:
                st.markdown(f"🔗 [Xem toàn văn trên Thư Viện Pháp Luật]({src.url})")
            if i < len(sources):
                st.divider()


def render_chat_message_item(
    msg_id: str,
    role: str,
    content: str,
    timestamp: str,
    sources: List[LegalSource] = None,
    suggested_questions: List[str] = None,
    feedback: Optional[str] = None,
    on_feedback: Callable[[str, str], None] = None,
    on_select_suggested: Callable[[str], None] = None
):
    """Render a single chat message (User aligned right, Assistant aligned left)."""
    if role == "user":
        st.markdown(f"""
        <div class="chat-row-user">
            <div class="chat-bubble-user">
                <div style="font-size: 0.76rem; font-weight: 700; color: #e9d5ff; margin-bottom: 4px; text-align: right;">
                    Bạn • {timestamp} 🧑‍💻
                </div>
                <div>{content}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div class="chat-row-assistant">
            <div class="chat-bubble-assistant">
                <div style="font-size: 0.78rem; font-weight: 700; color: #c084fc; margin-bottom: 10px; display: flex; align-items: center; justify-content: space-between;">
                    <span style="display: flex; align-items: center; gap: 6px;">⚖️ <span>Trợ lý Luật Lao Động</span></span>
                    <span style="color: #94a3b8; font-weight: 500;">{timestamp}</span>
                </div>
                <div>
        """, unsafe_allow_html=True)

        st.markdown(content)

        st.markdown("</div></div></div>", unsafe_allow_html=True)

        # Render legal sources expander if available
        if sources:
            render_sources_section(sources)

        # Render action bar & suggested follow-up questions
        col_act, col_sug = st.columns([0.4, 0.6])
        with col_act:
            btn_h_type = "primary" if feedback == "helpful" else "secondary"
            btn_u_type = "primary" if feedback == "unhelpful" else "secondary"
            
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("👍 Useful", key=f"fb_h_{msg_id}", type=btn_h_type, help="Câu trả lời hữu ích"):
                    if on_feedback: on_feedback(msg_id, "helpful")
            with c2:
                if st.button("👎 Issue", key=f"fb_u_{msg_id}", type=btn_u_type, help="Cần chính xác hơn"):
                    if on_feedback: on_feedback(msg_id, "unhelpful")
            with c3:
                if st.button("📋 Copy", key=f"cp_{msg_id}", help="Sao chép câu trả lời"):
                    st.toast("Đã sao chép nội dung vào bộ nhớ tạm!", icon="📋")

        if suggested_questions:
            st.caption("💡 **Câu hỏi tiếp theo gợi ý:**")
            cols = st.columns(len(suggested_questions))
            for idx, sq in enumerate(suggested_questions):
                with cols[idx % len(cols)]:
                    if st.button(f"❓ {sq}", key=f"sq_{msg_id}_{idx}", use_container_width=True):
                        if on_select_suggested: on_select_suggested(sq)


def render_risk_warning(risk_level: RiskLevel):
    """Render prominent warning card when user query indicates high-risk disputes or wrongful termination."""
    if risk_level == RiskLevel.URGENT:
        st.markdown("""
        <div class="risk-urgent-card">
            <h4 style="margin: 0 0 8px 0; font-size: 1.1rem; display: flex; align-items: center; gap: 8px; color: #fef2f2;">
                🚨 CẢNH BÁO: TRƯỜNG HỢP CÓ DẤU HIỆU VI PHẠM PHÁP LUẬT NGHÊM TRỌNG
            </h4>
            <p style="margin: 0 0 12px 0; font-size: 0.92rem; line-height: 1.5; color: #fee2e2;">
                Vấn đề của bạn có dấu hiệu tranh chấp lao động nghiêm trọng, sa thải trái pháp luật, quấy rối hoặc cưỡng ép. Thông tin AI chỉ mang tính tham khảo và không thể thay thế hỗ trợ pháp lý trực tiếp.
            </p>
            <p style="margin: 0; font-size: 0.9rem; font-weight: 700; color: #ffffff;">
                📢 Đề xuất liên hệ hỗ trợ khẩn cấp:
            </p>
            <ul style="margin: 6px 0 0 0; padding-left: 20px; font-size: 0.88rem; color: #fef2f2;">
                <li><b>Công đoàn cơ sở / Công đoàn cấp quận/huyện</b> nơi bạn làm việc.</li>
                <li><b>Thanh tra Sở Lao động - Thương binh và Xã hội</b> địa phương.</li>
                <li><b>Trung tâm Trợ giúp Pháp lý Nhà nước</b> hoặc Luật sư chuyên môn.</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
    elif risk_level == RiskLevel.IMPORTANT:
        st.markdown("""
        <div class="risk-important-card">
            <h5 style="margin: 0 0 6px 0; font-size: 1rem; color: #fffbeb;">
                ⚠️ LƯU Ý QUAN TRỌNG VỀ QUYỀN LỢI LAO ĐỘNG
            </h5>
            <p style="margin: 0; font-size: 0.88rem; color: #fef3c7;">
                Bạn nên lưu lại toàn bộ bằng chứng (Email, tin nhắn Zalo, Hợp đồng, Phiếu lương) trước khi làm việc hoặc nộp đơn khiếu nại với công ty.
            </p>
        </div>
        """, unsafe_allow_html=True)


def render_disclaimer():
    """Render footer disclaimer."""
    st.markdown("""
    <div class="disclaimer-text">
        ⚖️ <i>Thông tin do Trợ lý AI cung cấp chỉ mang tính tham khảo, không thay thế tư vấn chính thức của Luật sư hoặc Cơ quan quản lý nhà nước có thẩm quyền.</i>
    </div>
    """, unsafe_allow_html=True)
