"""So sánh retrieval thuần trên benchmark nâng cao (query gốc, không LLM sinh query).
Hit@k = số câu có đáp án mà top-k chứa chunk thuộc ĐÚNG trang gold (multihop: Evidence Hit@k = đủ mọi trang gold).
Dùng: python retrieval_eval.py dev|test"""
import json, sys
from pathlib import Path
from rag import *

split = sys.argv[1]
Q = [q for q in json.load(open(Path(__file__).parent / "benchmark.json", encoding="utf8")) if q["split"] == split and q["answerable"]]
C = Corpus()
d, b = Dense(C), BM25(C)
M = {"dense": d, "bm25": b, "hybrid_rrf": Hybrid([d, b]), "dense_visual_only": Dense(C, {"visual"})}
res = {}
for name, m in M.items():
    row = {}
    for q in Q:
        gp = {g["page"] for g in q["gold"]}
        out = m.search(q["question"], 10)
        ranks = {g: min([c["rank"] for c in out if c["page"] == g] or [99]) for g in gp}
        row[q["id"]] = {"cat": q["category"], "need_rank": max(ranks.values()), "min_rank": min(ranks.values())}
    n = len(Q); f = lambda k: sum(1 for v in row.values() if v["need_rank"] <= k)
    g1 = sum(1 for v in row.values() if v["min_rank"] == 1)
    bycat = {c: f"{sum(1 for v in row.values() if v['cat']==c and v['need_rank']<=5)}/{sum(1 for v in row.values() if v['cat']==c)}" for c in sorted({v['cat'] for v in row.values()})}
    res[name] = {"hit@1(any gold page)": f"{g1}/{n}", "evidence_hit@3": f"{f(3)}/{n}", "evidence_hit@5": f"{f(5)}/{n}", "evidence_hit@10": f"{f(10)}/{n}", "by_cat@5": bycat, "per_question": row}
    print(split, f"{name:18s}", "Hit@1", res[name]["hit@1(any gold page)"], "EvHit@3", res[name]["evidence_hit@3"], "@5", res[name]["evidence_hit@5"], "@10", res[name]["evidence_hit@10"], bycat, flush=True)
Path(__file__).parent.joinpath("results").mkdir(exist_ok=True)
json.dump(res, open(Path(__file__).parent / "results" / f"retrieval_{split}.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
