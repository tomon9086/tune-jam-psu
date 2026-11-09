#!/usr/bin/env python3
"""VER-01：KiCad の ERC を回し、許可リストにない違反を数える。

使い方：python tools/verify/erc_check.py 回路図.kicad_sch [許可リスト.json]

許可リスト（hw/erc_waivers.json）の形：
    [{"type": "power_pin_not_driven", "contains": "U1 Pin 2", "reason": "…"}]
type が一致し、違反の説明か対象の説明に contains の文字列を含む違反を許可する。
error が 1 件でも残れば終了コード 1。warning は表示だけする。
"""
import json
import pathlib
import subprocess
import sys
import tempfile


def main():
    sch = sys.argv[1]
    waivers = json.loads(pathlib.Path(sys.argv[2]).read_text()) if len(sys.argv) > 2 else []
    with tempfile.TemporaryDirectory() as d:
        out = pathlib.Path(d) / "erc.json"
        subprocess.run(["kicad-cli", "sch", "erc", "--format", "json", "--severity-all",
                        "-o", str(out), sch], check=True, capture_output=True)
        report = json.loads(out.read_text())
    errors = warnings = waived = 0
    for sheet in report["sheets"]:
        for v in sheet["violations"]:
            text = v["description"] + " " + " ".join(i["description"] for i in v["items"])
            w = next((w for w in waivers if w["type"] == v["type"] and w["contains"] in text), None)
            label = f'{v["severity"]:7} {v["type"]}: {v["description"]} ' \
                    f'[{"; ".join(i["description"] for i in v["items"])}] ({sheet["path"]})'
            if w:
                waived += 1
                print(f"  許可  {label} ← {w['reason']}")
            elif v["severity"] == "error":
                errors += 1
                print(f"  NG    {label}")
            else:
                warnings += 1
                print(f"  注意  {label}")
    print(f"ERC: エラー {errors} 件、注意 {warnings} 件、許可 {waived} 件")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
