#!/usr/bin/env python3
"""VER-07：出力スイッチ（N-FET × 2 ＋チャージポンプ）のシミュレーションを回し、合否を出す。

使い方（リポジトリの最上位で）：python sim/output-switch/check.py

合格の条件：
- ON のとき Vgs ≥ 4.0V（AO3400A を十分に ON にする）
- ON・OFF の間ずっと Vgs ≤ 12V、OFF のあと Vgs ≥ −1V（AO3400A の定格 ±12V）
- OFF の指示から、電流が 0.2A 以下になるまで 2µs 以内（PRT-02 の 10µs の一部）
- OFF のとき、外部 15V をかけても降圧側に流れる電流が 1µA 以下（PRT-04）
"""
import concurrent.futures
import os
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent


def run(cir):
    out = subprocess.run(["ngspice", "-b", cir.name], cwd=HERE, capture_output=True, text=True, timeout=900)
    text = (out.stdout + out.stderr).replace("\r", "\n")
    vals = {}
    for m in re.finditer(r"^(\w+)\s+=\s+([-+0-9.eE]+)", text, re.M):
        vals[m.group(1)] = float(m.group(2))
    return cir.stem, vals


def main():
    subprocess.run([sys.executable, "gen.py"], cwd=HERE, check=True, capture_output=True)
    cirs = sorted(HERE.glob("case_*.cir")) + [HERE / "reverse_block.cir"]
    ok = True
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 2) as ex:
        results = dict(ex.map(run, cirs))
    for name, v in results.items():
        if name == "reverse_block":
            good = abs(v.get("irev", 1)) <= 1e-6
            print(f"  {'OK' if good else 'NG'}  逆流：{v.get('irev', float('nan')) * 1e9:.1f} nA（上限 1000 nA）")
        else:
            toff = (v.get("ioff", 1) - 2e-3) * 1e6
            checks = [v.get("vgs_on", 0) >= 4.0, v.get("vgsmax", 99) <= 12.0, v.get("vgsmin", -99) >= -1.0, toff <= 2.0]
            good = all(checks)
            print(f"  {'OK' if good else 'NG'}  {name}: Vgs(ON) {v.get('vgs_on', float('nan')):.2f}V、"
                  f"Vgs 最大 {v.get('vgsmax', float('nan')):.2f}V、最小 {v.get('vgsmin', float('nan')):.2f}V、"
                  f"OFF まで {toff:.2f}µs、降下 {v.get('vdrop', float('nan')) * 1e3:.0f}mV")
        ok &= good
    print("出力スイッチ：" + ("合格" if ok else "不合格あり"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
