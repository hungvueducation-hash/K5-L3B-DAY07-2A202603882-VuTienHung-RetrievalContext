"""Bước 3: dựng index đa phương thức cho cả 248 trang.
Mỗi trang cho ra: (a) các chunk TEXT (~900 ký tự, tách theo dòng/câu) từ text layer PDF; (b) 1 chunk VISUAL (mô tả bảng/biểu đồ/sơ đồ do
model vision sinh từ ảnh trang, nếu trang có nội dung trực quan). Mọi chunk giữ page + kind; ảnh trang gốc ở work/img/pNNN.jpg để model xem lại.
Embedding: OpenAI text-embedding-3-small (1536 chiều), lưu .npy. Dùng: python index.py"""
import json, re, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import common  # noqa
import os
from openai import OpenAI

W = Path(__file__).resolve().parent / "work"
EMB = "text-embedding-3-small"


def split_text(t, size=900):
    parts, cur = [], ""
    for line in t.split("\n"):
        line = line.strip()
        if not line:
            continue
        if cur and len(cur) + len(line) > size:
            parts.append(cur); cur = line
        else:
            cur = (cur + " " + line).strip()
    if cur:
        parts.append(cur)
    return parts


def build():
    chunks = []
    for l in open(W / "pages.jsonl", encoding="utf8"):
        x = json.loads(l); p = x["page"]
        for i, t in enumerate(split_text(x["text"])):
            chunks.append({"id": f"p{p:03d}:t{i}", "page": p, "kind": "text", "text": t})
        vf = W / "visual" / f"p{p:03d}.json"
        if vf.exists():
            v = json.loads(vf.read_text(encoding="utf8"))["text"].strip()
            if v and not v.startswith("NO_VISUAL"):
                for i in range(0, len(v), 2500):
                    chunks.append({"id": f"p{p:03d}:v{i//2500}", "page": p, "kind": "visual", "text": v[i:i + 2500]})
    return chunks


if __name__ == "__main__":
    chunks = build()
    json.dump(chunks, open(W / "chunks.json", "w", encoding="utf8"), ensure_ascii=False)
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    vecs = []
    for i in range(0, len(chunks), 100):
        r = client.embeddings.create(model=EMB, input=[c["text"][:6000] for c in chunks[i:i + 100]])
        vecs += [d.embedding for d in r.data]
    np.save(W / f"emb_{EMB}.npy", np.array(vecs, dtype=np.float32))
    from collections import Counter
    print(len(chunks), "chunks", Counter(c["kind"] for c in chunks), "emb", np.array(vecs).shape)
