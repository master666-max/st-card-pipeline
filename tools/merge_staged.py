# -*- coding: utf-8 -*-
"""阶段化条目合并器：把双态条目组并入角色卡内嵌书 / 独立世界书
输入：
  --staged     阶段化双态条目 JSON（列表，每条含 comment 标记库归属）
  --card       chara_card_v2 JSON（含 data.character_book.entries）
  --worldbook  ST 独立世界书 JSON（entries 为 {uid: entry} 字典）
拆分规则：comment 含 --own-marker（默认「专属」）→ 并入角色卡内嵌书；
          comment 含 --common-marker（默认「共通」）→ 并入独立世界书。
说明：角色隐私态（身份/秘密）放专属库（卡书只对该角色生效）；房间级事实态
（世界级事件 plant/payoff）放共通库（全局挂载，全体成员共享同一状态）。
用法示例见 README「快速开始」。
"""
import json, argparse, os


def load_items(path):
    d = json.load(open(path, encoding="utf-8"))
    return d if isinstance(d, list) else d.get("entries") or d.get("items")


def merge_card(card_path, items, markers, card_out, version, note):
    card = json.load(open(card_path, encoding="utf-8"))
    data = card["data"]
    cb = data["character_book"]
    uid = max(e.get("uid", i) for i, e in enumerate(cb["entries"])) + 1
    for it in items:
        e = dict(it)
        e.setdefault("uid", uid); uid += 1
        e.setdefault("enabled", True)
        e.setdefault("insertion_order", 100)
        cb["entries"].append(e)
    if version:
        data["character_version"] = version
    if note:
        xl = data["extensions"].setdefault("x_canonlay", {})
        if isinstance(xl, dict):
            xl["staged_merge"] = note
    json.dump(card, open(card_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"card: {len(cb['entries'])} entries -> {card_out}")


def merge_worldbook(wb_path, items, wb_out, note):
    wb = json.load(open(wb_path, encoding="utf-8"))
    es = wb["entries"]
    uid = max(int(k) for k in es.keys()) + 1
    for it in items:
        e = dict(it)
        e.setdefault("uid", uid)
        e.setdefault("key", e.get("keys", []))  # 独立世界书用 key，卡内书用 keys
        e.setdefault("content", e.get("content", ""))
        e.setdefault("constant", False)
        e.setdefault("disable", False)
        es[str(uid)] = e
        uid += 1
    if note:
        wb["description"] = (wb.get("description") or "") + "\n" + note
    json.dump(wb, open(wb_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"worldbook: {len(es)} entries -> {wb_out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--staged", required=True)
    ap.add_argument("--card", help="chara_card_v2 JSON（有专属条目时必给）")
    ap.add_argument("--worldbook", help="独立世界书 JSON（有共通条目时必给）")
    ap.add_argument("--card-out")
    ap.add_argument("--worldbook-out")
    ap.add_argument("--own-marker", default="专属")
    ap.add_argument("--common-marker", default="共通")
    ap.add_argument("--card-version")
    ap.add_argument("--card-note")
    ap.add_argument("--wb-note")
    a = ap.parse_args()
    items = load_items(a.staged)
    own = [it for it in items if a.own_marker in it.get("comment", "")]
    common = [it for it in items if a.common_marker in it.get("comment", "")]
    print(f"split: own+{len(own)} common+{len(common)}")
    if own:
        assert a.card and a.card_out, "--card/--card-out required for own entries"
        merge_card(a.card, own, a.own_marker, a.card_out, a.card_version, a.card_note)
    if common:
        assert a.worldbook and a.worldbook_out, "--worldbook/--worldbook-out required for common entries"
        merge_worldbook(a.worldbook, common, a.worldbook_out, a.wb_note)
    if not own and not common:
        raise SystemExit("no staged entries matched markers — check comment fields / marker args")


if __name__ == "__main__":
    main()
