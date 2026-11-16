"""So sánh retrieval thuần (query gốc, không LLM) trên cùng câu hỏi/filter: Hit@1, Evidence Hit@3, Recall@10, MRR@10."""
import json, sys, time
from common import DATA, RESULTS
from retrievers import *


def methods():
    d, b = DenseRetriever(), BM25Retriever()
    ms = {"dense": d, "bm25_syllable": BM25Retriever(bigram=False), "bm25": b, "hybrid_rrf": HybridRetriever(d, b)}
    try:
        ml = MultilingualDense()
        ms["dense_multilingual"] = ml
        ms["hybrid_ml_rrf"] = HybridRetriever(ml, b, name="hybrid_ml_rrf")
        ms["hybrid3_rrf"] = HybridRetriever(d, ml, b, name="hybrid3_rrf")
    except Exception as e:
        print("Bỏ qua embedding đa ngữ:", repr(e)[:300])
    return ms


if __name__ == "__main__":
    split = sys.argv[1] if len(sys.argv) > 1 else "dev"
    only = sys.argv[2].split(",") if len(sys.argv) > 2 else None
    qs = [q for q in json.load(open(DATA / "questions.json", encoding="utf8")) if q["split"] == split and q.get("answerable", True)]
    out = {}
    for name, m in methods().items():
        if only and name not in only:
            continue
        t = time.time(); rows = []
        for q in qs:
            res = m.search(q["question"], q.get("filter"), 10)
            ranks = [r["rank"] for r in res if is_hit(r, q["gold"])]
            rows.append({"id": q["id"], "first_hit_rank": min(ranks) if ranks else None, "top3": [r["id"] for r in res[:3]]})
        n = len(rows)
        f = lambda k: sum(1 for r in rows if r["first_hit_rank"] and r["first_hit_rank"] <= k)
        out[name] = {"n": n, "hit@1": f"{f(1)}/{n}", "hit@3": f"{f(3)}/{n}", "recall@10": f"{f(10)}/{n}",
                     "mrr@10": round(sum(1 / r["first_hit_rank"] for r in rows if r["first_hit_rank"]) / n, 3),
                     "sec": round(time.time() - t, 2), "per_question": rows}
        o = out[name]
        print(f"{split} {name:20s} Hit@1 {o['hit@1']:6s} Hit@3 {o['hit@3']:6s} R@10 {o['recall@10']:6s} MRR {o['mrr@10']}  {o['sec']}s")
    RESULTS.mkdir(exist_ok=True)
    json.dump(out, open(RESULTS / f"retrieval_{split}.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
