"""Xuất chunk Day 6 (chunks_b) và câu hỏi Day 6 -> data/chunks.json, data/questions.json."""
import json
import psycopg
from common import DATA, TABLE, db_url

D6 = DATA.parent.parent.parent / "Day6" / "Lab6"
DATA.mkdir(exist_ok=True)
with psycopg.connect(db_url()) as c:
    rows = c.execute(f"SELECT chunk_id,text,document_id,source,page,section,mien,metadata FROM {TABLE} ORDER BY document_id,page,chunk_id").fetchall()
chunks = [{"id": r[0], "text": r[1], "source_id": r[2], "source": r[3], "page": r[4],
           "metadata": {**(r[7] or {}), "section": r[5], "mien": r[6]}} for r in rows]
json.dump(chunks, open(DATA / "chunks.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)

qs = json.load(open(D6 / "benchmark" / "questions.json", encoding="utf8"))
out = []
for q in qs:
    o = {"id": q["id"], "split": q["split"], "question": q["question"], "expected_answer": q["expected_answer"],
         "answerable": True, "expected_behavior": "search_and_answer",
         "gold": [{"source_id": q["gold_source_id"], "page": q["gold_page"], "evidence": q["evidence_quote"]}]}
    if q.get("filter"):
        o["filter"] = q["filter"]
    out.append(o)
json.dump(out, open(DATA / "questions_answerable.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
print(len(chunks), "chunks;", len(out), "câu có đáp án")
