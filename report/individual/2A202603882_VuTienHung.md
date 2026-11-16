# Báo cáo Day 7 — 2A202603882 — Vũ Tiến Hùng

> **Khai báo dùng AI:** code, thí nghiệm và bản nháp báo cáo được tạo với sự hỗ trợ của Claude Code (theo RULES.md cho phép AI hỗ trợ lập trình). Các nhãn chấm tay do Claude đề xuất từ việc đọc trace; Hùng đã đọc và duyệt trước khi nộp. Phần thử thách nâng cao (+15) đã làm nhưng **không đạt ngưỡng 90%** (xem cuối báo cáo).

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

\*Chi phí tính theo giá gpt-4o-mini $0.15/$0.60 mỗi 1M token (đã đối chiếu trang model của OpenAI ngày 2026-11-16: $0.15/$0.60; trang ghi gpt-4o-mini đã bị đánh dấu deprecated). Search-1 Hit@3 = evidence trong top-3 của lượt tìm đầu tiên (agent tự viết query, không phải query gốc).

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

Chấm context cuối gửi model (0 = không có evidence; 1 = có nhưng thiếu điều kiện/nguồn; 2 = đủ evidence và nguồn), 7 câu test có đáp án, đối chiếu đoạn gold với danh sách chunk trong context (mỗi chunk đi kèm nguồn/trang):

| Query | Baseline dense | Lý do | bm25 (chọn) | Lý do |
|---|---|---|---|---|
| q21 | 0 | context toàn đoạn Vũng Tàu p33/p34, không có đoạn "phường Vũng Tàu thuộc TP.HCM" | 2 | có `vung-tau:p31:para:0` chứa câu gold |
| q22 | 2 | có `vung-tau:p32:para:0` | 2 | như trái |
| q23 | 2 | có `vung-tau:p33:para:5` | 2 | như trái |
| q24 | 0 | không có đoạn Minh Mạng/ba làng (lẫn Phú Quốc, Sa Pa) | 2 | có `vung-tau:p34:para:0` |
| q25 | 2 | có `vung-tau:p34:para:2` | 2 | như trái |
| q26 | 2 | có `phu-quoc:p13:para:3` | 2 | như trái |
| q27 | 0 | Sa Pa p27/p29, thiếu p30 chứa "1.500m" | 2 | có `sa-pa:p30:para:1` |
| **Số câu 0/1/2** | **3 / 0 / 4** | | **0 / 0 / 7** | |

Không câu nào chấm mức 1: mọi chunk trả về đều mang nguồn/trang, và các đoạn gold nằm trọn trong một chunk nên không có trường hợp thiếu điều kiện.

- Lệnh chạy (Python venv của Day 6, cần Docker pgvector Day 6 và `OPENAI_API_KEY` trong `Day6/Lab6/starter/.env`; không commit `.env`):
  `python src/export_data.py` → `python src/build_questions.py` → `python src/retrieval_eval.py dev|test` → `python src/run_agent_benchmark.py <config> dev|test`. Kết quả: `results/`.
- Giới hạn: (1) benchmark nhỏ (7 câu test có đáp án, 2 thiếu bằng chứng) → khoảng tin cậy rộng; (2) câu hỏi Day 6 viết gần nguyên văn tài liệu → thiên lợi cho BM25, kết luận "lexical > dense" có thể không giữ với câu hỏi diễn đạt lại tự nhiên; (3) corpus chỉ 129 chunk nên Recall@10 hầu như bão hoà; (4) chưa thử rerank, chunk lân cận, nén context; (5) chưa có chấm context 0/1/2; (6) chi phí tính theo giá chưa đối chiếu.

## Thử thách nâng cao (nếu thực hiện)

**Kết luận ngắn (nói thẳng): phần nâng cao KHÔNG đạt ngưỡng 90%, không nhận bonus +15.** Cấu hình tốt nhất trên test đạt **24/30 = 80%** (cần ≥27/30); cấu hình tôi đã chọn trước khi chạy test chỉ đạt **19/30 = 63,3%** (chấm nghiêm ngặt). Chi tiết và các lỗi của chính quy trình tôi ở dưới.

- Tài liệu, nguồn, quyền sử dụng, số trang và phiên bản: World Bank, *Viet Nam Rising: Pathways to a High-Income Future* (23/07/2025), bản tiếng Anh **248 trang** (trang PDF), hdl.handle.net/10986/43481, giấy phép **CC BY-NC 3.0 IGO** (dùng phi thương mại, ghi nguồn). PDF **không** nằm trong repo; `adv/download.sh` tải lại và kiểm SHA-256 `e2974ce5…c552`. Có 154 hình và 19 bảng (biểu đồ, sơ đồ khung, bản đồ Đồng bằng sông Cửu Long, bảng số và bảng chính sách).
- Cách xử lý text, bảng, ảnh, biểu đồ; phạm vi index và phần chưa xử lý: (1) text layer PDF bằng pypdf → 829 chunk text (~900 ký tự), mỗi chunk giữ số trang. Text layer **làm xáo trộn bảng** (số rời khỏi nhãn hàng/cột) nên không đủ cho câu bảng. (2) Mỗi trang dựng thành ảnh (pypdfium2) rồi `gpt-4.1-mini` (vision) mô tả bảng/biểu đồ/sơ đồ → 164 chunk "visual" (có thể sai, chỉ dùng để tìm). (3) Embedding `text-embedding-3-small` (1536 chiều), lưu .npy. (4) Agent có thêm tool `view_page(page)` xem ảnh trang gốc để tự đọc số. Phạm vi: cả 248 trang đều được index (không trang lỗi); không có ảnh crop theo vùng; mô tả visual **chưa được kiểm toàn bộ** với bản gốc (chỉ kiểm các trang trong benchmark).
- Cách chia benchmark, schema evidence, model và cấu hình: 54 câu = **dev 18** (15 có đáp án + 3 thiếu bằng chứng) và **test 30** (24 + 6) với đúng phân bố yêu cầu (test: bảng 6, ảnh/sơ đồ 5, biểu đồ 5, multi-hop 4, text 4, thiếu bằng chứng 6). Gold do tôi đọc **trực tiếp trên ảnh trang gốc**, không từ mô tả của model; mỗi gold ghi trang PDF, vùng (Table/Figure, hàng/cột) và nội dung; dev/test không dùng chung trang gold. Câu hỏi tiếng Anh (khớp ngôn ngữ tài liệu). `adv/benchmark.json`. Câu thiếu bằng chứng kiểm bằng regex trên text 248 trang + mô tả visual (xem `absence_check`).

**So sánh retrieval thuần (query gốc, hit theo trang gold; multi-hop cần đủ mọi trang):**

| Phương pháp | Dev Hit@1 | Dev Ev.Hit@3 | Dev @5 | Test Hit@1 | Test Ev.Hit@3 | Test @5 |
|---|---|---|---|---|---|---|
| dense (embedding) | 12/15 | 15/15 | 15/15 | 16/24 | 20/24 | 23/24 |
| BM25 | 13/15 | 13/15 | 13/15 | 20/24 | 21/24 | 21/24 |
| hybrid RRF | 13/15 | 14/15 | 15/15 | 18/24 | 22/24 | 22/24 |
| dense chỉ chunk visual | 13/15 | 13/15 | 14/15 | 14/24 | 18/24 | 20/24 |

**Agent (chấm nghiêm ngặt = trả lời đúng theo đáp án chuẩn và trích đủ trang gold; câu thiếu bằng chứng chỉ đạt khi agent nộp lời từ chối thật; lỗi/không có kết quả = không đạt, vẫn nằm trong mẫu số):**

| Cấu hình | Mô tả | Dev (n=18) | Test (n=30) | Test theo nhóm (bảng/ảnh/biểu đồ/multihop/text/thiếu) | Thời gian / chi phí test |
|---|---|---|---|---|---|
| A0 baseline | dense, chỉ text+mô tả, gpt-4.1-mini | 17/18 | **24/30 (80%)** | 6/6, 5/5, 2/5, 2/4, 4/4, 5/6 | 162s / $0.06 |
| A2 | hybrid RRF + view_page, gpt-4.1-mini | 16/18 | 23/30 | 6/6, 4/5, 3/5, 1/4, 4/4, 5/6 | 822s / $0.17 |
| **A3 (đã chọn trước khi chạy test)** | hybrid + view_page, gpt-4.1 | 15/18 | **19/30 (63%)** | 6/6, 5/5, 2/5, 2/4, 3/4, 1/6 | 2286s / $1.27 |
| A1 | dense + view_page, gpt-4.1-mini | 16/18 | (không chạy test) | | |

Không có lỗi API/timeout nào (0/30). Với A2 trên dev, máy chấm gán d12 là "partial" dù câu trả lời đúng khi đọc tay, nên A2 dev thực tế có thể là 17/18; tôi giữ số theo máy chấm cho nhất quán.

**Điều đã sai trong quy trình của tôi (trung thực):**
1. **Chọn cấu hình dựa trên số liệu sai.** Bộ chấm tự động ban đầu coi "abstain" là đạt cho câu thiếu bằng chứng, kể cả khi agent **hết lượt mà không nộp câu trả lời** ("No final answer"). Trên dev, A3 có 3 câu như vậy (d16, d17, d18) nên con số "18/18" ban đầu là sai; chấm đúng A3 chỉ 15/18 và A0 là tốt nhất (17/18). Tôi chốt A3 (theo tiêu chí dự phòng "dev hòa → chọn model mạnh hơn") khi số liệu dev còn sai. Nếu chấm đúng từ đầu, tiêu chí đã công bố sẽ chọn A0. Tôi **không** chọn lại sau khi xem test; A3 vẫn là "cấu hình đã chốt".
2. **Lỗi hệ thống trong agent:** khi hết lượt search/xem ảnh mà chưa nộp, vòng lặp trả "No final answer" thay vì ép nộp. Trên test, A3 gặp 5 câu (t15 và t25–t28); 4 câu thiếu bằng chứng trong đó từng được máy chấm tính "đạt" sai. Đây là lỗi thiết kế agent, **chưa sửa**, vì sửa rồi chạy lại trên test là chỉnh theo test.
3. **Lỗi nhãn của tôi (phát hiện khi đọc tay kết quả test):** (a) bỏ sót trang thay thế: t13 (biểu đồ lặp ở trang 211), t21 (đoạn văn lặp ở trang 22), t19 (gói PP4 còn được mô tả ở trang 49) và t12 (trang 56), nên các câu trả lời đúng nhưng trích trang khác trang gold bị chấm trượt; (b) **t30 không hợp lệ**: báo cáo có số liệu lương trung bình (agent trích trang 206), câu "thiếu bằng chứng" của tôi sai; (c) t18 mơ hồ: Table 15 cho cost-effectiveness của cash transfers là 0,03 nhưng Table 16 baseline CE là 0,6, agent dùng bảng sau. Sửa các nhãn này sau khi đã xem test nên **test này không còn độc lập**: số "đã sửa nhãn" dưới đây chỉ để tham khảo, không dùng để nhận bonus.

| Cấu hình | Test chấm nghiêm ngặt, nhãn gốc | Sau khi sửa nhãn (bỏ t30; thêm trang thay thế), chỉ tham khảo |
|---|---|---|
| A0 | 24/30 (80,0%) | 24/29 (82,8%) |
| A2 | 23/30 (76,7%) | 23/29 (79,3%) |
| A3 | 19/30 (63,3%) | 22/29 (75,9%) |

Cả ba đều thấp hơn ngưỡng 90% (≥27/30). Để báo điểm bonus chặt chẽ cần **bộ test mới** (đề yêu cầu) sau khi sửa agent; tôi chưa làm.

**Lỗi đã đọc, nguyên nhân (A3 trên test):** t15 (Figure 67): xem trang 130 rồi xem thêm trang khác, hết lượt, không nộp → lỗi vòng lặp. t16 (Figure 109): đúng kênh "heat stress" và xu hướng tăng nhưng nói "70–80% suốt giai đoạn" trong khi biểu đồ cho khoảng 63% (2030) đến 77% (2045): đọc giá trị biểu đồ chưa chính xác. t25–t28: model liên tục gọi view_page để "tìm cho chắc" câu không có đáp án rồi hết lượt. Biểu đồ là nhóm yếu nhất ở mọi cấu hình (2–3/5).

**Mức đạt theo nhóm (A3 test, nghiêm ngặt):** bảng 6/6, ảnh/sơ đồ 5/5, biểu đồ 2/5, multi-hop 2/4, text 3/4, thiếu bằng chứng 1/6 → tổng 19/30.

- Trace, nhãn và evidence từng câu; thời gian, chi phí, lỗi hệ thống: `adv/results/agent-{dev,test}/traces_*.json` (mỗi trace: tool call, trang đã xem, context, câu trả lời, citation, token, chi phí), `summary_*.json`, `retrieval_{dev,test}.json`, `selection.md` (tiêu chí viết trước khi chạy test), `benchmark.json`. Nhãn cuối của test do Claude đọc đối chiếu; máy chấm (gpt-4.1) chỉ là bước sơ bộ và từng sai (vd. d12). Hùng cần xem lại các nhãn này. Chi phí ước tính toàn bộ phần nâng cao ≈ $2,7 (mô tả ảnh 248 trang $0,28; embedding <$0,01; agent dev ≈ $0,86; agent test ≈ $1,5; chấm điểm vài cent). Giá đã đối chiếu trang OpenAI ngày 2026-11-16: gpt-4.1-mini $0,40/$1,60, gpt-4.1 $2/$8, text-embedding-3-small $0,02 mỗi 1M token; hai model chat bị OpenAI đánh dấu deprecated.
- Giới hạn và cách tái lập: giới hạn: benchmark do một người viết (gold chưa có người thứ hai kiểm); câu hỏi viết bám tài liệu; mô tả visual do model sinh; chưa sửa lỗi hết lượt; chưa có test độc lập mới. Tái lập (venv Day 6 + `pypdfium2`, `pillow`, `pypdf`; cần `OPENAI_API_KEY`): `sh adv/download.sh` → `python adv/prepare.py <pdf> adv/work` → `python adv/describe_pages.py gpt-4.1-mini` → `python adv/build_benchmark.py` → `python adv/index.py` → `python adv/retrieval_eval.py dev|test` → `python adv/run_agent.py <A0_dense_text|A2_hybrid_view|A3_hybrid_view_41> dev|test`. Thư mục `adv/work/` (ảnh trang, text, mô tả) không được commit.
