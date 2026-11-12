#!/usr/bin/env python3
"""VER-10：検証をまとめて実行し、合否の一覧を出す。

使い方（リポジトリの最上位で）：python tools/verify/run_all.py [--strict]
結果は画面と build/verify_report.md に出す。1 つでも不合格なら終了コード 1。
"""
import datetime
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
PY = sys.executable
SCH = "build/hw/tune_jam_psu/tune_jam_psu.kicad_sch"
STRICT = ["--strict"] if "--strict" in sys.argv else []

STEPS = [
    ("回路図の生成", [PY, "hw/build.py"]),
    ("VER-01 ERC", ["python3", "tools/verify/erc_check.py", SCH, "hw/erc_waivers.json"]),
    ("ネットリストの出力", ["kicad-cli", "sch", "export", "netlist", "-o", "build/hw/kicad.net", SCH]),
    ("VER-03f 往復チェック", ["python3", "tools/verify/netlist_diff.py", "build/hw/expected_nets.json", "build/hw/kicad.net"]),
    ("VER-06 VAR の定数", ["python3", "hw/calc/var_network.py"]),
    ("VER-05 BOM", ["python3", "tools/verify/bom_check.py", "build/hw/components.json", *STRICT]),
    ("VER-07 出力スイッチ", ["python3", "sim/output-switch/check.py"]),
]


def main():
    rows, logs, ok_all = [], [], True
    for name, cmd in STEPS:
        t = time.time()
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        ok = r.returncode == 0
        ok_all &= ok
        last = next((l for l in reversed((r.stdout or r.stderr).strip().splitlines()) if l.strip()), "")
        rows.append((name, "合格" if ok else "不合格", f"{time.time() - t:.1f}s", last.strip()))
        logs.append(f"### {name}\n\n```\n{(r.stdout + r.stderr).strip()[-4000:]}\n```\n")
        print(f"{'OK' if ok else 'NG'}  {name:<22} {rows[-1][2]:>6}  {last.strip()}")
        if not ok and name == "回路図の生成":
            break
    report = ["# 検証結果", "", f"実行：{datetime.datetime.now():%Y-%m-%d %H:%M}", "",
              "| 項目 | 結果 | 時間 | 要約 |", "|---|---|---|---|"]
    report += [f"| {a} | {b} | {c} | {d.replace('|', '/')} |" for a, b, c, d in rows]
    report += ["", "## 詳細", ""] + logs
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build" / "verify_report.md").write_text("\n".join(report))
    print("全体：" + ("合格" if ok_all else "不合格あり") + "（詳細は build/verify_report.md）")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
