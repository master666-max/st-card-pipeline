# -*- coding: utf-8 -*-
"""ST 聊天记录漂移量化器（动态面判卷用）
输入：SillyTavern 聊天导出 JSONL（每行一条消息，含 mes / is_user / name）。
做什么：1) is_user 区分双方 2) 剥 HTML 状态栏取正文 3) 可选全文落盘 4) 漂移量化
（逐角色消息轮次输出：均句长 / 语气词每百字 / 省略号 / 自定义签名词计数）。
签名词与关键轮次均可经参数注入，不写死任何角色。
用法：
  py -X utf8 chat_drift.py --src <chat.jsonl> [--out 报告.md] [--sig 诶,拜托,不是么] [--key-turns 10,16,18]
"""
import json, re, argparse, os

DEFAULT_PART = list("呢吧啊嘛哦诶呀啦哟嗯")


def strip_html(t):
    t = re.sub(r"<div[^>]*>.*?</div>", "", t, flags=re.S)   # 状态栏/氛围框
    t = re.sub(r"<[^>]+>", "", t)                            # 残留标签
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def make_stats(sigs):
    def stats(text):
        sents = [s for s in re.split(r"[。！？\n]", text) if s.strip()]
        chars = len(text)
        return {
            "n_sent": len(sents),
            "avg_sent": round(chars / max(len(sents), 1), 1),
            "part100": round(sum(text.count(p) for p in DEFAULT_PART) * 100 / max(chars, 1), 2),
            "ell": text.count("……"),
            **{f"sig_{s}": text.count(s) for s in sigs},
        }
    return stats


def load_messages(src):
    msgs = []
    for l in open(src, encoding="utf-8"):
        if not l.strip():
            continue
        d = json.loads(l)
        if d.get("mes") is None:
            continue
        body = strip_html(d["mes"])
        msgs.append({"i": len(msgs), "who": "USER" if d.get("is_user", False) else "CHAR",
                     "name": d.get("name", "?"), "chars": len(body), "body": body})
    return msgs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="ST 聊天 JSONL")
    ap.add_argument("--out", help="全文 Markdown 落盘路径（可选）")
    ap.add_argument("--sig", default="诶,拜托,不是么", help="逗号分隔的签名词")
    ap.add_argument("--key-turns", default="", help="逗号分隔的关键轮次号（打印全文用）")
    a = ap.parse_args()
    sigs = [s for s in a.sig.split(",") if s]
    stats = make_stats(sigs)
    msgs = load_messages(a.src)
    for m in msgs:
        m["stats"] = stats(m["body"]) if m["who"] == "CHAR" else None

    if a.out:
        md = ["# 实聊记录解析", ""]
        for m in msgs:
            md.append(f"### [{m['i']}] {m['who']} ({m['chars']}字)")
            md.append(m["body"])
            md.append("")
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        open(a.out, "w", encoding="utf-8").write("\n".join(md))

    print("总消息:", len(msgs), "| USER:", sum(1 for m in msgs if m['who'] == 'USER'),
          "| CHAR:", sum(1 for m in msgs if m['who'] == 'CHAR'))
    print("\n== 角色消息漂移曲线（轮次: 均句长/语气词每百字/……/" + "/".join(sigs) + "）==")
    for m in msgs:
        if m["who"] != "CHAR":
            continue
        s = m["stats"]
        sigs_str = " ".join(f"{s[f'sig_{x}']}" for x in sigs)
        print(f"[{m['i']:02d}] {m['chars']:4d}字 均句{s['avg_sent']:5.1f} 语气{s['part100']:5.2f} ……{s['ell']:2d} {sigs_str}")

    if a.key_turns:
        print("\n== 关键轮全文 ==")
        for i in [int(x) for x in a.key_turns.split(",") if x.strip()]:
            m = msgs[i]
            print(f"\n--- [{i}] {m['who']} ---")
            print(m["body"][:700])


if __name__ == "__main__":
    main()
