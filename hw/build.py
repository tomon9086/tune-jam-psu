#!/usr/bin/env python3
"""回路のソース（hw/tune_jam_psu）から KiCad プロジェクトを作る。

使い方（リポジトリの最上位で）：
    python hw/build.py            # build/hw/tune_jam_psu/ に出力

出力：
- build/hw/tune_jam_psu/*.kicad_sch、*.kicad_pro：KiCad の回路図
- build/hw/expected_nets.json：コードで意図した接続（往復チェックの期待値）
- build/hw/components.json：部品の一覧（BOM チェック用）

毎回 build/hw を消してから作り直す（既存のプロジェクトがあると古い接続が残るため）。

後処理：circuit-synth 0.12.1 は 1 枚の図でも階層ラベルを使い、KiCad の ERC がエラーにする。
global_label に置き換える（接続は変わらない。eval/q7-schematic-tools/README.md）。
"""
import json
import os
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "build" / "hw"
NAME = "tune_jam_psu"

sys.path.insert(0, str(ROOT / "hw"))


def collect(data, comps, nets, path=""):
    """circuit-synth の JSON（サブ回路を含む）から、部品とネットを平らに集める。"""
    for ref, c in data.get("components", {}).items():
        comps[ref] = {k: c.get(k) for k in ("symbol", "value", "footprint")}
        comps[ref]["fields"] = c.get("_extra_fields", {})
    for name, n in data.get("nets", {}).items():
        nodes = n["nodes"] if isinstance(n, dict) else n  # 最上位は {"nodes": [...]}、サブ回路は [...]
        nets.setdefault(name, set()).update(f'{x["component"]}.{x["pin"]["number"]}' for x in nodes)
    for sub in data.get("subcircuits", []):
        collect(sub, comps, nets, path + "/" + sub.get("name", ""))


def main():
    from tune_jam_psu.top import top

    # circuit-synth は既存のプロジェクトがあると「更新」し、古い接続が残ることがある。
    # 毎回消してから作り直す（往復チェックで発見、2026-11-09）
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)
    os.chdir(OUT)
    circ = top()
    circ.generate_kicad_project(project_name=NAME, generate_pcb=False)

    proj = OUT / NAME
    for sch in proj.glob("*.kicad_sch"):
        s = sch.read_text()
        sch.write_text(s.replace("(hierarchical_label ", "(global_label "))

    data = json.loads((proj / f"{NAME}.json").read_text())
    comps, nets = {}, {}
    collect(data, comps, nets)
    (OUT / "expected_nets.json").write_text(
        json.dumps({k: sorted(v) for k, v in sorted(nets.items())}, ensure_ascii=False, indent=1))
    (OUT / "components.json").write_text(json.dumps(comps, ensure_ascii=False, indent=1))
    print(f"OK: {len(comps)} 部品、{len(nets)} ネット → {proj}")


if __name__ == "__main__":
    main()
