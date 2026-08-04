# Báo Cáo Nhóm — Đề Tài 1: Trợ Lý Hỏi Đáp Luật Lao Động Cho Người Trẻ

## 1. Thông Tin Nhóm

| STT | Họ và tên | MSSV | Vai trò |
|---|---|---|---|
| 1 | Lương Đức Thắng | 2A202601196 | Role 1 — Team Leader & RAG Architect (Nhóm trưởng) |
| 2 | Lương Trí Tuệ | 2A202601919 | Role 2 — Data Engineering & Scraping Dev |
| 3 | Phùng Đình Đạt | 2A202601540 | Role 3 — Vector Database & Dense Search Dev |
| 4 | Nguyễn Hà Bách | 2A202601592 | Role 4 — Sparse Retrieval & Fallback Dev |
| 5 | Hoàng Thái Dương | 2A202601518 | Role 5 — Frontend UI & App Integration Dev |
| 6 | Nguyễn Hoàng Vũ | 2A202601941 | Role 6 — Evaluation & Benchmark QA Dev |

## 2. Đề Tài Đã Chọn

**Đề Tài 1** (theo `SUGGESTED_TOPICS.md`): Trợ lý AI tra cứu và giải đáp các vấn đề pháp lý lao động
phổ biến cho Gen Z — thử việc, làm thêm giờ (OT), nghỉ phép, hợp đồng học việc, sa thải.

**Nguồn dữ liệu:** Bộ luật Lao động 2019, các Nghị định hướng dẫn thi hành (145/2020/NĐ-CP,
12/2022/NĐ-CP), hợp đồng lao động mẫu, bài viết giải đáp pháp luật lao động.

## 3. Phân Công Công Việc Chi Tiết

Chia nhỏ các công đoạn dữ liệu và kiểm thử chuyên sâu theo pipeline RAG (Task 1–10):

### Role 1 — Team Leader & RAG Architect (Lương Đức Thắng)
- Quản lý tiến độ nhóm, chốt cấu hình dùng chung (embedding model, chunk size, LLM model...)
- Xây dựng **Task 9** (Retrieval Pipeline hoàn chỉnh — kiến trúc Supervisor + fallback logic)
- Điều phối thuyết trình demo, viết README mô tả kiến trúc hệ thống

### Role 2 — Data Engineering & Scraping Dev (Lương Trí Tuệ)
- **Task 1**: Thu thập văn bản pháp lý (Bộ luật Lao động, Nghị định hướng dẫn)
- **Task 2**: Crawl bài viết hướng dẫn/giải đáp pháp luật lao động
- **Task 3**: Convert toàn bộ tài liệu sang Markdown

### Role 3 — Vector Database & Dense Search Dev (Phùng Đình Đạt)
- **Task 4**: Chunking (theo cấu trúc Điều/Khoản cho văn bản luật) & Indexing vào ChromaDB
- **Task 5**: Semantic Search & HyDE

### Role 4 — Sparse Retrieval & Fallback Dev (Nguyễn Hà Bách)
- **Task 6**: Lexical Search (BM25 / TF-IDF)
- **Task 7**: RRF Reranking
- **Task 8**: PageIndex Vectorless Fallback

### Role 5 — Frontend UI & App Integration Dev (Hoàng Thái Dương)
- Thiết kế giao diện Streamlit Chatbot (`app.py`)
- **Task 10**: Generation có Citation

### Role 6 — Evaluation & Benchmark QA Dev (Nguyễn Hoàng Vũ)
- Xây dựng Golden Dataset mở rộng (≥20 câu hỏi luật lao động)
- Chạy RAGAS benchmark & viết báo cáo `group_project/evaluation/results.md`

## 4. Tài Liệu Tham Khảo

- Kế hoạch làm việc song song, interface contract giữa các module, cấu hình dùng chung, timeline:
  xem [`description.md`](description.md)
- Hướng dẫn kỹ thuật chi tiết Task 1–10 và tiêu chí chấm điểm: xem [`README.md`](README.md)
