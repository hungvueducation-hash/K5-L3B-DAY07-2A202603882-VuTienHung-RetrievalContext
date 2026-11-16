"""Chạy agent thật trên một split với một cấu hình. Lưu trace + chỉ số tự động (retrieval/context/tool use/chi phí).
Chấm grounded answer, citation support, abstention là bước THỦ CÔNG (xem review.py) — script không tự chấm.

Dùng: python src/run_agent_benchmark.py <config> <split>
"""
import json, sys, time
from common import DATA, RESULTS
from retrievers import *
from agent import run_agent


def build(name):
    d, b = DenseRetriever(), BM25Retriever()
    ml = MultilingualDense()
    R = {"dense": d, "bm25": b, "hybrid_rrf": HybridRetriever(d, b), "dense_multilingual": ml,
         "hybrid_ml_rrf": HybridRetriever(ml, b, name="hybrid_ml_rrf"), "hybrid3_rrf": HybridRetriever(d, ml, b, name="hybrid3_rrf")}
    return R[name]


# Mỗi cấu hình: retriever + tham số agent. top_k/budget/max_searches ghi trong trace.
CONFIGS = {
    "base_dense":      dict(r="dense", top_k=3, budget=1500, max_searches=3),                         # baseline Day 6 + agent
    "bm25":            dict(r="bm25", top_k=3, budget=1500, max_searches=3),
    "hybrid":          dict(r="hybrid_rrf", top_k=3, budget=1500, max_searches=3),
    "hybrid_k5":       dict(r="hybrid_rrf", top_k=5, budget=2800, max_searches=3),
    "hybrid_ml":       dict(r="hybrid_ml_rrf", top_k=3, budget=1500, max_searches=3),
    "hybrid3":         dict(r="hybrid3_rrf", top_k=3, budget=1500, max_searches=3),
    "hybrid3_k5":      dict(r="hybrid3_rrf", top_k=5, budget=2800, max_searches=3),
    "hybrid3_k5_rw":   dict(r="hybrid3_rrf", top_k=5, budget=2800, max_searches=3, rewrite_hint=True),
}

if __name__ == "__main__":
    cfg_name, split = sys.argv[1], sys.argv[2]
    cfg = dict(CONFIGS[cfg_name]); retr = build(cfg.pop("r"))
    qs = [q for q in json.load(open(DATA / "questions.json", encoding="utf8")) if q["split"] == split]
    out_dir = RESULTS / f"agent-{split}"; out_dir.mkdir(parents=True, exist_ok=True)
    traces = []
    for q in qs:
        try:
            # Agent chỉ nhận question + filter do người dùng cung cấp; KHÔNG nhận gold/expected_answer.
            res = run_agent(q["question"], retr, filters=q.get("filter"), **cfg)
        except Exception as e:   # lỗi model/vector store ghi riêng, không thay bằng kết quả giả
            res = {"status": "error", "error": repr(e)[:300], "events": [], "citations": [], "context_ids": [], "usage": {}}
        res["query_id"] = q["id"]; res["config"] = cfg_name
        # chỉ số tự động (dùng gold SAU khi agent chạy xong)
        by_id = {c["id"]: c for c in retr.chunks} if hasattr(retr, "chunks") else {c["id"]: c for c in load_chunks()}
        ctx = [by_id[i] for i in res["context_ids"]]
        if q.get("answerable", True):
            need = q.get("gold_all") or None
            res["context_has_evidence"] = (all(any(is_hit(c, [g]) for c in ctx) for g in need) if need else any(is_hit(c, q["gold"]) for c in ctx))
            ev = [e for e in res["events"] if e.get("event") == "search"]
            res["first_query_hit"] = [bool(ev and any(is_hit(by_id[r["id"]], q["gold"]) for r in ev[0]["results"][:3]))]
        traces.append(res)
        u = res.get("usage", {})
        print(q["id"], res["status"], "searches", u.get("searches"), "ctxEv", res.get("context_has_evidence"), flush=True)
    json.dump(traces, open(out_dir / f"traces_{cfg_name}.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    ok = [t for t in traces if t["status"] != "error"]
    ans = [q for q in qs if q.get("answerable", True)]
    summ = {"config": cfg_name, "split": split, "params": CONFIGS[cfg_name], "model": "gpt-4o-mini",
            "n_run_ok": len(ok), "n_error": len(traces) - len(ok),
            "context_evidence": f"{sum(1 for t in traces if t.get('context_has_evidence'))}/{len(ans)}",
            "first_query_hit@3": f"{sum(1 for t in traces if t.get('first_query_hit', [False])[0])}/{len(ans)}",
            "tool_use": f"{sum(1 for t in ok if t['usage'].get('searches', 0) > 0)}/{len(ok)}",
            "searches_distribution": {str(k): sum(1 for t in ok if t['usage'].get('searches') == k) for k in range(0, 5)},
            "answered": sum(1 for t in ok if t["status"] == "answered"), "abstain": sum(1 for t in ok if t["status"] == "abstain"),
            "seconds": round(sum(t["usage"].get("seconds", 0) for t in ok), 1),
            "cost_usd": round(sum(t["usage"].get("cost_usd", 0) for t in ok), 4)}
    json.dump(summ, open(out_dir / f"summary_{cfg_name}.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(json.dumps(summ, ensure_ascii=False))
