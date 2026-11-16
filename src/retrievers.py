"""Các phương pháp retrieval Day 7. Mọi phương pháp dùng cùng corpus (129 chunk Day 6, bảng chunks_b),
cùng filter do người dùng cung cấp (mien/section) và trả cùng định dạng kết quả."""
import json, math, re, unicodedata
from collections import Counter
import numpy as np
import psycopg
from common import DATA, TABLE, EMBED_MODEL, db_url

_emb = {}


def get_embedder(name=EMBED_MODEL):
    if name not in _emb:
        from sentence_transformers import SentenceTransformer
        _emb[name] = SentenceTransformer(name)
    return _emb[name]


def load_chunks():
    return json.load(open(DATA / "chunks.json", encoding="utf8"))


def pass_filter(c, filters):
    return all(c["metadata"].get(k) == v for k, v in (filters or {}).items())


def tok(text, bigram=True):
    syl = re.findall(r"\w+", unicodedata.normalize("NFC", text).casefold())
    return syl + ([a + "_" + b for a, b in zip(syl, syl[1:])] if bigram else [])


class DenseRetriever:
    """Dense: embedding Day 6 (all-MiniLM-L6-v2, 384 chiều) + pgvector cosine, filter bằng SQL."""
    name = "dense"

    def search(self, query, filters=None, top_k=3):
        qv = get_embedder().encode([query], normalize_embeddings=True)[0].tolist()
        where, params = "", [str(qv)]
        if filters:
            where = "WHERE " + " AND ".join(f"{k} = %s" for k in filters)
            params += list(filters.values())
        params += [str(qv), top_k]
        sql = f"""SELECT chunk_id,text,document_id,source,page,section,mien,metadata,embedding <=> %s AS d
                  FROM {TABLE} {where} ORDER BY embedding <=> %s LIMIT %s"""
        with psycopg.connect(db_url()) as c:
            rows = c.execute(sql, params).fetchall()
        return [{"id": r[0], "text": r[1], "source_id": r[2], "source": r[3], "page": r[4],
                 "metadata": {**(r[7] or {}), "section": r[5], "mien": r[6]}, "score": 1 - float(r[8]), "rank": i + 1,
                 "method": self.name} for i, r in enumerate(rows)]


class BM25Retriever:
    """Lexical: BM25 (k1=1.5, b=0.75), tách từ = âm tiết + bigram âm tiết liền kề (xấp xỉ từ ghép tiếng Việt)."""

    def __init__(self, bigram=True, k1=1.5, b=0.75):
        self.name = "bm25" if bigram else "bm25_syllable"
        self.bigram, self.k1, self.b = bigram, k1, b
        self.chunks = load_chunks()
        self.tf = [Counter(tok(c["text"], bigram)) for c in self.chunks]
        self.len = np.array([sum(t.values()) for t in self.tf], float)
        self.avg = self.len.mean()
        df = Counter(w for t in self.tf for w in t)
        n = len(self.chunks)
        self.idf = {w: math.log(1 + (n - d + .5) / (d + .5)) for w, d in df.items()}

    def scores(self, query):
        q = tok(query, self.bigram)
        s = np.zeros(len(self.chunks))
        for i, t in enumerate(self.tf):
            norm = self.k1 * (1 - self.b + self.b * self.len[i] / self.avg)
            for w in q:
                if w in t:
                    s[i] += self.idf[w] * t[w] * (self.k1 + 1) / (t[w] + norm)
        return s

    def search(self, query, filters=None, top_k=3):
        s = self.scores(query)
        order = [i for i in np.argsort(-s, kind="stable") if s[i] > 0 and pass_filter(self.chunks[i], filters)][:top_k]
        return [{**self.chunks[i], "score": float(s[i]), "rank": r + 1, "method": self.name} for r, i in enumerate(order)]


class HybridRetriever:
    """Hybrid: RRF (k=60) trộn thứ hạng của các retriever con (lấy mỗi bên `pool` ứng viên)."""

    def __init__(self, *parts, pool=20, k=60, name="hybrid_rrf"):
        self.parts, self.pool, self.k, self.name = parts, pool, k, name

    def search(self, query, filters=None, top_k=3):
        fused, store = Counter(), {}
        for p in self.parts:
            for r in p.search(query, filters, self.pool):
                fused[r["id"]] += 1 / (self.k + r["rank"])
                store[r["id"]] = r
        top = sorted(fused, key=lambda i: (-fused[i], i))[:top_k]
        return [{**store[i], "score": fused[i], "rank": n + 1, "method": self.name} for n, i in enumerate(top)]


class MultilingualDense:
    """Dense với embedding đa ngữ (index MỚI trong bộ nhớ, cache .npy) — thử nghiệm đổi embedding model."""

    def __init__(self, model="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", name="dense_multilingual"):
        self.name, self.model = name, model
        self.chunks = load_chunks()
        cache = DATA / f"emb_{model.split('/')[-1]}.npy"
        if cache.exists():
            self.m = np.load(cache)
        else:
            self.m = get_embedder(model).encode([c["text"] for c in self.chunks], normalize_embeddings=True, batch_size=32)
            np.save(cache, self.m)

    def search(self, query, filters=None, top_k=3):
        q = get_embedder(self.model).encode([query], normalize_embeddings=True)[0]
        s = self.m @ q
        order = [i for i in np.argsort(-s) if pass_filter(self.chunks[i], filters)][:top_k]
        return [{**self.chunks[i], "score": float(s[i]), "rank": r + 1, "method": self.name} for r, i in enumerate(order)]


def is_hit(chunk, gold):
    return any(chunk["source_id"] == g["source_id"] and chunk["page"] == g["page"] and g["evidence"] in chunk["text"] for g in gold)
