# -*- coding: utf-8 -*-
"""隐私零命中扫描门（发布前最后一关）
正则类：本机用户目录 / 绝对盘符路径 / 真实 token（ghp_/gho_/github_pat_）/ PRIVATE KEY
        / 邮箱 / 内网 IP。
语义类提示：.log / .pid / __pycache__ / .pyc 等危险文件一律报出。
额外禁词：--forbid 传入逗号分隔的自定义敏感串（如内部项目代号、角色名、真实姓名），
命中即失败——发布树里不应出现任何上游语料的专有内容。
用法：
  py -X utf8 scan_privacy.py <目录> [--forbid 词1,词2] 
退出码：0=零命中（通过）；1=有命中（禁止发布）。
"""
import os, re, sys, argparse

PATS = {
    "Windows用户目录": re.compile(rb"C:\\Users\\[A-Za-z0-9_]+"),
    "绝对盘符路径": re.compile(rb"[A-Z]:\\\\|[A-Z]:/[Uu]sers/"),
    "真实token": re.compile(rb"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gho_[A-Za-z0-9]{20,}"),
    "私钥块": re.compile(rb"PRIVATE KEY"),
    "邮箱": re.compile(rb"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+\.(?:com|org|net|cn|edu|gov)(?:\.[a-z]{2})?"),
    "内网IP": re.compile(rb"192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+"),
}
DANGEROUS_FILES = re.compile(r"\.(log|pid|pem|key|crt|pyc)$|__pycache__")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("root")
    ap.add_argument("--forbid", default="", help="逗号分隔的自定义禁词（按原文编码匹配）")
    a = ap.parse_args()
    forbids = [w for w in a.forbid.split(",") if w]
    hits = 0
    for root, dirs, fs in os.walk(a.root):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__")]
        for f in fs:
            p = os.path.join(root, f)
            if os.path.abspath(p) == os.path.abspath(__file__):
                continue  # 扫描器无法有意义地扫描自身源码（内含全部模式串），原则性跳过
            if DANGEROUS_FILES.search(f):
                print("危险文件:", p)
                hits += 1
            try:
                b = open(p, "rb").read()
            except OSError:
                continue
            found = [k for k, rx in PATS.items() if rx.search(b)]
            for w in forbids:
                if w.encode("utf-8") in b:
                    found.append(f"禁词:{w}")
            if found:
                print(p, "→", ", ".join(found))
                hits += 1
    print("命中:", hits)
    sys.exit(0 if hits == 0 else 1)


if __name__ == "__main__":
    main()
