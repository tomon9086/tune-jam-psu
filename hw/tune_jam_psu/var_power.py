"""VAR（可変出力）：降圧（LMR33630）、FB 注入、CC ループ、短絡検出、出力スイッチ。

設計は docs/design/var.md、定数は hw/calc/var_network.py。
要件：VAR-01〜13、PRT-02〜04、PRT-08、D21、D22

MCU とつなぐネット（引数）：
  dac1 / dac2      ：Vset / Iset（DAC 出力）
  inj_en           ：INJ スイッチ（High で注入 ON。リセット時はプルダウンで OFF）
  out_off          ：出力 OFF（High で出力スイッチ OFF。リセット時はプルアップで OFF）
  cp_pwm           ：チャージポンプ用の PWM（3.3V、100kHz）。止まると出力スイッチは OFF になる
  latch_rst        ：短絡ラッチの解除（High パルス）
  short_n          ：短絡ラッチの状態（Low でラッチ中）
  pg_var           ：LMR33630 の PG（オープンドレイン、VDDA にプルアップ）
  adc_vbuck / adc_vout / adc_iout：ADC へ（分圧済み）
"""
from circuit_synth import Component, Net, circuit

from .parts import C, C0805, C1206, R, R1206

SOIC8 = "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
SOT23 = "Package_TO_SOT_SMD:SOT-23"
SOD123 = "Diode_SMD:D_SOD-123"


def nfet(lcsc="C20917"):
    return Component(symbol="Transistor_FET:AO3400A", ref="Q", value="AO3400A", footprint=SOT23, LCSC=lcsc)


def d4148():
    return Component(symbol="Diode:1N4148W", ref="D", value="1N4148W", footprint=SOD123, LCSC="C81598")


@circuit(name="var_power")
def var_power(vin, gnd, v5, vdda, var_out,
              dac1, dac2, inj_en, out_off, cp_pwm, latch_rst, short_n, pg_var,
              adc_vbuck, adc_vout, adc_iout):
    sw, boot, vcc, fb = Net("VAR_SW"), Net("VAR_BOOT"), Net("VAR_VCC"), Net("VAR_FB")
    bout, vs = Net("VAR_BUCK"), Net("VAR_SENSE")          # シャントの前と後
    th, inj, inj_s = Net("VSET_TH"), Net("INJ"), Net("INJ_S")
    csa, csp, inn, ccout, ccd = Net("CSA"), Net("CSP"), Net("CC_INN"), Net("CC_OUT"), Net("CC_D")
    gate, src, cp_a, cp = Net("OUT_GATE"), Net("OUT_SRC"), Net("CP_A"), Net("CP")
    thr, lat_p, lat_n = Net("SHORT_THR"), Net("LATCH_P"), Net("LATCH_N")

    # ---- 降圧 ----
    u = Component(symbol="Regulator_Switching:LMR33630ADDA", ref="U", value="LMR33630ADDAR",
                  footprint="Package_SO:TI_SO-PowerPAD-8_ThermalVias", LCSC="C841384")
    u["VIN"] += vin; u["EN"] += vin; u["GND"] += gnd
    u["SW"] += sw; u["BOOT"] += boot; u["FB"] += fb; u["VCC"] += vcc; u["PG"] += pg_var
    for _ in range(2):
        c = C("10u", C1206); c[1] += vin; c[2] += gnd
    c = C("100n"); c[1] += boot; c[2] += sw
    c = C("1u"); c[1] += vcc; c[2] += gnd
    r = R("100k"); r[1] += pg_var; r[2] += vdda
    l = Component(symbol="Device:L", ref="L", value="10u",
                  footprint="Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm", LCSC="C2687402")
    l[1] += sw; l[2] += bout
    for _ in range(2):
        c = C("22u", C1206); c[1] += bout; c[2] += gnd

    # ---- シャント 100mΩ × 3 並列（33.3mΩ）と電流センス（INA180A1、20V/V）----
    for _ in range(3):
        r = R("100m", R1206, lcsc="C25334"); r[1] += bout; r[2] += vs
    csa_ic = Component(symbol="Amplifier_Current:INA180A1", ref="U", value="INA180A1",
                       footprint="Package_TO_SOT_SMD:SOT-23-5", LCSC="C122228")
    csa_ic["+"] += bout; csa_ic["-"] += vs; csa_ic["V+"] += v5; csa_ic["GND"] += gnd; csa_ic[1] += csa
    c = C("100n"); c[1] += v5; c[2] += gnd

    # ---- FB の分圧と Vset 注入 ----
    r = R("100k"); r[1] += vs; r[2] += fb        # R1（シャントの後から。電圧降下を補償）
    r = R("499k"); r[1] += fb; r[2] += gnd       # R2
    r = R("14.7k"); r[1] += dac1; r[2] += th     # Ra
    r = R("7.5k"); r[1] += th; r[2] += gnd       # Rb
    r = R("2.7k"); r[1] += th; r[2] += inj       # Rinj

    # INJ スイッチ：N-FET 2 個のソース共通（どちら向きにも流さない）。ゲートはリセット時にプルダウンで OFF
    qa, qb = nfet(), nfet()
    qa["D"] += inj; qa["S"] += inj_s; qa["G"] += inj_en
    qb["D"] += fb; qb["S"] += inj_s; qb["G"] += inj_en
    r = R("100k"); r[1] += inj_en; r[2] += gnd

    # ---- CC アンプ（MCP6002 の A）：「CSA + 0.2V」× 0.943 と DAC2 を比べる ----
    op = Component(symbol="tune_jam_psu:MCP6002_SOIC8", ref="U", value="MCP6002",
                   footprint=SOIC8, LCSC="C7377")
    r = R("10k"); r[1] += csa; r[2] += csp       # 下駄：CSP = 0.943 × (CSA + 0.2V)
    r = R("165k"); r[1] += vdda; r[2] += csp
    op["+INA"] += csp; op["-INA"] += inn
    r = R("10k"); r[1] += dac2; r[2] += inn      # Ri
    rf, cf, mid = R("4.7k"), C("10n"), Net("CC_FB_MID")   # Rf + Cf（値は sim/cc-loop の結果で決める）
    rf[1] += inn; rf[2] += mid; cf[1] += mid; cf[2] += ccout
    op["OUTA"] += ccout
    d = d4148(); d["A"] += ccout; d["K"] += ccd
    r = R("0", lcsc="TODO"); r[1] += ccd; r[2] += Net("CC_D2")   # VAR-06a：CC だけを切り離す 0Ω（DNP 可）
    r2 = R("10k"); r2[1] += Net("CC_D2"); r2[2] += inj           # Rcc
    # MCP6002 の B は使わない：ボルテージフォロアにして入力を GND に
    opb = Net("OPB_OUT")
    op["+INB"] += gnd; op["-INB"] += opb; op["OUTB"] += opb
    op["VDD"] += v5; op["VSS"] += gnd
    c = C("100n"); c[1] += v5; c[2] += gnd

    # ---- 短絡検出とラッチ（LM393）----
    cmp_ = Component(symbol="tune_jam_psu:LM393_SOIC8", ref="U", value="LM393", footprint=SOIC8, LCSC="C7955")
    # A：CSA > 2.0V（3A）で出力 Low。しきい値は VDDA の分圧
    r = R("6.49k"); r[1] += vdda; r[2] += thr
    r = R("10k"); r[1] += thr; r[2] += gnd       # 3.3 × 10 / 16.49 = 2.00V
    cmp_["+INA"] += thr; cmp_["-INA"] += csa
    # B：ラッチ。B の出力（SHORT_N）が High のときは + 入力も高く保たれ、A が引き下げると Low で固まる
    cmp_["OUTA"] += lat_p                       # A の出力（オープンコレクタ）で LATCH_P を引き下げる
    r = R("10k"); r[1] += vdda; r[2] += short_n   # SHORT_N のプルアップ（MCU に合わせて 3.3V）
    r = R("10k"); r[1] += short_n; r[2] += lat_p  # 正帰還
    r = R("10k"); r[1] += lat_p; r[2] += gnd
    r = R("20k"); r[1] += vdda; r[2] += lat_n
    r = R("10k"); r[1] += lat_n; r[2] += gnd      # B の − 入力 1.1V（通常時の + 入力は 1.65V）
    cmp_["+INB"] += lat_p; cmp_["-INB"] += lat_n; cmp_["OUTB"] += short_n
    d = d4148(); d["A"] += latch_rst; d["K"] += lat_p   # 解除：MCU が LATCH_P を持ち上げる
    cmp_["VCC"] += v5; cmp_["GND"] += gnd
    c = C("100n"); c[1] += v5; c[2] += gnd

    # ---- 出力スイッチ（AO3400A × 2、ソース共通）＋チャージポンプ（sim/output-switch/）----
    q1, q2 = nfet(), nfet()
    q1["D"] += vs; q1["S"] += src; q1["G"] += gate
    q2["D"] += var_out; q2["S"] += src; q2["G"] += gate
    bav = Component(symbol="tune_jam_psu:BAV99_SOT23", ref="D", value="BAV99", footprint=SOT23, LCSC="C2500")
    # 自作の記号（KiCad 標準の BAV99 はピン名がデータシートと逆で、同名のピンがある）
    bav["A1"] += vin; bav["K1A2"] += cp_a; bav["K2"] += cp
    c = C("100n"); c[1] += cp_pwm; c[2] += cp_a
    c = C("100n", C0805); c[1] += cp; c[2] += vin
    r = R("100k"); r[1] += cp; r[2] += gate
    z = Component(symbol="Device:D_Zener", ref="D", value="MMSZ5240B", footprint=SOD123, LCSC="C19077425")
    z["K"] += gate; z["A"] += src
    # OFF：OUT_OFF（MCU、リセット時はプルアップ）で N-FET がゲートを引く。短絡ラッチ中も引く
    qo = nfet(); qo["D"] += gate; qo["S"] += gnd; qo["G"] += out_off
    r = R("100k"); r[1] += out_off; r[2] += vdda
    d = d4148(); d["A"] += gate; d["K"] += short_n
    # 出力の放電（VAR-13）：出力 OFF のとき 1kΩ でつなぐ
    qd, dis = nfet(), Net("DISCH")
    qd["D"] += dis; qd["S"] += gnd; qd["G"] += out_off
    r = R("1k", R1206); r[1] += var_out; r[2] += dis
    # 出力の TVS と ESD（PRT-08）
    tvs = Component(symbol="Device:D_Zener", ref="D", value="SMAJ15A", footprint="Diode_SMD:D_SMA",
                    LCSC="C19077535")
    tvs["K"] += var_out; tvs["A"] += gnd

    # ---- ADC への分圧（MCU の ADC、3.3V）----
    for node, net in ((vs, adc_vbuck), (var_out, adc_vout)):
        r = R("100k"); r[1] += node; r[2] += net
        r = R("27k"); r[1] += net; r[2] += gnd    # 15V で 3.19V
        c = C("100n"); c[1] += net; c[2] += gnd
    r = R("10k"); r[1] += csa; r[2] += adc_iout  # 直列抵抗（CSA が 5V 近くになっても ADC の注入電流を制限）
    c = C("100n"); c[1] += adc_iout; c[2] += gnd
