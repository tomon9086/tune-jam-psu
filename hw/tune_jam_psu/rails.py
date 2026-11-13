"""ブレッドボードのレール選択と、ブレッドボード用のピン。

要件：BB-01〜05、FIX-04、TST-01
左右のレールごとに 2x3 のピンヘッダを置き、ジャンパで VAR / 5V / 3.3V のどれかを選ぶ（外せば OFF）。
ピンの本数と位置（MB102 互換）は P3 で決める。ここでは接続だけを書く。
"""
from circuit_synth import Net, circuit

from .parts import hand

H2x3 = "Connector_PinHeader_2.54mm:PinHeader_2x03_P2.54mm_Vertical"
H1x2 = "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"


@circuit(name="rails")
def rails(gnd, var_out, v5, v3_out):
    for side in ("L", "R"):
        rail = Net(f"RAIL_{side}")
        sel = hand("Connector_Generic:Conn_02x03_Odd_Even", "J", f"SEL_{side}", H2x3, "ピンヘッダ 2x3 ＋ ジャンパ")
        sel[1] += var_out; sel[3] += v5; sel[5] += v3_out
        sel[2] += rail; sel[4] += rail; sel[6] += rail
        bb = hand("Connector_Generic:Conn_01x02", "J", f"BB_{side}", H1x2, "ピンヘッダ 1x2（ブレッドボードのレールへ）")
        bb[1] += rail; bb[2] += gnd
    # リード線で取り出す端子（BB-05、任意）
    lead = hand("Connector_Generic:Conn_01x02", "J", "VAR_LEAD", H1x2, "ピンヘッダ 1x2")
    lead[1] += var_out; lead[2] += gnd
