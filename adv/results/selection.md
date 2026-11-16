# Chốt cấu hình nâng cao TRƯỚC khi chạy test (ghi trước khi chạy test)

Kết quả dev (18 câu: 15 có đáp án + 3 thiếu bằng chứng), chấm tự động rồi người đọc lại các câu bị trượt:
- A0 dense + text/mô tả (không xem ảnh), gpt-4.1-mini: 17/18 tự động (trượt d12: lấy nhầm "3 thành phần" từ Table 7) — baseline.
- A1 dense + view_page, gpt-4.1-mini: 16/18 (trượt d12 một phần; d17 bịa "88 triệu người dùng" từ con số 88%).
- A2 hybrid(dense+BM25) + view_page, gpt-4.1-mini: tự động 17/18; câu d12 máy chấm cho "partial" nhưng đọc tay thì câu trả lời ĐÚNG (liệt kê 4 thành phần) => 18/18 sau khi đọc lại. Chi phí $0.09, 173s.
- A3 hybrid + view_page, gpt-4.1: 18/18. Chi phí $0.65, 941s (~$0.036/câu).

Tiêu chí chọn công bố trước (thứ tự): (1) tỷ lệ đạt dev sau khi đọc lại; (2) nếu hòa, ưu tiên cấu hình ít rủi ro sai trên câu chưa thấy (model mạnh hơn),
miễn chi phí < $0.05/câu; (3) thời gian. Dev quá nhỏ và bão hòa nên A2 và A3 hòa 18/18 => theo (2) chọn **A3_hybrid_view_41**
(hybrid RRF dense+BM25, view_page, gpt-4.1, top_k=5, tối đa 4 lượt search và 4 lượt xem ảnh). Đây là quyết định theo tiêu chí dự phòng, không phải do dev phân biệt được.
Baseline để so sánh trên test: A0_dense_text. Test chạy 1 lần cho mỗi cấu hình; không chỉnh gì dựa trên test.
