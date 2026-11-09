"""よく使う部品の作り方をまとめる。

すべての SMD 部品に LCSC 番号（JLC で実装するときの部品番号）を付ける。
手はんだの部品は Assembly="HAND" にして、BOM チェックで LCSC 番号を求めないようにする。
"""
from circuit_synth import Component

R0603 = "Resistor_SMD:R_0603_1608Metric"
R1206 = "Resistor_SMD:R_1206_3216Metric"
C0603 = "Capacitor_SMD:C_0603_1608Metric"
C0805 = "Capacitor_SMD:C_0805_2012Metric"
C1206 = "Capacitor_SMD:C_1206_3216Metric"

# JLC の Basic 部品（docs/parts-selection.md 0 章）。受動部品の LCSC 番号は P2 で値を決めるときに埋める
LCSC_TODO = "TODO"


def part(symbol, value, footprint, lcsc, **fields):
    return Component(symbol=symbol, ref=symbol.split(":")[1][0], value=value,
                     footprint=footprint, LCSC=lcsc, **fields)


def R(value, footprint=R0603, lcsc=LCSC_TODO):
    return Component(symbol="Device:R", ref="R", value=value, footprint=footprint, LCSC=lcsc)


def C(value, footprint=C0603, lcsc=LCSC_TODO):
    return Component(symbol="Device:C", ref="C", value=value, footprint=footprint, LCSC=lcsc)


def hand(symbol, ref, value, footprint, supplier):
    """手はんだの部品（秋月などで買う）。supplier に購入先と型番を書く。"""
    return Component(symbol=symbol, ref=ref, value=value, footprint=footprint,
                     Assembly="HAND", Supplier=supplier)
