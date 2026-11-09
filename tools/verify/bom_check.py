#!/usr/bin/env python3
"""VER-05：BOM（部品表）のチェック。

使い方：python tools/verify/bom_check.py build/hw/components.json [--strict] [--offline]

- 手はんだの部品（Assembly=HAND）は購入先（Supplier）があるかだけを見る
- JLC で実装する部品は LCSC 番号が必要。"TODO" は未決定として数える（--strict ならエラー）
- JLC の部品検索 API で、区分（Basic / Preferred / Extended）と在庫を調べる
  （結果は build/jlc_cache.json に 1 日保存。--offline ならキャッシュだけを使う）
- 在庫が 1,000 個未満なら注意（MFG-05）。必要数（2 枚分）に足りなければエラー
- Extended（Preferred を除く）の種類数が 8 を超えたらエラー（MFG-04a）
"""
import collections
import json
import pathlib
import sys
import time
import urllib.request

API = "https://jlcpcb.com/api/overseas-pcb-order/v1/shoppingCart/smtGood/selectSmtComponentList"
CACHE = pathlib.Path("build/jlc_cache.json")
BOARDS = 2
EXTENDED_MAX = 8
STOCK_WARN = 1000


def lookup(lcsc, cache, offline):
    hit = cache.get(lcsc)
    if hit and (offline or time.time() - hit["t"] < 86400):
        return hit
    if offline:
        return None
    req = urllib.request.Request(API, data=json.dumps({"keyword": lcsc, "currentPage": 1, "pageSize": 5}).encode(),
                                 headers={"Content-Type": "application/json", "User-Agent": "tune-jam-psu-bom-check"})
    data = json.load(urllib.request.urlopen(req, timeout=30))
    for c in (data.get("data") or {}).get("componentPageInfo", {}).get("list") or []:
        if c.get("componentCode") == lcsc:
            kind = "Basic" if c["componentLibraryType"] == "base" else ("Preferred" if c.get("preferredComponentFlag") else "Extended")
            hit = {"t": time.time(), "kind": kind, "stock": c["stockCount"], "model": c.get("componentModelEn", "")}
            cache[lcsc] = hit
            time.sleep(0.5)
            return hit
    return None


def main():
    comps = json.loads(pathlib.Path(sys.argv[1]).read_text())
    strict, offline = "--strict" in sys.argv, "--offline" in sys.argv
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    errors = 0
    todo, hand = [], []
    by_lcsc = collections.defaultdict(list)
    for ref, c in sorted(comps.items()):
        f = c.get("fields", {})
        if c["symbol"].startswith("power:"):
            continue
        if f.get("Assembly") == "HAND":
            hand.append(ref)
            if not f.get("Supplier"):
                errors += 1
                print(f"  NG    {ref}: 手はんだの部品に購入先（Supplier）がない")
            continue
        lcsc = f.get("LCSC", "")
        if not lcsc or lcsc == "TODO":
            todo.append(f'{ref}（{c["value"]}）')
            continue
        by_lcsc[lcsc].append(ref)

    ext = []
    for lcsc, refs in sorted(by_lcsc.items()):
        try:
            info = lookup(lcsc, cache, offline)
        except Exception as e:  # ネットワークの失敗は注意にとどめる
            print(f"  注意  {lcsc}: JLC に問い合わせできない（{e}）")
            continue
        need = len(refs) * BOARDS
        if info is None:
            errors += 1
            print(f"  NG    {lcsc}（{', '.join(refs)}）: JLC に見つからない")
            continue
        mark = "OK  "
        if info["stock"] < need:
            errors += 1
            mark = "NG  "
        elif info["stock"] < STOCK_WARN:
            mark = "注意"
        print(f"  {mark}  {lcsc} {info['model']:<22} {info['kind']:<9} 在庫 {info['stock']:>8}  使用 {len(refs)} 個（{', '.join(refs)}）")
        if info["kind"] == "Extended":
            ext.append(lcsc)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(cache, indent=1))

    if todo:
        msg = f"LCSC 番号が未決定：{len(todo)} 個（{', '.join(todo)}）"
        if strict:
            errors += 1
            print("  NG    " + msg)
        else:
            print("  注意  " + msg)
    print(f"  手はんだ：{', '.join(hand) or 'なし'}")
    if len(ext) > EXTENDED_MAX:
        errors += 1
        print(f"  NG    Extended が {len(ext)} 種類（上限 {EXTENDED_MAX}）")
    print(f"BOM：Extended {len(ext)} 種類（{', '.join(ext)}）、エラー {errors} 件")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
