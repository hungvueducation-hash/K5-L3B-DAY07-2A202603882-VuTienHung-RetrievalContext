# Chốt cấu hình trước khi chạy test (ghi trước khi chạy test)

Tiêu chí (thứ tự ưu tiên, công bố trước): (1) Context Evidence Rate trên dev, (2) số câu trả lời đúng/đủ đọc tay trên dev,
(3) từ chối đúng câu thiếu bằng chứng, (4) chi phí/thời gian.

Kết quả dev (agent gpt-4o-mini, 22 câu, 20 có đáp án): base_dense 11/20, bm25 19/20, hybrid 17/20, hybrid3 17/20, hybrid3_k5_rw 16/20.
=> Chọn `bm25` (top_k=3, budget=1500 ký tự, max_searches=3). Baseline so sánh: `base_dense` (dense Day 6, cùng tham số).
Test CHƯA được dùng để chọn hay chỉnh bất cứ thứ gì. Mọi chỉnh sửa validator đã làm trên dev trước đó.
