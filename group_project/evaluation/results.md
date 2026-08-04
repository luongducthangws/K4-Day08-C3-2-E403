# RAG Evaluation Results

## Framework sử dụng

RAGAS (0.1.21) — LLM/embeddings qua FPT AI Marketplace.

---

## Retrieval Hit-Rate (citation-based, không cần LLM, n=94/100 câu có trích dẫn "Điều N" Bộ luật Lao động 2019)

| Metric | Config A (hybrid + rerank) | Config B (dense-only) |
|--------|---------------------------|----------------------|
| Hit Rate@1 | 0.596 | 0.479 |
| Hit Rate@5 | 0.830 | 0.862 |
| MRR | 0.700 | 0.634 |

Đo bằng cách kiểm tra retrieved chunk có chứa đúng chuỗi "Điều N" trong `expected_context` của golden dataset hay không — không qua LLM judge nên không bị ảnh hưởng bởi lỗi API, chạy trên toàn bộ 94 câu (không phải subset 5 câu như bảng RAGAS bên dưới).

**Nhận xét:** hybrid+rerank xếp hạng chunk đúng lên top-1 thường xuyên hơn hẳn (0.596 vs 0.479, +0.117) và MRR cao hơn (0.700 vs 0.634) — rerank giúp đẩy đúng bằng chứng lên đầu. Ngược lại dense-only có Hit Rate@5 nhỉnh hơn một chút (0.862 vs 0.830) — tức là trong top-5 thô, dense-only đôi khi "vớt" được đúng chunk mà hybrid (sau rerank) đẩy ra ngoài top-5. Tóm lại: rerank đánh đổi một phần recall thô lấy độ chính xác thứ hạng — hợp lý cho trải nghiệm người dùng (câu trả lời dùng top-1/top-3, không dùng cả top-5).

6/100 câu hỏi trong golden dataset bị loại khỏi phép đo này vì trích dẫn văn bản không có trong corpus đã thu thập (Luật Bảo hiểm xã hội 2014, Thông tư 10/2020/TT-BLĐTBXH) — không retriever nào có thể tìm thấy bằng chứng không tồn tại trong dữ liệu; đây là khoảng trống của golden dataset/corpus, không phải lỗi retrieval.

---

## Overall Scores (RAGAS, LLM-judged, subset 5 câu)

| Metric | Config A (hybrid + rerank) | Config B (dense-only) | Δ |
|--------|---------------------------|----------------------|---|
| Faithfulness | 0.573 | 0.640 | -0.067 |
| Answer Relevance | N/A | N/A | +nan |
| Context Recall | 0.800 | 0.800 | +0.000 |
| Context Precision | 0.667 | 0.500 | +0.167 |
| **Average** | **0.680** | **0.647** | **+0.033** |

---

## A/B Comparison Analysis

**Config A:** hybrid search (semantic + BM25 lexical, merge bằng RRF) + rerank.

**Config B:** chỉ semantic search (dense-only), không lexical, không rerank.

**Kết luận:** Config A (hybrid + rerank) có điểm trung bình cao hơn (0.680 so với 0.647). Chênh lệch lớn nhất nằm ở metric có Δ tuyệt đối cao nhất trong bảng trên — cho thấy phần đóng góp chính của lexical search + rerank tới chất lượng retrieval.

---

## Worst Performers (Bottom 3, Config A)

| # | Question | Faithfulness | Relevance | Recall | Failure Stage | Root Cause |
|---|----------|-------------|-----------|--------|---------------|------------|
| 1 | Người lao động có phải báo trước khi đơn phương chấm dứt hợp | 0.200 | N/A | 0.000 | Retrieval | Điểm Context Recall thấp nhất |
| 2 | Người sử dụng lao động có được giữ bản chính giấy tờ tùy thâ | 0.500 | N/A | 1.000 | Generation | Điểm Faithfulness thấp nhất |
| 3 | Tiền lương của người lao động trong thời gian thử việc ít nh | 0.500 | N/A | 1.000 | Generation | Điểm Faithfulness thấp nhất |

---

## Recommendations

### Cải tiến 1
**Action:** Calibrate lại `SCORE_THRESHOLD` trong `task9_retrieval_pipeline.py` bằng điểm cosine thật đo trên câu hỏi liên quan/lạc đề.
**Expected impact:** Fallback PageIndex kích hoạt đúng lúc hơn, tăng Context Recall.

### Cải tiến 2
**Action:** Tăng `top_k` khi retrieval trả context_precision thấp cho câu hỏi nhiều Điều/Khoản liên quan.
**Expected impact:** Tăng Context Recall, đổi lại Context Precision có thể giảm nhẹ.

### Cải tiến 3
**Action:** Với các câu Faithfulness thấp, siết prompt (`SYSTEM_PROMPT` trong `task10_generation.py`) yêu cầu trích dẫn Điều/Khoản cụ thể hơn.
**Expected impact:** Giảm câu trả lời suy diễn ngoài context, tăng Faithfulness.

---

> **Ghi chú:** một số giá trị `N/A` do RAGAS gặp lỗi API (vd. `422 Unprocessable Entity` từ FPT AI Marketplace khi tính Answer Relevance) — không phải do pipeline retrieval/generation.
