# Description — Đề Tài 1: Trợ Lý Hỏi Đáp Luật Lao Động Cho Người Trẻ

> Tài liệu điều phối cho cả nhóm. Đọc hết 1 lần trước khi bắt đầu code — mục tiêu là để 6 người
> làm **song song** mà không giẫm chân nhau, và ghép lại (integrate) không bị vỡ vì sai format dữ liệu.

---

## 1. Đề tài & phạm vi dữ liệu

Nhóm chọn **Đề tài 1** trong `SUGGESTED_TOPICS.md`: trợ lý AI tra cứu/giải đáp pháp lý lao động phổ
biến cho Gen Z (thử việc, OT, nghỉ phép, hợp đồng học việc, sa thải...).

Codebase gốc (`src/task*.py`, `app.py`) được viết mẫu theo chủ đề "E-commerce Shopee" — đó chỉ là
**ví dụ minh hoạ**, không phải yêu cầu bắt buộc. Domain thật của nhóm là **luật lao động**, nên khi
code, mọi docstring/prompt/sample query mẫu có nhắc "Shopee/thanh toán/đổi trả" cần được viết lại
theo domain lao động (chi tiết ở mục việc từng role bên dưới). Bộ test chấm điểm
(`tests/test_individual.py`) **không kiểm tra nội dung domain**, chỉ kiểm tra format/số lượng file
→ đổi đề tài không ảnh hưởng tới cách chấm.

**Nguồn dữ liệu gợi ý (Task 1 — văn bản pháp lý, PDF):**
- Bộ luật Lao động 2019 (số 45/2019/QH14)
- Nghị định 145/2020/NĐ-CP (hướng dẫn thi hành một số điều của Bộ luật Lao động)
- Nghị định 12/2022/NĐ-CP (xử phạt vi phạm hành chính trong lĩnh vực lao động)
- Thông tư/hợp đồng lao động mẫu (Bộ LĐTBXH hoặc mẫu hợp đồng thử việc công khai)
- Tải PDF chính thức từ [thuvienphapluat.vn](https://thuvienphapluat.vn) hoặc cổng thông tin Bộ LĐTBXH

**Nguồn dữ liệu gợi ý (Task 2 — crawl bài viết, tối thiểu 5 bài):**
- Bài giải đáp về: thời gian & lương thử việc, tính lương OT/tăng ca, nghỉ phép năm, hợp đồng thời
  vụ/học việc, quy trình sa thải/chấm dứt HĐLĐ đúng luật, trợ cấp thôi việc
- Nguồn: chuyên mục hỏi-đáp pháp luật lao động trên thuvienphapluat.vn, blog nhân sự (TopCV,
  Glints), hoặc báo chính thống (chỉ dùng nguồn công khai, không cần đăng nhập)

**Câu hỏi truy vấn mẫu** (dùng để test end-to-end và làm golden dataset — Task 6/Role 6):
- "Thời gian thử việc tối đa cho vị trí lập trình viên là bao lâu và lương thử việc tối thiểu bằng
  bao nhiêu % lương chính thức?"
- "Công ty sa thải tôi qua tin nhắn Zalo mà không báo trước 30 ngày thì có đúng luật không?"
- "Làm thêm giờ (OT) vào ngày lễ được trả lương gấp bao nhiêu lần?"
- "Người lao động thử việc có được hưởng phép năm không?"

> Lưu ý field `customer_role` trong docstring Task 1 (kế thừa từ template e-commerce) — với domain
> lao động, đổi thành `stakeholder: "employee" | "employer" | "both"` để giữ được tính năng lọc theo
> đối tượng (metadata filter) khi viết câu hỏi benchmark.

---

## 2. Nguyên tắc để làm SONG SONG được (đọc kỹ mục này)

Pipeline có phụ thuộc tuần tự tự nhiên: `Task1,2 → Task3 → Task4 → {Task5, Task6} → Task7 → Task9
(+Task8 độc lập) → Task10 → app.py`. Nếu chờ đúng thứ tự này, cả nhóm sẽ làm việc tuần tự chứ không
song song. Cách để phá vỡ sự phụ thuộc đó:

1. **Contract-first**: Mọi hàm giao tiếp giữa các task đều có **schema dict cố định** (mục 4). Ai
   cũng có thể code + test module của mình chỉ cần tuân theo schema đầu vào/đầu ra, **không cần chờ
   người khác code xong** — miễn là dùng dữ liệu giả (mock) đúng schema.
2. **Dữ liệu mẫu để mọi người bắt đầu ngay** (mục 5): Role 2 tạo 2-3 file `.md` mẫu trong
   `data/standardized/` **ngay trong buổi đầu tiên** (không cần đợi crawl xong hết), để Role 3/4 có
   dữ liệu thật index/test trong lúc Role 2 tiếp tục thu thập đủ số lượng.
3. **Chốt cấu hình dùng chung TRƯỚC khi code** (mục 3) — đây là nguyên nhân xung đột phổ biến nhất
   khi làm song song (đổi embedding model giữa chừng → phải xoá `chroma_db/` và mọi người code lại).
4. **Mỗi người chỉ sửa file mình sở hữu** (mục 4, cột "File sở hữu") + file test riêng của mình. Khi
   cần sửa file chung (`app.py`, `README.md`, `.env.example`) thì báo trước trong nhóm chat.
5. **Nhánh git riêng theo role, PR nhỏ, merge thường xuyên** (mục 7) — tránh 1 nhánh khổng lồ merge
   cuối cùng gây conflict hàng loạt.

---

## 3. Cấu hình dùng chung — CẢ NHÓM CHỐT TRƯỚC KHI CODE (Checkpoint 0, ~15 phút đầu)

Họp nhanh đầu tiên (video call/voice) để chốt các giá trị sau, ghi lại vào `.env` chung và Slack/Zalo
group — **đừng để mỗi người tự chọn khác nhau**, vì Task 4/5/9/10 dùng chung các giá trị này:

| Cấu hình | Giá trị đề xuất | Ảnh hưởng nếu đổi sau |
|---|---|---|
| `EMBEDDING_PROVIDER` | `sentence_transformers` (local, không cần API key — khuyến nghị cho nhóm học) | Đổi → phải xoá `chroma_db/` và reindex lại (dimension khác nhau) |
| `EMBEDDING_MODEL` | `BAAI/bge-m3` (multilingual, tốt tiếng Việt) | Ảnh hưởng Task 4 & 5 |
| `COLLECTION_NAME` (Task 4) | `labor_law_docs` | Đổi tên collection thì Task 5 phải sửa theo |
| Chunking | **Hybrid theo loại tài liệu**: `legal_structure` (chunk theo `Điều N.`, chẻ tiếp theo Khoản nếu Điều > `CHUNK_SIZE`) cho `data/standardized/legal/`; `RecursiveCharacterTextSplitter` cho `data/standardized/news/`. `CHUNK_SIZE=800`, `overlap=50` | Ảnh hưởng chất lượng retrieval **và độ chính xác trích dẫn** — xem lý do bên dưới |
| Rerank method (Task 7/9) | `rrf` (không cần API key) | Nếu đổi sang cross-encoder cần `JINA_API_KEY` |
| `LLM_MODEL` (Task 10) | 1 model `:free` trên OpenRouter (xem `openrouter.ai/models?max_price=0`) | Đổi model có thể đổi giọng văn câu trả lời |
| `SCORE_THRESHOLD` (Task 9) | Để mặc định `0.3`, **Role 4 tự calibrate lại** bằng dữ liệu luật lao động thật (xem ghi chú trong `task9_retrieval_pipeline.py`) | Threshold cũ tính trên corpus Shopee — không dùng nguyên |

Ai phụ trách Task 4 (Role 3) là người **khởi tạo** các giá trị này trong code; người khác **đọc lại
từ `.env`/import từ `task4_chunking_indexing.py`**, không tự định nghĩa giá trị riêng.

**Vì sao chunk theo Điều/Khoản thay vì recursive thuần cho văn bản luật?** Task 10 yêu cầu trích dẫn
dạng `[Điều 25, Bộ luật Lao động 2019]`. Recursive splitter cắt theo số ký tự cố định, không biết
ranh giới Điều — dễ cắt đôi 1 Điều giữa 2 chunk khác nhau, khiến trích dẫn sai/mơ hồ và giảm độ chính
xác retrieval (1 câu trả lời đúng có thể nằm vắt qua 2 chunk). SemanticChunker cũng không cần thiết
ở đây vì luật đã có ranh giới cấu trúc rõ (Điều/Khoản) sẵn — dùng embedding để đoán lại ranh giới đã
biết trước là lãng phí. `RecursiveCharacterTextSplitter` vẫn cần dùng làm fallback cho
`data/standardized/news/` (bài viết crawl, prose tự do, không có cấu trúc Điều/Khoản). Xem code mẫu
hybrid trong `src/task4_chunking_indexing.py::chunk_documents()`.

---

## 4. Phân công vai trò (theo `report_nhom.md`)

| Role | Thành viên | Nhiệm vụ | File sở hữu | Deliverable | Phụ thuộc vào |
|---|---|---|---|---|---|
| **1 — Team Leader & RAG Architect** | Lương Đức Thắng | Quản lý tiến độ, chốt cấu hình chung (mục 3), code **Task 9** (ghép retrieval pipeline), viết `README.md`/kiến trúc, điều phối demo | `src/task9_retrieval_pipeline.py`, `group_project/README.md` | Pipeline `retrieve()` chạy end-to-end + kiến trúc hệ thống trong README | Task 5, 6, 7, 8 (nhưng có thể code sớm bằng mock — mục 5) |
| **2 — Data Engineering & Scraping Dev** | Lương Trí Tuệ | Task 1 (tải PDF luật lao động) + Task 2 (crawl bài viết) + Task 3 (convert Markdown) | `src/task1_collect_legal_docs.py`, `src/task2_crawl_news.py`, `src/task3_convert_markdown.py` | ≥3 PDF trong `data/landing/legal/`, ≥5 bài JSON trong `data/landing/news/`, toàn bộ convert sang `.md` trong `data/standardized/` | Không phụ thuộc ai — **làm trước, mở khoá cho cả nhóm** |
| **3 — Vector Database & Dense Search Dev** | Phùng Đình Đạt | Task 4 (Chunking & ChromaDB Indexing) + Task 5 (Semantic Search & HyDE) | `src/task4_chunking_indexing.py`, `src/task5_semantic_search.py` | Vector store index thành công + `semantic_search()` trả kết quả đúng schema | Task 3 (dùng mock trong lúc chờ — mục 5) |
| **4 — Sparse Retrieval & Fallback Dev** | Nguyễn Hà Bách | Task 6 (BM25/TF-IDF) + Task 7 (RRF Reranking) + Task 8 (PageIndex Fallback) | `src/task6_lexical_search.py`, `src/task7_reranking.py`, `src/task8_pageindex_vectorless.py` | `lexical_search()`, `rerank()`/`rerank_rrf()`, `pageindex_search()` đúng schema | Task 3 (dùng mock — mục 5); Task 8 hoàn toàn độc lập, có thể làm ngay từ đầu |
| **5 — Frontend UI & App Integration Dev** | Hoàng Thái Dương | Thiết kế Streamlit Chatbot `app.py` (đổi branding/sample questions sang luật lao động) + Task 10 (Citation Generation) | `app.py`, `src/task10_generation.py` | Chatbot chạy được, có citation, hiển thị nguồn | Task 9 (dùng mock response `{"answer","sources","retrieval_source"}` để code UI song song) |
| **6 — Evaluation & Benchmark QA Dev** | Nguyễn Hoàng Vũ | Xây `golden_dataset.json` (≥15-20 câu hỏi luật lao động) + chạy RAGAS benchmark + viết `results.md` | `group_project/evaluation/golden_dataset.json`, `group_project/evaluation/eval_pipeline.py`, `group_project/evaluation/results.md` | Bảng điểm 4 metrics (Faithfulness, Answer Relevance, Context Recall/Precision) + so sánh A/B ≥2 config | Có thể viết câu hỏi + expected_answer **ngay từ đầu** (không cần pipeline chạy), chỉ cần chạy eval cuối cùng khi Task 10 xong |

**Ai có thể bắt đầu ngay hôm nay không cần chờ ai:** Role 1 (chốt config + viết khung Task 9 theo
mock), Role 2 (không phụ thuộc gì), Role 4/Task 8 (PageIndex độc lập hoàn toàn), Role 6 (viết câu
hỏi + đáp án mẫu bằng kiến thức luật lao động, không cần chờ code).

---

## 5. Interface Contracts — schema cố định giữa các module

Đây là phần quan trọng nhất để làm song song: **tuân thủ đúng các dict key dưới đây**, dù bạn code
trước hay sau người khác, khi ghép lại sẽ chạy được ngay.

```python
# ---- Sau Task 3: 1 document đã convert markdown ----
# data/standardized/{legal,news}/*.md — file thô, chưa có schema Python

# ---- Task 4.load_documents() ----
{"content": str, "metadata": {"source": str, "type": "legal" | "news", "stakeholder": "employee" | "employer" | "both"}}

# ---- Task 4.chunk_documents() — mỗi chunk ----
{"content": str, "metadata": {**doc_metadata, "chunk_index": int | str}}
# Nếu type == "legal": metadata có thêm "dieu_number": str (vd. "25") để Task 10 trích dẫn
# đúng dạng "[Điều 25, <source>]" thay vì chỉ trích dẫn theo tên file.

# ---- Task 4.embed_chunks() — thêm 1 key vào chunk ----
{..., "embedding": list[float]}

# ---- Task 5.semantic_search() / Task 6.lexical_search() / Task 7.rerank*() / Task 8.pageindex_search() ----
# TẤT CẢ trả về cùng 1 schema, sort theo score giảm dần:
{"content": str, "score": float, "metadata": dict}
# Task 8 (pageindex) và Task 9 (retrieve) BẮT BUỘC có thêm:
{..., "source": "hybrid" | "pageindex"}

# ---- Task 9.retrieve() ----
list[dict]  # đúng schema trên, đã merge + rerank + fallback, độ dài = top_k

# ---- Task 10.generate_with_citation() ----
{"answer": str, "sources": list[dict], "retrieval_source": "hybrid" | "pageindex" | "none"}
```

**Quy ước bắt buộc:**
- `score` luôn là `float`, sort **giảm dần** (cao nhất trước) ở mọi module trả list.
- `metadata` luôn có key `source` (tên file gốc) và `type` (`legal`/`news`) — Task 10 và `app.py` cần
  2 key này để hiển thị nguồn trích dẫn.
- Không đổi tên key đã thống nhất (vd. không đổi `content` thành `text`). Nếu thực sự cần đổi, báo
  cả nhóm trước — vì ít nhất 2 người khác đang import trực tiếp từ module của bạn.

---

## 6. Dữ liệu mock để bắt đầu ngay (dùng trong lúc chờ Task 1–3 xong thật)

Role 3, 4, 5 có thể dán đoạn Python sau vào 1 file tạm (vd. `scratch_mock.py`, không commit) để có
dữ liệu giả đúng schema, test module của mình độc lập trước khi có index thật:

```python
MOCK_CHUNKS = [
    {"content": "Điều 25. Thời gian thử việc tối đa 60 ngày đối với công việc có chức danh nghề "
                 "nghiệp cần trình độ chuyên môn từ cao đẳng trở lên. Lương thử việc tối thiểu "
                 "bằng 85% lương chính thức.",
     "score": 0.91, "metadata": {"source": "bo-luat-lao-dong-2019.md", "type": "legal", "stakeholder": "both", "dieu_number": "25"}},
    {"content": "Điều 98. Làm thêm giờ vào ngày lễ, tết được trả lương ít nhất bằng 300% chưa kể "
                 "lương ngày lễ đối với người lao động hưởng lương ngày.",
     "score": 0.85, "metadata": {"source": "nghi-dinh-145-2020.md", "type": "legal", "stakeholder": "employee", "dieu_number": "98"}},
    {"content": "Khi đơn phương chấm dứt hợp đồng lao động, người sử dụng lao động phải báo "
                 "trước ít nhất 30 ngày đối với hợp đồng xác định thời hạn.",
     "score": 0.78, "metadata": {"source": "huong-dan-sa-thai-dung-luat.md", "type": "news", "stakeholder": "employer"}},
]
```

Role 1 (Task 9) và Role 5 (Task 10/`app.py`) cũng nên mock trực tiếp output của
`generate_with_citation()` để dựng UI song song mà không cần chờ LLM call thật:

```python
MOCK_GENERATION_RESPONSE = {
    "answer": "Thời gian thử việc tối đa là 60 ngày [Bộ luật Lao động 2019, Điều 25].",
    "sources": MOCK_CHUNKS,
    "retrieval_source": "hybrid",
}
```

---

## 7. Git Workflow

- **Nhánh**: `feature/task<N>-<ho-ten-ngan>` (vd. `feature/task4-dat`, `feature/task9-thang`).
- Mỗi người chỉ push vào nhánh của mình, mở **Pull Request nhỏ** vào `main` khi function chạy được
  (không cần hoàn hảo — có thể để `TODO` nhỏ và note trong PR).
- Role 1 (Team Leader) review & merge PR để tránh 2 người merge conflict cùng lúc vào `main`.
- Merge thường xuyên (không dồn đến cuối) — vì Task 9/10/app.py cần import trực tiếp từ code người
  khác, merge sớm giúp phát hiện lệch schema sớm.
- File chung dễ conflict (`README.md`, `requirements.txt`, `.env.example`) — báo trong group chat
  trước khi sửa, hoặc để Role 1 gom lại sửa 1 lần.

---

## 8. Timeline đề xuất (điều chỉnh theo lịch nhóm thực tế)

| Mốc | Nội dung | Ai xong trước |
|---|---|---|
| CP0 | Họp chốt cấu hình chung (mục 3) + tạo nhánh git cho từng người | Cả nhóm |
| CP1 | Task 1–3 xong tối thiểu 1 phần (vài file mẫu) để mở khoá cho Role 3/4 | Role 2 |
| CP2 | Task 4–8 code song song bằng data thật (khi có) hoặc mock | Role 3, Role 4 |
| CP3 | Task 9 ghép pipeline, Task 10 + `app.py` dựng UI bằng mock response | Role 1, Role 5 |
| CP4 | Golden dataset viết xong (không cần chờ pipeline) | Role 6 |
| CP5 | Tích hợp toàn bộ: `app.py` gọi pipeline thật, chạy thử end-to-end | Cả nhóm |
| CP6 | Chạy RAGAS benchmark, viết `results.md`, chuẩn bị demo | Role 6 + Role 1 |

Tham khảo thêm phân bổ thời gian chi tiết theo checkpoint trong `checkpoint_timer.html` và mục
"Hướng Dẫn Thời Gian" trong `README.md` gốc (dùng cho buổi lab cá nhân, nhóm có thể giãn ra nhiều
buổi).

---

## 9. Checklist bàn giao cuối cùng (map theo thang điểm trong `README.md`)

- [ ] Task 1–10 (`pytest tests/ -v` pass) — 50%
- [ ] `app.py` chạy, chatbot trả lời có citation, hiển thị nguồn, hỗ trợ follow-up — phần "Bài Nhóm"
- [ ] `group_project/evaluation/golden_dataset.json` ≥15 câu hỏi luật lao động
- [ ] `group_project/evaluation/eval_pipeline.py` chạy RAGAS (Faithfulness, Answer Relevancy,
      Context Recall, Context Precision)
- [ ] `group_project/evaluation/results.md` — bảng điểm + so sánh A/B (vd. có rerank vs không) +
      phân tích worst performers
- [ ] `group_project/README.md` — điền bảng "Phân Công Công Việc" + vẽ kiến trúc hệ thống
- [ ] Code push đầy đủ lên repo chung, không còn `NotImplementedError`

---

## 10. Liên lạc & đồng bộ

- Báo tiến độ trong group chat mỗi khi merge xong 1 task (kèm link PR).
- Nếu đổi bất kỳ giá trị nào trong mục 3 (cấu hình chung) sau khi đã chốt → báo ngay, vì ít nhất 2
  người khác code dựa trên giá trị cũ.
- Nếu phát hiện schema ở mục 5 không đủ dùng (thiếu key cần thiết) → thảo luận trước khi tự ý đổi,
  vì thay đổi ảnh hưởng dây chuyền tới các task phía sau.
