"""
Mock service providing illustrative realistic legal responses for Gen Z labor law inquiries.
Used when RAG backend is offline or API key is not present.
"""

import time
from typing import Dict, Generator, List
from models.chat import LegalSource, RiskLevel

MOCK_DISCLAIMER_NOTE = "\n\n*(⚡ Dữ liệu minh họa từ Kho dữ liệu Bộ luật Lao động 2019)*"

MOCK_DATABASE = {
    "thử việc": {
        "answer": """### 📝 Trả lời ngắn gọn
Thời gian thử việc tối đa phụ thuộc vào trình độ chuyên môn của công việc, thường từ **60 ngày** (đối với trình độ cao đẳng, đại học trở lên) đến **30 ngày** (trình độ trung cấp, công nhân kỹ thuật). Công ty không được kéo dài quá thời gian này cho 01 công việc.

---

### 💡 Giải thích dễ hiểu
- **Trình độ Đại học / Lập trình viên / Chuyên viên**: Thử việc tối đa **60 ngày**.
- **Tiền lương thử việc**: Phải đạt ít nhất **85%** mức lương chính thức của công việc đó.
- **Quyền nghỉ việc**: Trong thời gian thử việc, cả bạn và công ty đều có quyền hủy bỏ thỏa thuận thử việc mà **không cần báo trước** và không phải bồi thường nếu việc làm thử không đạt yêu cầu.

---

### ⚖️ Căn cứ pháp lý
- **[Bộ luật Lao động 2019, Điều 25]**: Thời gian thử việc do hai bên thỏa thuận căn cứ vào tính chất và mức độ phức tạp của công việc nhưng chỉ được thử việc một lần đối với một công việc và không quá 60 ngày đối với công việc có chức danh nghề nghiệp cần trình độ chuyên môn, kỹ thuật từ cao đẳng trở lên.
- **[Bộ luật Lao động 2019, Điều 26]**: Tiền lương thử việc do hai bên thỏa thuận nhưng ít nhất phải bằng 85% mức lương của công việc đó.

---

### 🚀 Bạn nên làm gì tiếp theo
1. **Kiểm tra Hợp đồng thử việc**: Xem quy định về tiền lương (ít nhất 85%) và thời hạn.
2. **Yêu cầu kết quả sau 60 ngày**: Khi hết thử việc, công ty phải thông báo kết quả. Nếu đạt, phải ký kết Hợp đồng lao động ngay.""",
        "sources": [
            LegalSource(
                title="Bộ luật Lao động 2019",
                article="Điều 25 — Thời gian thử việc",
                effective_date="01/01/2021",
                url="https://thuvienphapluat.vn/van-ban/Lao-dong-Viec-lam/Bo-Luat-lao-dong-2019-487355.aspx",
                content_snippet="Thời gian thử việc do hai bên thỏa thuận... nhưng không quá 60 ngày đối với trình độ cao đẳng trở lên.",
                score=0.94
            ),
            LegalSource(
                title="Bộ luật Lao động 2019",
                article="Điều 26 — Tiền lương thử việc",
                effective_date="01/01/2021",
                url="https://thuvienphapluat.vn/van-ban/Lao-dong-Viec-lam/Bo-Luat-lao-dong-2019-487355.aspx",
                content_snippet="Tiền lương của người lao động trong thời gian thử việc do hai bên thỏa thuận nhưng ít nhất phải bằng 85% mức lương của công việc đó.",
                score=0.91
            ),
        ],
        "risk_level": RiskLevel.NORMAL,
        "suggested_questions": [
            "Lương thử việc có phải đóng BHXH không?",
            "Nghỉ việc khi đang thử việc có được trả lương không?",
            "Hết thời gian thử việc công ty không nói gì thì sao?"
        ]
    },
    "giữ bằng": {
        "answer": """### 📝 Trả lời ngắn gọn
**TẬP QUÁN NÀY LÀ HOÀN TOÀN TRÁI PHÁP LUẬT!** Công ty tuyệt đối KHÔNG ĐƯỢC giữ bản chính giấy tờ tùy thân, văn bằng, chứng chỉ của bạn hoặc bắt bạn đặt cọc tiền khi vào làm việc.

---

### 💡 Giải thích dễ hiểu
Dù công ty có lấy lý do "đảm bảo cam kết làm việc" hay "tránh nhân viên tự ý nghỉ", thì hành vi giữ bằng đại học gốc, học bạ, CCCD hoặc tiền cọc đều là hành vi vi phạm pháp luật lao động nghiêm trọng. Công ty vi phạm có thể bị phạt tiền từ **20.000.000đ đến 50.000.000đ**.

---

### ⚖️ Căn cứ pháp lý
- **[Bộ luật Lao động 2019, Điều 17, Khoản 1 & 2]**: Hành vi bị cấm khi tuyên dụng: 1. Giữ bản chính giấy tờ tùy thân, văn bằng, chứng chỉ của người lao động. 2. Yêu cầu người lao động phải thực hiện biện pháp bảo đảm bằng tiền hoặc tài sản khác cho việc thực hiện hợp đồng lao động.
- **[Nghị định 12/2022/NĐ-CP, Điều 9]**: Phạt tiền từ 20 - 50 triệu đồng đối với người sử dụng lao động có hành vi giữ bằng gốc hoặc thu tiền cọc.

---

### 🚀 Bạn nên làm gì tiếp theo
1. **Từ chối nộp bản gốc**: Bạn chỉ cần cung cấp bản sao có chứng thực (công chứng) hoặc mang bản gốc đến đối chiếu rồi cầm về.
2. **Khéo léo từ chối bằng văn bản/tin nhắn**: "Em được biết theo Điều 17 Bộ luật Lao động 2019, công ty không được giữ bằng gốc, em xin gửi bản công chứng ạ."
3. **Khiếu nại nếu bị ép buộc**: Nếu công ty cố tình bắt nộp mới được làm, hãy gửi phản ánh lên Thanh tra Sở Lao động - Thương binh và Xã hội địa phương.""",
        "sources": [
            LegalSource(
                title="Bộ luật Lao động 2019",
                article="Điều 17 — Hành vi người sử dụng lao động không được làm khi giao kết, thực hiện HĐLĐ",
                effective_date="01/01/2021",
                url="https://thuvienphapluat.vn/van-ban/Lao-dong-Viec-lam/Bo-Luat-lao-dong-2019-487355.aspx",
                content_snippet="Cấm giữ bản chính giấy tờ tùy thân, văn bằng, chứng chỉ của người lao động...",
                score=0.96
            ),
            LegalSource(
                title="Nghị định 12/2022/NĐ-CP",
                article="Điều 9 — Vi phạm quy định về giao kết hợp đồng lao động",
                effective_date="17/01/2022",
                url="https://thuvienphapluat.vn/van-ban/Lao-dong-Viec-lam/Nghi-dinh-12-2022-ND-CP-xuat-phat-hang-hanh-chinh-lao-dong-499385.aspx",
                content_snippet="Phạt tiền từ 20.000.000 đồng đến 50.000.000 đồng đối với người sử dụng lao động...",
                score=0.93
            ),
        ],
        "risk_level": RiskLevel.IMPORTANT,
        "suggested_questions": [
            "Nếu lỡ nộp bằng gốc rồi thì lấy lại thế nào?",
            "Công ty bắt đặt cọc tiền trước khi thử việc thì xử lý ra sao?",
            "Làm sao báo cáo công ty giữ bằng gốc với Thanh tra Lao động?"
        ]
    },
    "nghỉ việc": {
        "answer": """### 📝 Trả lời ngắn gọn
Tùy thuộc vào loại Hợp đồng lao động (HĐLĐ) bạn đã ký:
- **HĐLĐ không xác định thời hạn**: Báo trước ít nhất **45 ngày**.
- **HĐLĐ xác định thời hạn (từ 12 - 36 tháng)**: Báo trước ít nhất **30 ngày**.
- **HĐLĐ dưới 12 tháng / Thử việc**: Báo trước ít nhất **03 ngày làm việc** (Thử việc: không cần báo trước).

---

### 💡 Giải thích dễ hiểu
Bạn có quyền đơn phương chấm dứt hợp đồng lao động **mà không cần công ty đồng ý**, miễn là bạn tuân thủ đúng **thời hạn báo trước**. Nếu báo đúng hạn, bạn sẽ được nhận đầy đủ lương những ngày đã làm và trợ cấp (nếu có).

---

### ⚖️ Căn cứ pháp lý
- **[Bộ luật Lao động 2019, Điều 35, Khoản 1]**: Người lao động có quyền đơn phương chấm dứt hợp đồng lao động nhưng phải báo trước cho người sử dụng lao động biết...
- **[Bộ luật Lao động 2019, Điều 40]**: Nghĩa vụ của người lao động khi đơn phương chấm dứt HĐLĐ trái pháp luật: Không được trợ cấp thôi việc, phải bồi thường nửa tháng tiền lương và tiền vi phạm thời hạn báo trước.

---

### 🚀 Bạn nên làm gì tiếp theo
1. **Nộp đơn xin nghỉ việc bằng Email / Văn bản**: Để lưu lại bằng chứng chứng minh bạn đã thông báo đúng số ngày quy định.
2. **Bàn giao công việc**: Lập biên bản bàn giao tài sản, máy tính, công việc rõ ràng.
3. **Yêu cầu chốt sổ BHXH & thanh toán tiền lương**: Trong vòng 14 ngày làm việc kể từ ngày chấm dứt hợp đồng, công ty phải thanh toán hết tiền lương và trả sổ BHXH.""",
        "sources": [
            LegalSource(
                title="Bộ luật Lao động 2019",
                article="Điều 35 — Quyền đơn phương chấm dứt HĐLĐ của NLĐ",
                effective_date="01/01/2021",
                url="https://thuvienphapluat.vn/van-ban/Lao-dong-Viec-lam/Bo-Luat-lao-dong-2019-487355.aspx",
                content_snippet="NLĐ có quyền đơn phương chấm dứt HĐLĐ nhưng phải báo trước ít nhất 30 ngày đối với HĐLĐ xác định thời hạn từ 12 đến 36 tháng.",
                score=0.95
            ),
        ],
        "risk_level": RiskLevel.NORMAL,
        "suggested_questions": [
            "Nghỉ ngang không báo trước thì bị phạt thế nào?",
            "Thời gian nghỉ phép năm có tính vào thời hạn báo trước không?",
            "Bao lâu sau khi nghỉ việc thì được lấy lại sổ BHXH?"
        ]
    },
    "nợ lương": {
        "answer": """### 📝 Trả lời ngắn gọn
Công ty **không được chậm trả lương quá 30 ngày**. Nếu nợ lương từ 15 ngày trở lên, công ty phải trả thêm tiền lãi chậm trả. Bạn có quyền **đơn phương chấm dứt hợp đồng ngay lập tức không cần báo trước** nếu bị nợ lương!

---

### 💡 Giải thích dễ hiểu
Trường hợp đặc biệt do thiên tai, dịch bệnh thì công ty được chậm lương tối đa 30 ngày. Nhưng nếu chậm từ 15 ngày trở lên, bạn được đền bù tiền lãi theo lãi suất ngân hàng. Nếu công ty cố tình nợ lương kéo dài, đây là hành vi vi phạm nghiêm trọng.

---

### ⚖️ Căn cứ pháp lý
- **[Bộ luật Lao động 2019, Điều 35, Khoản 2, Điểm b]**: NLĐ có quyền đơn phương chấm dứt HĐLĐ **không cần báo trước** nếu không được trả đủ lương hoặc trả lương không đúng thời hạn.
- **[Bộ luật Lao động 2019, Điều 94 & 97]**: Nguyên tắc trả lương và kỳ hạn trả lương.

---

### 🚀 Bạn nên làm gì tiếp meo
1. **Gửi văn bản/Email đối chiếu lương**: Yêu cầu phòng Kế toán/HR xác nhận số tiền lương còn nợ và thời hạn trả cụ thể.
2. **Thông báo đơn phương nghỉ việc**: Gửi thông báo nghỉ việc ngay lý do công ty vi phạm nghĩa vụ trả lương.
3. **Khiếu nại Thanh tra Lao động / Công đoàn**: Gửi đơn khiếu nại tới Thanh tra Sở Lao động - Thương binh và Xã hội hoặc Hòa giải viên lao động quận/huyện.""",
        "sources": [
            LegalSource(
                title="Bộ luật Lao động 2019",
                article="Điều 97 — Kỳ hạn trả lương",
                effective_date="01/01/2021",
                url="https://thuvienphapluat.vn/van-ban/Lao-dong-Viec-lam/Bo-Luat-lao-dong-2019-487355.aspx",
                content_snippet="Trường hợp vì lý do bất khả kháng... không được chậm quá 30 ngày. Chậm từ 15 ngày trở lên phải đền bù lãi...",
                score=0.97
            ),
        ],
        "risk_level": RiskLevel.URGENT,
        "suggested_questions": [
            "Mẫu đơn khiếu nại công ty nợ lương viết thế nào?",
            "Quy trình đòi tiền lương bị nợ qua Hòa giải viên lao động?",
            "Công ty giải thể/phá sản thì tiền lương được ưu tiên trả thế nào?"
        ]
    }
}

DEFAULT_MOCK = {
    "answer": """### 📝 Trả lời ngắn gọn
Theo quy định của **Bộ luật Lao động 2019**, quyền lợi lao động của bạn luôn được pháp luật bảo vệ tối đa về hợp đồng, tiền lương, thời giờ làm việc và bảo hiểm xã hội.

---

### 💡 Giải thích dễ hiểu
Dù bạn mới đi làm hay làm việc lâu năm, bạn cần lưu ý 3 nguyên tắc vàng:
1. **Phải có thỏa thuận bằng văn bản**: Hợp đồng lao động hoặc hợp đồng thử việc rõ ràng.
2. **Không nộp bản gốc CCCD/Bằng cấp/Tiền cọc**.
3. **Nắm rõ thời gian làm việc & thời gian nghỉ ngơi** (tối đa 8 giờ/ngày, 48 giờ/tuần).

---

### ⚖️ Căn cứ pháp lý
- **[Bộ luật Lao động 2019, Điều 13]**: Hợp đồng lao động là sự thỏa thuận giữa người lao động và người sử dụng lao động về việc làm có trả công, tiền lương, điều kiện lao động, quyền và nghĩa vụ của mỗi bên.
- **[Bộ luật Lao động 2019, Điều 105]**: Thời giờ làm việc bình thường không quá 08 giờ trong 01 ngày và không quá 48 giờ trong 01 tuần.

---

### 🚀 Bạn nên làm gì tiếp theo
1. Bạn có thể gõ câu hỏi chi tiết hơn về trường hợp cụ thể của bạn (ví dụ: *thử việc*, *nợ lương*, *nghỉ việc*, *làm thêm giờ OT*...).
2. Mình sẽ trích dẫn điều luật cụ thể để bạn kiểm tra!""",
    "sources": [
        LegalSource(
            title="Bộ luật Lao động 2019 (Luật 45/2019/QH14)",
            article="Điều 13 — Hợp đồng lao động",
            effective_date="01/01/2021",
            url="https://thuvienphapluat.vn/van-ban/Lao-dong-Viec-lam/Bo-Luat-lao-dong-2019-487355.aspx",
            content_snippet="Quy định chung về Hợp đồng lao động và quyền lợi nghĩa vụ các bên.",
            score=0.90
        )
    ],
    "risk_level": RiskLevel.NORMAL,
    "suggested_questions": [
        "Thử việc 2 tháng có đúng luật không?",
        "Công ty giữ bằng gốc của mình có được không?",
        "Nghỉ việc có cần báo trước 30 ngày không?"
    ]
}


def get_mock_response(query: str) -> Dict:
    """Find matching mock or fallback to default mock."""
    query_lower = query.lower()
    for key, data in MOCK_DATABASE.items():
        if key in query_lower:
            return data
    return DEFAULT_MOCK


def mock_stream_response(full_text: str, delay: float = 0.015) -> Generator[str, None, None]:
    """Yield word chunks to simulate real-time AI response streaming."""
    words = full_text.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(delay)
