#!/usr/bin/env python3
"""自作の記号ライブラリ（tune_jam_psu.kicad_sym）を、ピン表から生成する。

KiCad 標準の記号をそのまま使えない部品だけをここに置く：
- 複数ユニットの記号（MCP6002、LM393）：circuit-synth 0.12.1 が 1 つ目のユニットしか描けず、
  ほかのユニットのピンのラベルを重ねてネットをつないでしまう（2026-11-13、往復チェックで発見）
- 同じ名前のピンがある記号（BAV99：KiCad では 1 と 3 がどちらも "K"）：ラベルを間違ったピンに付ける。
  しかも KiCad のピン名はデータシートと逆（データシートは 1=A1、2=K2、3=K1/A2）

ピン表は各部品のデータシートから写した（出典を書く）。VER-04 のピン照合でもこの表を使う。
使い方：python hw/symbols/gen_symbols.py
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent

# (記号名, 説明, 標準のフットプリント, 出典, [(番号, 名前, 種類), ...]) 左側に前半、右側に後半を並べる
SYMBOLS = [
    ("MCP6002_SOIC8", "デュアル オペアンプ（1 ユニットにまとめた記号）", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     "Microchip MCP6001/1R/1U/2/4 データシート DS20001733、Table 3-1（SOIC）",
     [("1", "OUTA", "output"), ("2", "-INA", "input"), ("3", "+INA", "input"), ("4", "VSS", "power_in"),
      ("5", "+INB", "input"), ("6", "-INB", "input"), ("7", "OUTB", "output"), ("8", "VDD", "power_in")]),
    ("LM393_SOIC8", "デュアル コンパレータ、オープンコレクタ出力（1 ユニットにまとめた記号）", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
     "onsemi LM393/LM2903 データシート、PIN CONNECTIONS（SOIC-8）",
     [("1", "OUTA", "open_collector"), ("2", "-INA", "input"), ("3", "+INA", "input"), ("4", "GND", "power_in"),
      ("5", "+INB", "input"), ("6", "-INB", "input"), ("7", "OUTB", "open_collector"), ("8", "VCC", "power_in")]),
    ("BAV99_SOT23", "直列 2 素子のスイッチングダイオード（ピン名をデータシートに合わせた記号）", "Package_TO_SOT_SMD:SOT-23",
     "Nexperia BAV99 データシート、Table 2 Pinning information（JLC C2500 のデータシート）",
     [("1", "A1", "passive"), ("3", "K1A2", "passive"), ("2", "K2", "passive")]),
]

PITCH = 2.54


def pin(num, name, kind, x, y, angle):
    return f"""      (pin {kind} line (at {x:.2f} {y:.2f} {angle}) (length 2.54)
        (name "{name}" (effects (font (size 1.27 1.27))))
        (number "{num}" (effects (font (size 1.27 1.27)))))"""


def symbol(name, desc, fp, src, pins):
    half = (len(pins) + 1) // 2
    left, right = pins[:half], pins[half:]
    h = max(len(left), len(right)) * PITCH
    w = 10.16
    body = [pin(n, nm, k, -w / 2 - 2.54, h / 2 - PITCH / 2 - i * PITCH, 0) for i, (n, nm, k) in enumerate(left)]
    body += [pin(n, nm, k, w / 2 + 2.54, h / 2 - PITCH / 2 - i * PITCH, 180) for i, (n, nm, k) in enumerate(right)]
    return f"""  (symbol "{name}" (pin_names (offset 1.016)) (exclude_from_sim no) (in_bom yes) (on_board yes)
    (property "Reference" "U" (at 0 {h / 2 + 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Value" "{name}" (at 0 {-h / 2 - 2.54:.2f} 0) (effects (font (size 1.27 1.27))))
    (property "Footprint" "{fp}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Datasheet" "{src}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (property "Description" "{desc}" (at 0 0 0) (effects (font (size 1.27 1.27)) (hide yes)))
    (symbol "{name}_0_1"
      (rectangle (start {-w / 2:.2f} {h / 2:.2f}) (end {w / 2:.2f} {-h / 2:.2f})
        (stroke (width 0.254) (type default)) (fill (type background))))
    (symbol "{name}_1_1"
{chr(10).join(body)}
    )
  )"""


def main():
    text = "(kicad_symbol_lib (version 20241209) (generator \"tune_jam_psu_gen\") (generator_version \"1\")\n"
    text += "\n".join(symbol(*s) for s in SYMBOLS) + "\n)\n"
    (HERE / "tune_jam_psu.kicad_sym").write_text(text)
    print(f"OK: {len(SYMBOLS)} 記号 → {HERE / 'tune_jam_psu.kicad_sym'}")


if __name__ == "__main__":
    main()
