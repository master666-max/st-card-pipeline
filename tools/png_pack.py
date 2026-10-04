# -*- coding: utf-8 -*-
"""SillyTavern 角色卡 PNG 打包与回读对账（v2/v3 双 chunk）
规格依据：SillyTavern v1.19.0 源码级（script.js 卡片导入：ccv3 chunk 优先于 chara）
- chara  chunk = base64( UTF-8 JSON of chara_card_v2 )
- ccv3   chunk = base64( UTF-8 JSON of chara_card_v3 )，ST 读取时 ccv3 优先
- 共享字段两份 JSON 必须一致（V3 = V2 data + group_only_greetings + assets）
用法：
  py -X utf8 png_pack.py dummy                 # 造占位图+哑卡自测（临时目录，无副作用）
  py -X utf8 png_pack.py pack <card.json> <img_out.png>
  py -X utf8 png_pack.py verify <card.json> <png>
"""
import sys, json, base64, struct, zlib, io, os, tempfile


def _chunk(ctype: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + ctype + data + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)


def make_placeholder(path: str, w=512, h=768):
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (w, h), (24, 28, 38))
    d = ImageDraw.Draw(img)
    for i in range(0, h, 24):  # 简单扫描线纹理，标识"占位"
        d.line([(0, i), (w, i)], fill=(30, 36, 50))
    d.rectangle([w // 2 - 70, h // 2 - 40, w // 2 + 70, h // 2 + 40], outline=(90, 160, 220), width=3)
    img.save(path, "PNG")


def v2_to_v3(v2: dict) -> dict:
    data = json.loads(json.dumps(v2["data"], ensure_ascii=False))
    data.setdefault("group_only_greetings", [])
    data.setdefault("assets", [])
    return {"spec": "chara_card_v3", "spec_version": "3.0", "data": data}


def embed(card_json_path: str, png_out: str, placeholder_if_missing=True):
    v2 = json.load(open(card_json_path, encoding="utf-8"))
    v3 = v2_to_v3(v2)
    payload_chara = base64.b64encode(json.dumps(v2, ensure_ascii=False).encode("utf-8"))
    payload_ccv3 = base64.b64encode(json.dumps(v3, ensure_ascii=False).encode("utf-8"))
    if os.path.exists(png_out):
        raw = open(png_out, "rb").read()
    elif placeholder_if_missing:
        buf = io.BytesIO()
        make_placeholder(buf)
        raw = buf.getvalue()
    else:
        raise FileNotFoundError(png_out)
    sig, rest = raw[:8], raw[8:]
    chunks, pos = [], 0
    while pos < len(rest):
        ln = struct.unpack(">I", rest[pos:pos + 4])[0]
        chunks.append(rest[pos:pos + 12 + ln]); pos += 12 + ln
    chunks = [c for c in chunks if not c[4:8] == b"tEXt" or not (b"chara" in c[:80] or b"ccv3" in c[:80])]
    out = [sig]
    for c in chunks:
        if c[4:8] == b"IEND":
            out.append(_chunk(b"tEXt", b"chara\x00" + payload_chara))
            out.append(_chunk(b"tEXt", b"ccv3\x00" + payload_ccv3))
        out.append(c)
    open(png_out, "wb").write(b"".join(out))
    print(f"packed: {png_out} ({os.path.getsize(png_out)} bytes, chara={len(payload_chara)}b64, ccv3={len(payload_ccv3)}b64)")


def extract(png_path: str):
    raw = open(png_path, "rb").read()[8:]
    got = {}
    pos = 0
    while pos < len(raw):
        ln = struct.unpack(">I", raw[pos:pos + 4])[0]
        ctype = raw[pos + 4:pos + 8]
        data = raw[pos + 8:pos + 8 + ln]
        if ctype == b"tEXt":
            kw, _, txt = data.partition(b"\x00")
            if kw in (b"chara", b"ccv3"):
                got[kw.decode()] = json.loads(base64.b64decode(txt).decode("utf-8"))
        pos += 12 + ln
        if ctype == b"IEND":
            break
    return got


def verify(card_json_path: str, png_path: str):
    v2 = json.load(open(card_json_path, encoding="utf-8"))
    v3 = v2_to_v3(v2)
    got = extract(png_path)
    ok = []
    ok.append(("chara==V2", got.get("chara") == v2))
    ok.append(("ccv3==V3", got.get("ccv3") == v3))
    # 共享字段逐字一致
    shared = True
    g2, g3 = got.get("chara", {}).get("data", {}), got.get("ccv3", {}).get("data", {})
    for k, v in g2.items():
        if k in ("group_only_greetings", "assets"):
            continue
        if g3.get(k) != v:
            shared = False
            print("  shared-field diff:", k)
    ok.append(("shared-fields-identical", shared))
    for name, passed in ok:
        print(("PASS " if passed else "FAIL ") + name)
    return all(p for _, p in ok)


def dummy():
    d = tempfile.mkdtemp(prefix="png_pack_dummy_")
    card = {"spec": "chara_card_v2", "spec_version": "2.0", "data": {
        "name": "DUMMY", "description": "测试", "personality": "", "scenario": "",
        "first_mes": "", "mes_example": "", "creator_notes": "", "system_prompt": "",
        "post_history_instructions": "", "alternate_greetings": [], "tags": [], "creator": "", "character_version": "0.1",
        "extensions": {}, "character_book": {"name": "t", "entries": []}}}
    cp = os.path.join(d, "_dummy_card.json")
    json.dump(card, open(cp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    pp = os.path.join(d, "_dummy.png")
    embed(cp, pp)
    ok = verify(cp, pp)
    print("DUMMY ROUNDTRIP:", "OK" if ok else "BROKEN")
    return ok


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "dummy"
    if cmd == "dummy":
        sys.exit(0 if dummy() else 1)
    elif cmd == "pack":
        embed(sys.argv[2], sys.argv[3])
    elif cmd == "verify":
        sys.exit(0 if verify(sys.argv[2], sys.argv[3]) else 1)
