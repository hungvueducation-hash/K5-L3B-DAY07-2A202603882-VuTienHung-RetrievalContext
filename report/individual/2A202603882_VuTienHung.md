# Báo cáo Day 7 — 2A202603882 — Vũ Tiến Hùng

> **Trạng thái:** bản nháp do Claude (AI hỗ trợ lập trình) tạo; mọi nhãn chấm tay trong báo cáo là **nhãn sơ bộ của Claude**, Hùng cần tự đọc lại trace và sửa trước khi nộp. Phần thử thách nâng cao (+15) **chưa làm**.

## Dữ liệu và benchmark

- Nguồn, quyền sử dụng, số trang và số chunk: dùng lại corpus Day 6 — 4 bài Wikipedia tiếng Việt (Nha Trang, Phú Quốc, Sa Pa, Vũng Tàu), CC BY-SA 4.0/GFDL, 34 unit (page), **129 chunk** (chiến lược B Day 6: `by_paragraph(max_size=500)`, bảng `chunks_b`). Lưu ý: chunk có thể cắt ngang câu/từ (vd. q05).
- Vector store, embedding model, phiên bản và số chiều: PostgreSQL 16 + pgvector 0.8.7 (Docker, Day 6), cosine, `sentence-transformers/all-MiniLM-L6-v2`, 384 chiều (**model tiếng Anh**, dùng cho câu hỏi tiếng Việt → dense yếu). Thí nghiệm thêm: `paraphrase-multilingual-MiniLM-L12-v2` (384 chiều) index mới trong bộ nhớ (`data/emb_*.npy`), chi phí $0 (local).
- Agent model, cách chạy và phân chia dev/test: `gpt-4o-mini` (OpenAI, tool calling, temperature 0). Dev = 20 câu có đáp án + 2 thiếu bằng chứng (u01, u02); test = 7 + 2 (u03, u04). 27 câu có đáp án lấy từ benchmark Day 6 (dev/test giữ nguyên chia của Day 6); 4 câu thiếu bằng chứng do tôi thêm. **Lưu ý trung thực:** kết quả test của baseline dense Day 6 đã được xem trong báo cáo Day 6 trước khi làm Day 7; cấu hình được chọn bằng dev, không chỉnh theo test.
- Cách xác định câu có/thiếu evidence và tiêu chí chấm: câu có đáp án có `gold` (source, page, đoạn evidence nằm trọn trong 1 chunk; hit = chunk đúng nguồn/trang chứa evidence). q05 là multi-chunk (ngày ở cuối `para:0`, quyết định ở đầu `para:1`): Hit@k tính theo chunk chứa quyết định; Context Evidence yêu cầu đủ cả 2 (`gold_all`). Câu thiếu bằng chứng: chủ đề gần nhưng grep regex toàn corpus + 129 chunk không có đáp án (`src/build_questions.py`; vài regex khớp ngẫu nhiên, đã đọc tay: giá tiêu 120.000đ/kg, "du khách" trong ngữ cảnh khác — không trả lời được câu hỏi). Filter `mien`/`section` do câu hỏi cung cấp (từ Day 6), áp cố định cho mọi phương pháp, model không tự suy ra, không suy từ gold.

## Retrieval và thử nghiệm

Retrieval thuần, **query gốc**, cùng corpus/câu hỏi/filter (không LLM). Hit@1 / Evidence Hit@3 trên câu có đáp án.

| Phương pháp | Mô tả | Dev Hit@1 | Dev Hit@3 | Dev MRR@10 | Test Hit@1 | Test Hit@3 |
|---|---|---|---|---|---|---|
| **dense** (baseline Day 6) | MiniLM-L6 + pgvector | 8/20 | 13/20 | 0.504 | 5/7 | 6/7 |
| bm25_syllable | BM25, tách âm tiết | 18/20 | 20/20 | 0.950 | 7/7 | 7/7 |
| **bm25** (chọn) | BM25, âm tiết + bigram | 18/20 | 20/20 | 0.942 | 7/7 | 7/7 |
| hybrid_rrf | RRF(dense, bm25) | 12/20 | 18/20 | 0.749 | 6/7 | 7/7 |
| dense_multilingual | embedding đa ngữ, index mới | 10/20 | 13/20 | 0.611 | 3/7 | 5/7 |
| hybrid_ml_rrf | RRF(dense đa ngữ, bm25) | 13/20 | 18/20 | 0.768 | 6/7 | 6/7 |
| hybrid3_rrf | RRF(dense, đa ngữ, bm25) | 14/20 | 19/20 | 0.821 | 5/7 | 6/7 |

(Cột test chỉ chạy **sau khi chốt cấu hình** và chỉ để báo cáo.) Thời gian retrieval: BM25 ≈ 0.03–0.11s cho 20 câu; dense 4.8s (gồm nạp model). Chi phí $0.

Agent thật (gpt-4o-mini, max 3 lượt search, budget 1500 ký tự gồm id/nguồn, dedupe theo chunk id), dev, 22 câu:

| Cấu hình | Phương pháp, top-k, budget | Giả thuyết | Context Evidence Rate | Search-1 Hit@3 | Trả lời/Từ chối | Thời gian / chi phí* |
|---|---|---|---|---|---|---|
| base_dense (Baseline) | dense, k=3, 1500 | baseline Day 6 | 11/20 | 12/20 | 12/10 | 112s / $0.0093 |
| **bm25 (Phương pháp 2, chọn)** | BM25, k=3, 1500 | embedding tiếng Anh yếu với tiếng Việt, câu hỏi chứa tên riêng/số → lexical tốt hơn | **19/20** | 20/20 | 20/2 | 66s / $0.0059 |
| hybrid (Phương pháp 3) | RRF dense+bm25, k=3 | trộn có thể bù hai phía | 17/20 | 18/20 | 18/4 | 101s / $0.0071 |
| hybrid3 (Cải thiện 1) | RRF dense+đa ngữ+bm25 | thêm embedding đa ngữ cải thiện dense | 17/20 | 18/20 | 18/4 | 101s / $0.0071 |
| hybrid3_k5_rw (Cải thiện 2) | như hybrid3, k=5, budget 2800, gợi ý viết lại query | tăng recall nhờ nhiều candidate + query ngắn | 16/20 | 16/20 | 18/4 | 114s / $0.0106 |

\*Chi phí tính theo giá gpt-4o-mini $0.15/$0.60 mỗi 1M token (giá tôi nhớ, cần đối chiếu bảng giá hiện hành). Search-1 Hit@3 = evidence trong top-3 của lượt tìm đầu tiên (agent tự viết query, không phải query gốc).

Test (chạy 1 lần sau khi chốt), 9 câu:

| Cấu hình | Context Evidence Rate | Search-1 Hit@3 | Trả lời/Từ chối | Thời gian / chi phí |
|---|---|---|---|---|
| Baseline base_dense | 4/7 | 5/7 | 4/5 | 72s / $0.0046 |
| **Đã chọn bm25** | **7/7** | 7/7 | 7/2 | 38s / $0.0033 |

**Hai lỗi dev và cách xử lý.**
1. *Lỗi code của tôi (lần chạy 1):* validator yêu cầu thẻ `[id]` xuất hiện trong văn bản, nhưng model chỉ điền mảng `citations` → hầu hết câu bị gán "abstain" dù context đủ (bm25 chỉ 1/22 answered). Sửa: chấp nhận khi ID có trong context, tự nối `[id]` còn thiếu; chạy lại toàn bộ dev. Bản lỗi giữ ở `results/agent-dev-run1-validator-bug/`. Ý nghĩa: chỉ số "abstain" của lần 1 không phản ánh chất lượng agent.
2. *Dense bỏ sót chunk đúng:* `dense` chỉ Hit@3 13/20 và agent dev base_dense Context Evidence 11/20. Nguyên nhân giả thuyết: embedding MiniLM-L6 là tiếng Anh. Thử embedding đa ngữ: **không cải thiện** (13/20 Hit@3 vẫn như cũ, Hit@1 10/20), và hybrid với dense còn **kéo BM25 xuống** (18–19/20 vs 20/20). Kết luận: trong corpus này, câu hỏi chứa nhiều tên riêng/số/cụm từ gần nguyên văn nên lexical thắng; RRF cộng thứ hạng không chuẩn hóa độ tin cậy nên dense tệ làm hỏng kết quả BM25.

Lý do chọn bm25: tiêu chí công bố trước (`results/selection.md`): (1) Context Evidence Rate dev, (2) câu trả lời đọc tay, (3) từ chối đúng, (4) chi phí/thời gian — bm25 dẫn đầu cả 4.

## Agent và đánh giá

- Tool: `search_documents(query)` (model tự viết/viết lại query, nhiều lượt) và `submit_answer(answer, citations, sufficient_evidence)`. Dừng khi model nộp; tối đa 3 lượt search (mặc định của tôi, không phải giới hạn của đề). Context = tất cả chunk đã đưa cho model, dedupe theo id, budget 1500 ký tự (chunk không vừa bị bỏ). Lỗi API/DB ghi `status: error` (không có lỗi nào xảy ra). Model không nhận gold/expected_answer; nội dung chunk được dặn là dữ liệu, không phải chỉ dẫn.
- Tool use: 22/22 (dev), 9/9 (test) có gọi search. Phân bố lượt gọi bm25 dev: 1 lượt 20 câu, 3 lượt 2 câu (2 câu thiếu evidence thử đủ 3 lần rồi từ chối); test: 1 lượt 6, 3 lượt 3.

Nhãn chấm tay **sơ bộ của Claude** (đọc câu trả lời đối chiếu đáp án và đoạn được cite; chưa đọc lại toàn văn mọi evidence — cần Hùng kiểm tra):

| Cấu hình / split | Tool use | Grounded answer 0/1/2 (trung bình) | Citation hợp lệ | Câu có citation | Abstention đúng | Từ chối nhầm |
|---|---|---|---|---|---|---|
| bm25 / dev | 22/22 | 0:0, 1:1 (q05), 2:19 → 1.95/2 (n=20) | 21/21 theo ID trong context; hỗ trợ nội dung: đọc sơ bộ đúng, q07 cite thêm `p16` chưa xác nhận | 20/20 | 2/2 | 0/20 |
| bm25 / test | 9/9 | 0:0, 1:0, 2:7 → 2.0/2 (n=7) | 7/7 ID hợp lệ, nội dung sơ bộ đúng | 7/7 | 2/2 | 0/7 |
| base_dense / test | 9/9 | 2 câu đúng chắc (q23, q26), q22, q25 đúng sơ bộ; 3 câu từ chối nhầm → chấm 0 | 4/4 ID hợp lệ | 4/4 | 2/2 | 3/7 (q21, q24, q27) |

Ví dụ (trace: `results/agent-test/traces_*.json`):
- *Có bằng chứng:* q27 "Sa Pa nằm ở độ cao bao nhiêu mét?" (filter mien=Bắc) → bm25: "1.500 mét [sa-pa:p30:para:1]" (nhãn 2). Baseline dense cùng câu: từ chối vì dense không tìm đúng chunk (nhãn 0 — từ chối nhầm).
- *Thiếu bằng chứng:* u03 "Đỉnh Fansipan cao bao nhiêu mét?" → cả hai cấu hình từ chối, không đưa số từ kiến thức ngoài (nhãn đúng; tôi chưa kiểm chứng trace từng bước ngoài kết luận).
- *Lỗi:* q05 (dev) agent trả lời quyết định 391-CP/QĐ nhưng **thiếu ngày 30/3/1977** vì ngày nằm ở chunk bên cạnh (nhãn 1; do chunking Day 6 cắt giữa câu — giải pháp chưa thử: lấy chunk lân cận).

Không có chấm context 0/1/2 riêng cho 5 câu test (BENCHMARK yêu cầu); chỉ có Context Evidence Rate tự động — **còn thiếu**, cần Hùng đọc ≥5 câu test baseline và cấu hình chọn.

- Lệnh chạy (Python venv của Day 6, cần Docker pgvector Day 6 và `OPENAI_API_KEY` trong `Day6/Lab6/starter/.env`; không commit `.env`):
  `python src/export_data.py` → `python src/build_questions.py` → `python src/retrieval_eval.py dev|test` → `python src/run_agent_benchmark.py <config> dev|test`. Kết quả: `results/`.
- Giới hạn: (1) benchmark nhỏ (7 câu test có đáp án, 2 thiếu bằng chứng) → khoảng tin cậy rộng; (2) câu hỏi Day 6 viết gần nguyên văn tài liệu → thiên lợi cho BM25, kết luận "lexical > dense" có thể không giữ với câu hỏi diễn đạt lại tự nhiên; (3) corpus chỉ 129 chunk nên Recall@10 hầu như bão hoà; (4) chưa thử rerank, chunk lân cận, nén context; (5) chưa có chấm context 0/1/2; (6) chi phí tính theo giá chưa đối chiếu.

## Thử thách nâng cao (nếu thực hiện)

Chưa thực hiện.
