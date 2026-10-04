# -*- coding: utf-8 -*-
"""实体对聚簇器 v0：关系断言目录 → 无向对关系簇库
输入：一个目录下的正典 relation 记录 JSON（schema：record_id / canonical{subject,rel_type,object,claim} / evidence[{chapter,quote}]）
输出：relation_clusters.json（全簇索引）+ 关系簇概览.md（Top30 表）
聚类口径：无向对聚簇（方向语义保留在 records 内）；强度 = 记录数 + 章跨度*0.5（简易版，有权威关系 tier 时可替换强度函数）。
用法：
  py -X utf8 pair_cluster.py --src <relation记录目录> --outdir <输出目录>
"""
import os, json, argparse, collections


def load_records(src_dir):
    for fn in sorted(os.listdir(src_dir)):
        if not fn.endswith(".json"):
            continue
        d = json.load(open(os.path.join(src_dir, fn), encoding="utf-8"))
        yield d


def cluster(src_dir):
    clusters = collections.OrderedDict()
    for d in load_records(src_dir):
        c = d.get("canonical", {})
        s, o = c.get("subject", "?"), c.get("object", "?")
        pair = tuple(sorted((s, o)))
        ev = (d.get("evidence") or [{}])[0]
        rec = {
            "record_id": d.get("record_id", "?"), "subject": s, "object": o,
            "rel_type": c.get("rel_type", "?"), "claim": bool(c.get("claim", False)),
            "chapter": ev.get("chapter"), "quote": (ev.get("quote") or "")[:60],
        }
        e = clusters.setdefault(pair, {"pair": list(pair), "records": [], "chapters": set()})
        e["records"].append(rec)
        if ev.get("chapter"):
            e["chapters"].add(ev["chapter"])
    ranked = []
    for e in clusters.values():
        e["n"] = len(e["records"])
        chs = sorted(e["chapters"])
        e["chapter_range"] = [chs[0], chs[-1]] if chs else None
        e["span"] = (chs[-1] - chs[0] + 1) if chs else 0
        del e["chapters"]
        e["strength"] = e["n"] + e["span"] * 0.5
        e["pos"] = sum(1 for r in e["records"] if r["claim"])
        e["neg"] = e["n"] - e["pos"]
        e["rel_types"] = sorted({r["rel_type"] for r in e["records"]})
        ranked.append(e)
    ranked.sort(key=lambda x: -x["strength"])
    return ranked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="relation 记录 JSON 所在目录")
    ap.add_argument("--outdir", default="out", help="输出目录（默认 ./out）")
    ap.add_argument("--top", type=int, default=30, help="概览表显示前 N 对")
    a = ap.parse_args()
    ranked = cluster(a.src)
    out = {
        "口径": "无向对聚簇（方向语义保留在 records 内）；强度=记录数+章跨度*0.5（简易版）",
        "n_pairs": len(ranked), "n_multi": sum(1 for e in ranked if e["n"] > 1),
        "clusters": ranked,
    }
    os.makedirs(a.outdir, exist_ok=True)
    jp = os.path.join(a.outdir, "relation_clusters.json")
    json.dump(out, open(jp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    md = ["# 关系簇概览（实体对聚簇 v0）", "",
          f"- {sum(e['n'] for e in ranked)} 条关系 → **{len(ranked)} 对**，多关系对 **{out['n_multi']}**", "",
          "| # | 实体对 | 记录数 | 章跨度 | 正/反 | rel_type 样例 |", "|---|---|---|---|---|---|"]
    for i, e in enumerate(ranked[:a.top], 1):
        rt = "、".join(e["rel_types"][:3]) + ("…" if len(e["rel_types"]) > 3 else "")
        md.append(f"| {i} | {' ↔ '.join(e['pair'])} | {e['n']} | {e['span']} | {e['pos']}/{e['neg']} | {rt[:50]} |")
    open(os.path.join(a.outdir, "关系簇概览.md"), "w", encoding="utf-8").write("\n".join(md))

    print("pairs:", len(ranked), "| multi:", out["n_multi"])
    for e in ranked[:5]:
        print(f"  {' ↔ '.join(e['pair'])}: {e['n']} 条, 跨 {e['span']} 章")


if __name__ == "__main__":
    main()
