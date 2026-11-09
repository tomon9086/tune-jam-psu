#!/usr/bin/env python3
"""意図した接続と、KiCad の回路図から出したネットリストを突き合わせる（往復チェック）。

使い方:
    kicad-cli sch export netlist -o out.net 回路図.kicad_sch
    python3 tools/verify/netlist_diff.py 期待値.json out.net

期待値.json は {"ネット名": ["U1.2", "C1.1", ...], ...} の形（hw/build.py が build/hw/expected_nets.json に出す）。
ネット名は比べず、「どのピンどうしが同じネットにいるか」（ピンの分け方）だけを比べる。
未接続のピン（KiCad が unconnected-(...) と名付けるネット）は、期待値に書かなければ無視する。
KiCad 側に意図していない接続がないかも逆向きに調べる。差分があれば終了コード 1 を返す。
"""
import json
import re
import sys


def read_kicad_net(path):
    s = open(path, encoding="utf-8").read()
    nets = {}
    for block in re.split(r"\(net \(code ", s)[1:]:
        name = re.search(r'\(name "([^"]*)"\)', block)[1]
        pins = {f"{r}.{p}" for r, p in re.findall(r'\(ref "([^"]+)"\) \(pin "([^"]+)"\)', block)}
        if name.startswith("unconnected-"):
            continue
        nets[name] = pins
    return nets


def main():
    expected = {k: set(v) for k, v in json.load(open(sys.argv[1])).items()}
    actual = read_kicad_net(sys.argv[2])
    pin2net = {p: n for n, ps in actual.items() for p in ps}
    ok = True
    for name, pins in sorted(expected.items()):
        got = {}
        for p in sorted(pins):
            got.setdefault(pin2net.get(p, "(未接続)"), []).append(p)
        if len(got) == 1 and "(未接続)" not in got:
            kname = next(iter(got))
            extra = actual[kname] - pins
            if extra:
                ok = False
                print(f"NG  {name}: 期待しないピンが混ざっている {sorted(extra)}（KiCad のネット {kname}）")
            else:
                print(f"OK  {name}: {len(pins)} ピン")
        else:
            ok = False
            detail = "、".join(f"{k} に {v}" for k, v in got.items())
            print(f"NG  {name}: 分かれている → {detail}")
    # 逆向き：KiCad 側のネットに、意図していないピンどうしの接続がないか
    exp_pin2net = {p: n for n, ps in expected.items() for p in ps}
    for kname, pins in sorted(actual.items()):
        groups = {exp_pin2net.get(p, "(期待値にない)") for p in pins}
        if len(groups) > 1 or "(期待値にない)" in groups:
            ok = False
            print(f"NG  KiCad のネット {kname} に、意図していない接続がある：{sorted(pins)}")
    print("往復チェック：" + ("一致" if ok else "不一致あり"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
