# -*- coding: utf-8 -*-
"""双态判卷匿名化：把候选卡随机分配甲/乙标签（映射留档，判卷侧禁读）
目的：判卷者只看「甲/乙」两份文件，避免知道哪个是修复版/候选版而产生偏好。
纪律：映射文件与判卷提示词物理隔离；判卷结束前不向判卷侧披露映射。
用法：
  py -X utf8 anonymize_cards.py --dir <卡目录> --cards a.json,b.json [--seed 20261001] --mapping-out 映射.json
输出：<dir>/判卷-甲.json、<dir>/判卷-乙.json（内容与原卡逐字一致）+ 映射文件。
"""
import json, random, argparse, os


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--cards", required=True, help="逗号分隔的两份（或以上）卡文件名")
    ap.add_argument("--labels", default="甲,乙")
    ap.add_argument("--seed", type=int, default=20261001)
    ap.add_argument("--mapping-out", required=True)
    a = ap.parse_args()
    cards = [c.strip() for c in a.cards.split(",") if c.strip()]
    labels = [l.strip() for l in a.labels.split(",") if l.strip()]
    assert len(labels) >= len(cards), "labels must cover all cards"
    random.seed(a.seed)
    random.shuffle(labels)
    mapping = dict(zip(cards, labels[:len(cards)]))
    for src, lab in mapping.items():
        d = json.load(open(os.path.join(a.dir, src), encoding="utf-8"))
        out = os.path.join(a.dir, f"判卷-{lab}.json")
        json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{src} -> 判卷-{lab}.json")
    json.dump(mapping, open(a.mapping_out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("mapping saved:", a.mapping_out)


if __name__ == "__main__":
    main()
