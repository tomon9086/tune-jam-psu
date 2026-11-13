#!/usr/bin/env python3
"""VER-06：VAR（可変出力）の FB 注入回路と CC ループの定数を計算し、要件と突き合わせる。

回路（docs/design/var.md）：
    VOUT_SENSE ─R1─┬─ FB（LMR33630、Vref = 1.0V）
                   R2
                   GND
    DAC1 ─Ra─┬─Rinj─┤INJ スイッチ├─ FB      （Vset。Rb で分圧してから注入）
             Rb
             GND
    CC アンプ ─D─Rcc─┘（INJ スイッチの手前で合流）
    CC アンプは「電流検出の電圧 + 0.2V」と DAC2 を比べる（DAC は 0.2V 未満を出せないため）

INJ スイッチが OFF のとき（起動中）は、出力が Vref × (1 + R1/R2) ≒ 1.2V で立ち上がる。
起動が終わってから MCU が INJ スイッチを ON にし、DAC1 で出力電圧を決める。

使い方：python hw/calc/var_network.py   （要件を満たさなければ終了コード 1）
"""
import sys

# ---- 部品・条件 ----
VREF = 1.0            # LMR33630 の FB 基準電圧（V、±1.5%）
DAC_LO, DAC_HI = 0.2, 3.1   # STM32G0 の DAC（バッファあり）の出力範囲（V）。VDDA = 3.3V
DAC_BITS = 12
VDDA = 3.3

R1 = 100e3            # VOUT_SENSE → FB
R2 = 499e3            # FB → GND
RA = 14.7e3           # DAC1 → 分圧点
RB = 7.5e3            # 分圧点 → GND
RINJ = 2.7e3          # 分圧点 → INJ スイッチ → FB

# 電流検出
RSHUNT = 0.1 / 3      # 100mΩ × 3 本並列
GAIN_CSA = 20         # INA180A1
I_SHORT = 3.0         # 短絡検出のしきい値（A、PRT-02）
V_OFF = 0.2           # CC アンプで電流検出の信号に足す下駄（V）。VDDA の分圧で作る（DAC と同じ基準なので誤差が打ち消し合う）

# 要件
VOUT_MIN_REQ, VOUT_MAX_REQ = 0.8, 12.0    # VAR-01
VSET_RES_REQ = 10e-3                       # VAR-03
ISET_MIN_REQ, ISET_MAX_REQ = 0.05, 2.0     # VAR-05
ISET_RES_REQ = 10e-3                       # VAR-05
LM393_CM_MAX = 5.0 - 1.5                   # LM393 の同相入力の上限（5V 電源）
DAC_LOAD_MIN = 5e3                         # STM32G0 の DAC が駆動できる最小の負荷抵抗


def par(a, b):
    return a * b / (a + b)


def vout(vdac, inj=True):
    """FB = VREF で釣り合うときの出力電圧。"""
    g = RB / (RA + RB)
    vth, rth = vdac * g, par(RA, RB) + RINJ
    i = VREF / R2 + ((VREF - vth) / rth if inj else 0.0)
    return VREF + R1 * i


def main():
    lsb = VDDA / 2 ** DAC_BITS
    rows = []

    def check(name, value, ok, note=""):
        rows.append((name, value, ok, note))

    v_lo, v_hi = vout(DAC_HI), vout(DAC_LO)
    check("出力の下限（DAC 最大）", f"{v_lo:.3f} V", v_lo <= VOUT_MIN_REQ, f"要件 {VOUT_MIN_REQ} V 以下まで出せること")
    check("出力の上限（DAC 最小）", f"{v_hi:.3f} V", v_hi >= VOUT_MAX_REQ, f"要件 {VOUT_MAX_REQ} V 以上まで出せること")
    res = abs(vout(1.0) - vout(1.0 + lsb))
    check("電圧の設定分解能", f"{res * 1e3:.2f} mV/LSB", res <= VSET_RES_REQ, f"要件 {VSET_RES_REQ * 1e3:.0f} mV")
    v0 = vout(0, inj=False)
    check("起動中の出力（INJ OFF）", f"{v0:.3f} V", v0 <= 1.5, "低い電圧で立ち上がること（1.5V 以下）")
    fb0 = (DAC_HI * RB / (RA + RB)) * R1 / (R1 + par(RA, RB) + RINJ)
    check("参考：INJ を ON のまま起動したときの FB", f"{fb0:.3f} V", True, "これが高いと起動しない（シミュレーションで確認、INJ スイッチの理由）")
    load = RA + par(RB, RINJ + R1)
    check("DAC1 の負荷抵抗", f"{load / 1e3:.1f} kΩ", load >= DAC_LOAD_MIN, f"{DAC_LOAD_MIN / 1e3:.0f} kΩ 以上")
    zfb = par(par(R1, R2), par(RA, RB) + RINJ)
    check("FB 端子から見た抵抗", f"{zfb / 1e3:.2f} kΩ", zfb <= 20e3, "ノイズを拾いにくいこと（20kΩ 以下）")

    k = RSHUNT * GAIN_CSA
    check("電流検出の感度", f"{k:.3f} V/A", True)
    d_lo, d_hi = V_OFF + ISET_MIN_REQ * k, V_OFF + ISET_MAX_REQ * k
    check("Iset に必要な DAC2 の電圧", f"{d_lo:.3f}〜{d_hi:.3f} V", DAC_LO <= d_lo and d_hi <= DAC_HI,
          f"DAC の出力範囲 {DAC_LO}〜{DAC_HI} V に収まること（下駄 {V_OFF} V を足して比べる）")
    check("電流の設定分解能", f"{lsb / k * 1e3:.2f} mA/LSB", lsb / k <= ISET_RES_REQ, f"要件 {ISET_RES_REQ * 1e3:.0f} mA")
    vs = I_SHORT * k
    check("短絡しきい値の電圧", f"{vs:.2f} V", vs <= LM393_CM_MAX, f"LM393 の同相入力 {LM393_CM_MAX} V 以下")
    p = (ISET_MAX_REQ / 3) ** 2 * 0.1
    check("シャント 1 本の損失（2A）", f"{p * 1e3:.0f} mW", p <= 0.25 * 0.5, "定格 0.25W の半分以下")

    ok_all = True
    for name, value, ok, note in rows:
        ok_all &= ok
        print(f"  {'OK' if ok else 'NG'}  {name:<28} {value:>16}  {note}")
    print("VAR の定数：" + ("要件を満たす" if ok_all else "要件を満たさない項目あり"))
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
