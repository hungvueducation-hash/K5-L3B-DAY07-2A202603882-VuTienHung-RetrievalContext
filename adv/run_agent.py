"""Chạy agent trên 1 split với 1 cấu hình; lưu trace, chấm sơ bộ (judge model + kiểm tra trang trích dẫn). Nhãn cuối cùng do người đọc lại.
Dùng: python run_agent.py <config> <dev|test>
Agent chỉ nhận question; gold/expected_answer chỉ dùng SAU khi agent xong (chấm)."""
import json, re, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from rag import *

HERE = Path(__file__).parent
CONFIGS = {
    "A0_dense_text":      dict(r="dense",  model="gpt-4.1-mini", use_view=False),   # baseline: chỉ text + mô tả trực quan
    "A1_dense_view":      dict(r="dense",  model="gpt-4.1-mini", use_view=True),
    "A2_hybrid_view":     dict(r="hybrid", model="gpt-4.1-mini", use_view=True),
    "A3_hybrid_view_41":  dict(r="hybrid", model="gpt-4.1",      use_view=True),
    "A4_dense_view_41":   dict(r="dense",  model="gpt-4.1",      use_view=True),
}
JUDGE = """You grade an answer against a reference. Question: {q}\nReference answer: {ref}\nCandidate answer: {ans}\n
Reply with JSON {{"grade": "correct"|"partial"|"wrong", "reason": "..."}}.
correct = every fact/number in the reference is present and consistent (extra correct detail is fine; approximate chart values within the stated approximation are fine);
partial = some but not all required facts, or a wrong unit/condition; wrong = contradicts or misses the key facts or refuses."""


def pages_cited(cites):
    s = set()
    for c in cites:
        m = re.search(r"p?(\d{1,3})", c)
        if m: s.add(int(m.group(1)))
    return s


def judge(q, ans):
    r = client().chat.completions.create(model="gpt-4.1", temperature=0, response_format={"type": "json_object"},
        messages=[{"role": "user", "content": JUDGE.format(q=q["question"], ref=q["expected_answer"], ans=ans)}])
    return json.loads(r.choices[0].message.content)


def build(r, C):
    d, b = Dense(C), BM25(C)
    return {"dense": d, "bm25": b, "hybrid": Hybrid([d, b])}[r]


def one(args):
    q, cfg, C = args
    R = build(cfg["r"], C)
    try:
        res = run_agent(q["question"], R, C, model=cfg["model"], use_view=cfg["use_view"])
    except Exception as e:
        return {"query_id": q["id"], "status": "error", "error": repr(e)[:300], "citations": [], "events": [], "usage": {}}
    res["query_id"] = q["id"]
    cited = pages_cited(res["citations"])
    if q["answerable"]:
        gp = {g["page"] for g in q["gold"]}
        alt = {56} if q["id"] == "t12" else set()   # Figure 7 (p56) lặp lại Figure O.1
        res["gold_pages"] = sorted(gp)
        res["cites_all_gold_pages"] = gp <= cited or (q["id"] == "t12" and (cited & (gp | alt)) != set())
        res["evidence_seen"] = bool({g for g in gp if g in set(res["viewed_pages"]) or any(c["page"] == g for c in [C.by_id[i] for i in res["context_ids"]])} == gp)
        res["judge"] = judge(q, res["answer"]) if res["status"] == "answered" else {"grade": "wrong", "reason": "abstained"}
        res["pass_auto"] = res["status"] == "answered" and res["judge"]["grade"] == "correct" and res["cites_all_gold_pages"]
    else:
        res["pass_auto"] = res["status"] == "abstain"
    return res


if __name__ == "__main__":
    cname, split = sys.argv[1], sys.argv[2]
    cfg = CONFIGS[cname]
    Q = [q for q in json.load(open(HERE / "benchmark.json", encoding="utf8")) if q["split"] == split]
    C = Corpus()
    with ThreadPoolExecutor(4) as ex:
        traces = list(ex.map(one, [(q, cfg, C) for q in Q]))
    out = HERE / "results" / f"agent-{split}"; out.mkdir(parents=True, exist_ok=True)
    json.dump(traces, open(out / f"traces_{cname}.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    qd = {q["id"]: q for q in Q}
    ok = [t for t in traces if t["status"] != "error"]
    ans = [t for t in traces if qd[t["query_id"]]["answerable"]]
    cats = {}
    for t in traces:
        c = qd[t["query_id"]]["category"]; a = cats.setdefault(c, [0, 0]); a[1] += 1; a[0] += bool(t.get("pass_auto"))
    S = {"config": cname, "split": split, "cfg": cfg, "n": len(traces), "errors": len(traces) - len(ok),
         "pass_auto": f"{sum(1 for t in traces if t.get('pass_auto'))}/{len(traces)}", "by_category": {k: f"{v[0]}/{v[1]}" for k, v in cats.items()},
         "answerable_pass": f"{sum(1 for t in ans if t.get('pass_auto'))}/{len(ans)}",
         "tool_use": f"{sum(1 for t in ok if t['usage'].get('searches', 0) > 0)}/{len(ok)}", "avg_views": round(sum(t['usage'].get('views', 0) for t in ok) / max(1, len(ok)), 2),
         "seconds_total": round(sum(t["usage"].get("seconds", 0) for t in ok), 0), "cost_usd": round(sum(t["usage"].get("cost_usd", 0) for t in ok), 3)}
    json.dump(S, open(out / f"summary_{cname}.json", "w", encoding="utf8"), ensure_ascii=False, indent=1)
    print(json.dumps(S, ensure_ascii=False))
    for t in traces:
        if not t.get("pass_auto"):
            q = qd[t["query_id"]]
            print("FAIL", t["query_id"], q["category"], t["status"], "|", (t.get("answer") or t.get("error", ""))[:140].replace("\n", " "), "| cites", t.get("citations"), "gold", t.get("gold_pages"), "| judge", t.get("judge", {}).get("grade"))
