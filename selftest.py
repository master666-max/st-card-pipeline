# -*- coding: utf-8 -*-
"""发布自测门：编译全部工具 + 四件工具在合成数据上真实跑通。
用法：py -X utf8 selftest.py
任何一项失败退出码非 0。全部使用临时目录与合成数据，不依赖任何上游语料。
"""
import py_compile, json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.join(HERE, "tools")
PY = sys.executable or "py"
FAILED = []


def run(args, **kw):
    r = subprocess.run([PY, "-X", "utf8"] + args, capture_output=True, text=True, encoding="utf-8", **kw)
    return r


def check(name, r, expect_zero=True, must_contain=()):
    ok = (r.returncode == 0) == expect_zero and all(m in (r.stdout + r.stderr) for m in must_contain)
    print(("PASS " if ok else "FAIL ") + name)
    if not ok:
        FAILED.append(name)
        print("  stdout:", r.stdout[-800:])
        print("  stderr:", r.stderr[-800:])


def t_compile(tmp):
    for f in os.listdir(TOOLS):
        if f.endswith(".py"):
            py_compile.compile(os.path.join(TOOLS, f), cfile=os.path.join(tmp, f + ".pyc"), doraise=True)
    print("PASS compile-all (6 tools)")
    return True


def t_png_pack(tmp):
    r = run([os.path.join(TOOLS, "png_pack.py"), "dummy"])
    check("png_pack dummy roundtrip", r, must_contain=("PASS chara==V2", "PASS ccv3==V3", "PASS shared-fields-identical", "DUMMY ROUNDTRIP: OK"))
    return r


def t_pair_cluster(tmp):
    src = os.path.join(tmp, "rel"); os.makedirs(src, exist_ok=True)
    recs = [
        {"record_id": "r1", "canonical": {"subject": "甲", "rel_type": "同门", "object": "乙"}, "evidence": [{"chapter": 3, "quote": "q1"}]},
        {"record_id": "r2", "canonical": {"subject": "乙", "rel_type": "挚友", "object": "甲", "claim": False}, "evidence": [{"chapter": 9, "quote": "q2"}]},
        {"record_id": "r3", "canonical": {"subject": "丙", "rel_type": "宿敌", "object": "甲"}, "evidence": [{"chapter": 5, "quote": "q3"}]},
    ]
    for i, d in enumerate(recs):
        json.dump(d, open(os.path.join(src, f"{i}.json"), "w", encoding="utf-8"), ensure_ascii=False)
    out = os.path.join(tmp, "cluster_out")
    r = run([os.path.join(TOOLS, "pair_cluster.py"), "--src", src, "--outdir", out])
    ok = r.returncode == 0
    if ok:
        d = json.load(open(os.path.join(out, "relation_clusters.json"), encoding="utf-8"))
        ok = d["n_pairs"] == 2 and d["n_multi"] == 1
    print(("PASS " if ok else "FAIL ") + "pair_cluster synthetic (n_pairs==2, multi==1)")
    if not ok:
        FAILED.append("pair_cluster"); print("  stdout:", r.stdout[-500:], r.stderr[-500:])


def t_merge_staged(tmp):
    card = {"spec": "chara_card_v2", "spec_version": "2.0", "data": {
        "name": "DEMO", "character_book": {"name": "demo", "entries": [
            {"uid": 0, "keys": ["demo"], "content": "base", "enabled": True, "insertion_order": 10}]},
        "extensions": {}}}
    wb = {"entries": {"0": {"uid": 0, "key": ["world"], "content": "base world", "comment": "base"}},
          "name": "demo_common"}
    cp = os.path.join(tmp, "card.json"); wp = os.path.join(tmp, "wb.json")
    json.dump(card, open(cp, "w", encoding="utf-8"), ensure_ascii=False)
    json.dump(wb, open(wp, "w", encoding="utf-8"), ensure_ascii=False)
    ex = os.path.join(HERE, "examples", "staged_entries_example.json")
    r = run([os.path.join(TOOLS, "merge_staged.py"), "--staged", ex, "--card", cp, "--worldbook", wp,
             "--card-out", os.path.join(tmp, "card_v2.json"), "--worldbook-out", os.path.join(tmp, "wb_v2.json"),
             "--card-version", "0.2", "--card-note", "merged staged identity", "--wb-note", "merged staged event"])
    ok = r.returncode == 0
    if ok:
        c = json.load(open(os.path.join(tmp, "card_v2.json"), encoding="utf-8"))
        w = json.load(open(os.path.join(tmp, "wb_v2.json"), encoding="utf-8"))
        ok = (len(c["data"]["character_book"]["entries"]) == 3
              and c["data"]["character_version"] == "0.2"
              and len(w["entries"]) == 3
              and any("staged_merge" in c["data"].get("extensions", {}).get("x_canonlay", {}) for _ in [0]))
    print(("PASS " if ok else "FAIL ") + "merge_staged synthetic (card 1+2, wb 1+2, version bump)")
    if not ok:
        FAILED.append("merge_staged"); print("  stdout:", r.stdout[-500:], r.stderr[-500:])


def t_chat_drift(tmp):
    chat = os.path.join(tmp, "chat.jsonl")
    rows = [
        {"mes": "你好呀。", "is_user": True, "name": "user"},
        {"mes": "<div>Status</div>嗯……你来啦。诶，要一起走吗？", "is_user": False, "name": "DEMO"},
        {"mes": "拜托了，别丢下我。不是么，你答应过的……", "is_user": False, "name": "DEMO"},
    ]
    open(chat, "w", encoding="utf-8").write("\n".join(json.dumps(x, ensure_ascii=False) for x in rows))
    r = run([os.path.join(TOOLS, "chat_drift.py"), "--src", chat, "--out", os.path.join(tmp, "chat.md"),
             "--sig", "诶,拜托,不是么", "--key-turns", "1"])
    check("chat_drift synthetic (3 msgs, drift curve)", r, must_contain=("总消息: 3", "USER: 1", "CHAR: 2"))


def t_scan_privacy(tmp):
    # 测试向量运行时拼装——避免触发扫描门自身（门对本文件保持严格）
    fake_forbid = "示例禁词" + "XYZ"
    fake_mail = "a" + "@" + "b." + "com"
    r = run([os.path.join(TOOLS, "scan_privacy.py"), HERE, "--forbid", fake_forbid])
    check("scan_privacy zero-hit on repo tree", r, must_contain=("命中: 0",))
    bad = os.path.join(tmp, "bad"); os.makedirs(bad, exist_ok=True)
    open(os.path.join(bad, "leak.txt"), "w", encoding="utf-8").write("mail me at " + fake_mail)
    r2 = run([os.path.join(TOOLS, "scan_privacy.py"), bad])
    check("scan_privacy catches leak (exit 1)", r2, expect_zero=False, must_contain=("邮箱",))


def main():
    tmp = tempfile.mkdtemp(prefix="stcard_selftest_")
    print("selftest workdir:", tmp, "\n")
    t_compile(tmp)
    t_png_pack(tmp)
    t_pair_cluster(tmp)
    t_merge_staged(tmp)
    t_chat_drift(tmp)
    t_scan_privacy(tmp)
    print("\n" + ("ALL PASS" if not FAILED else "FAILED: " + ", ".join(FAILED)))
    sys.exit(0 if not FAILED else 1)


if __name__ == "__main__":
    main()
