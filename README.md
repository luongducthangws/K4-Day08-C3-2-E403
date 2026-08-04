# ⚖️💬 Luật Đi Làm — Trợ Lý Hỏi Đáp Luật Lao Động Cho Người Trẻ (Gen Z)

> **"Hiểu luật dễ hơn — đi làm tự tin hơn."**

Ứng dụng Chatbot RAG trợ giúp người lao động trẻ / Gen Z tra cứu quyền và nghĩa vụ lao động tại Việt Nam theo **Bộ luật Lao động 2019**, **Nghị định 145/2020/NĐ-CP** với giao diện **Material You Dark Mode** hiện đại, thân thiện và linh hoạt.

---

## ✨ Tính năng nổi bật

- **🎨 Thiết kế Material You Dark Mode**: Giao diện tối sang trọng, bo góc mềm mại, thiết kế responsive trên cả Desktop và Mobile.
- **💬 Căn lề tin nhắn trực quan**: Câu hỏi người dùng bên phải (Lề Phải), phản hồi AI trợ lý bên trái (Lề Trái).
- **🗂️ Quản lý Đa cuộc trò chuyện (Multi-session Chat)**:
  - Tự động đặt tên cuộc trò chuyện từ câu hỏi đầu tiên.
  - Phân nhóm lịch sử: *Hôm nay*, *7 ngày gần đây*, *Cũ hơn*.
  - Đổi tên và Xóa cuộc trò chuyện linh hoạt.
- **⚡ 3 Chế độ phản hồi tùy chỉnh**:
  - `⚡ Giải thích nhanh`: Tóm tắt 2 phần trọng tâm.
  - `📊 Phân tích chi tiết`: Cung cấp cấu trúc 4 phần chuẩn mực.
  - `🛡️ Kiểm tra quyền lợi`: Đánh giá rủi ro pháp lý theo hợp đồng.
- **🚨 Cảnh báo Rủi ro cao & Tranh chấp khẩn cấp**: Tự động phát hiện trường hợp nợ lương, sa thải trái pháp luật, giữ bằng gốc hoặc cưỡng ép lao động để hiển thị thẻ cảnh báo và thông tin liên hệ Công đoàn/Thanh tra Lao động/Luật sư.
- **📚 Trích dẫn Căn cứ pháp lý chuẩn xác**: Thẻ nguồn hiển thị tên văn bản, điều khoản, ngày hiệu lực và liên kết tra cứu chính thức.
- **📎 Hỗ trợ đính kèm Hợp đồng/Tài liệu**: Tải lên tệp PDF, DOCX, TXT hoặc ảnh hợp đồng.
- **🌗 Tùy chỉnh Giao diện Sáng / Tối (Light & Dark Mode)**.

---

## 🛠️ Cấu trúc Mã nguồn (Modular Architecture)

```
K4-Day08-C3-2-E403/
├── streamlit_app.py         # Entrypoint khởi chạy chính của ứng dụng
├── models/
│   └── chat.py              # Data models (ChatMessage, LegalSource, Conversation)
├── services/
│   ├── chat_service.py      # Adapter kết nối UI với RAG Pipeline / Risk detection
│   └── mock_service.py      # Bộ sinh phản hồi mô phỏng thực tế khi offline
├── ui/
│   ├── styles.py            # CSS Custom & Material You Design Tokens
│   └── components.py        # Các component UI (Sidebar, Header, Welcome, Chat, Cards)
├── .streamlit/
│   └── config.toml          # Cấu hình theme Streamlit
├── requirements.txt         # Danh sách thư viện phụ thuộc
└── README.md                # Hướng dẫn cài đặt và sử dụng
```

---

## 🚀 Hướng dẫn Cài đặt & Khởi chạy

### 1. Khởi tạo môi trường Python (Python >= 3.10)

```bash
# Tạo môi trường ảo
python3 -m venv .venv

# Kích hoạt môi trường ảo
# Trên macOS / Linux:
source .venv/bin/activate

# Trên Windows:
# .venv\Scripts\activate
```

### 2. Cài đặt Dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình File Môi trường `.env` (Tùy chọn cho RAG Online)

Tạo file `.env` tại thư mục gốc dự án:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
# Hoặc
OPENAI_API_KEY=your_openai_api_key_here
```

*(Nếu chưa nhập API Key, ứng dụng sẽ tự động chạy ở chế độ Offline Mock Service với dữ liệu minh họa thực tế mà không bị lỗi).*

### 4. Khởi chạy Ứng dụng Streamlit

```bash
streamlit run app.py
```

Ứng dụng sẽ tự động mở tại địa chỉ: **[http://localhost:8501](http://localhost:8501)**

---

## ⚖️ Disclaimer (Miễn trừ trách nhiệm)

*Thông tin do Trợ lý AI cung cấp chỉ mang tính tham khảo, không thay thế tư vấn pháp lý chính thức từ Luật sư hoặc Cơ quan quản lý nhà nước có thẩm quyền.*
