"""Ghép bộ câu hỏi Day 7: 27 câu có đáp án (Day 6) + 4 câu thiếu bằng chứng; kiểm chứng sự vắng mặt trong corpus Day 6."""
import json, re
from common import DATA

D6 = DATA.parent.parent.parent / "Day6" / "Lab6" / "starter" / "data" / "corpus.json"
qs = json.load(open(DATA / "questions_answerable.json", encoding="utf8"))
chunks = json.load(open(DATA / "chunks.json", encoding="utf8"))

# q05: bằng chứng bị cắt ngang giữa 2 chunk liền kề (Day 6 tách theo đoạn 500 ký tự, có thể cắt giữa câu).
for q in qs:
    if q["id"] == "q05":
        q["gold"] = [{"source_id": "nha-trang", "page": 4,
                      "evidence": "theo quyết định số 391-CP/QĐ của Hội đồng Chính phủ nước Cộng hòa Xã hội chủ nghĩa Việt Nam, thị xã Nha Trang được nâng lên cấp thành phố trực thuộc tỉnh"}]
        q["gold_all"] = [{"source_id": "nha-trang", "page": 4, "evidence": "Ngày 30 tháng 3 năm 1977,"}, q["gold"][0]]
        q["note"] = "Multi-chunk: ngày nằm cuối chunk para:0, quyết định nằm đầu chunk para:1. Hit@k tính theo chunk chứa quyết định; Context Evidence yêu cầu đủ cả hai (gold_all)."

absent = [
 ("u01", "dev", "Giá vé cáp treo Hòn Thơm ở Phú Quốc hiện nay là bao nhiêu?", r"giá vé|vé cáp|\d+\.?\d*\s*(đồng|vnđ|vnd)", "Bài Phú Quốc chỉ liệt kê Cáp treo Hòn Thơm như một điểm tham quan, không nêu giá vé."),
 ("u02", "dev", "Nhiệt độ trung bình vào mùa đông ở Sa Pa là bao nhiêu độ C?", r"sa pa.{0,200}(nhiệt độ|°C)|(nhiệt độ|°C).{0,200}sa pa", "Các đoạn Sa Pa không có số liệu nhiệt độ/khí hậu."),
 ("u03", "test", "Đỉnh Fansipan cao bao nhiêu mét?", r"3\.?143|fansipan.{0,80}\d[\d.,]*\s*(m|mét)\b", "Fansipan chỉ được nhắc tên (nóc nhà Đông Dương, khách sạn Fansipan), không nêu độ cao."),
 ("u04", "test", "Năm 2023 Nha Trang đón bao nhiêu lượt khách du lịch?", r"lượt khách|khách du lịch|du khách", "Bài Nha Trang trong corpus không có thống kê lượt khách."),
]
corpus_text = open(D6, encoding="utf8").read()
all_text = corpus_text + " ".join(c["text"] for c in chunks)
for uid, split, question, pattern, reason in absent:
    hits = [m.group(0) for m in re.finditer(pattern, all_text, re.I)]
    scope = hits  # in ra để người làm tự đọc lại
    print(uid, "khớp regex kiểm tra:", len(scope), scope[:3])
    qs.append({"id": uid, "split": split, "question": question, "answerable": False,
               "expected_behavior": "search_and_abstain", "absence_reason": reason,
               "absence_check": f"regex {pattern!r} trên toàn bộ corpus Day 6 + 129 chunk"})
json.dump(qs, open(DATA / "questions.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(len(qs), "câu")
