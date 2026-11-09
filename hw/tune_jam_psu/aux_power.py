"""入力と補助電源：DC ジャック → TVS → 5V 降圧（LMR33630）→ 3.3V LDO × 2。

要件：IN-01、PRT-05、FIX-01/02、D13、D17、D23
定数は仮の値（P2 で設計計算スクリプトにする）。
- 5V：Vout = 1.0V × (1 + 100k / 24.9k) ≒ 5.02V
- 逆接保護（PRT-09）と突入制限（IN-08）は、まだ入れていない
"""
from circuit_synth import Component, Net, circuit

from .parts import C, C0805, C1206, R, hand


@circuit(name="aux_power")
def aux_power(vin, gnd, v5, v3_int, v3_out):
    sw, boot, fb, vcc = Net("SW_5V"), Net("BOOT_5V"), Net("FB_5V"), Net("VCC_5V")

    # PWR_FLAG（電源の入口の印）は circuit-synth 0.12.1 が書き出さないので、hw/erc_waivers.json で許可している

    j = hand("Connector:Barrel_Jack", "J", "MJ-179PH",
             "Connector_BarrelJack:BarrelJack_Horizontal",  # TODO: MJ-179PH 用のフットプリントを作る（P3）
             "秋月 106568")
    j[1] += vin
    j[2] += gnd

    tvs = Component(symbol="Device:D_Zener", ref="D", value="SMAJ22A",
                    footprint="Diode_SMD:D_SMA", LCSC="C41376403")
    tvs["K"] += vin
    tvs["A"] += gnd

    u = Component(symbol="Regulator_Switching:LMR33630ADDA", ref="U", value="LMR33630ADDAR",
                  footprint="Package_SO:TI_SO-PowerPAD-8_ThermalVias", LCSC="C841384")
    u["VIN"] += vin
    u["EN"] += vin
    u["GND"] += gnd
    u["SW"] += sw
    u["BOOT"] += boot
    u["FB"] += fb
    u["VCC"] += vcc

    cin = C("10u", C1206)
    cin[1] += vin
    cin[2] += gnd
    cboot = C("100n")
    cboot[1] += boot
    cboot[2] += sw
    cvcc = C("1u")
    cvcc[1] += vcc
    cvcc[2] += gnd

    l = Component(symbol="Device:L", ref="L", value="10u",
                  footprint="Inductor_SMD:L_Bourns_SRP7028A_7.3x6.6mm", LCSC="C2687402")
    l[1] += sw
    l[2] += v5
    cout = C("22u", C1206)
    cout[1] += v5
    cout[2] += gnd
    rt = R("100k")
    rt[1] += v5
    rt[2] += fb
    rb = R("24.9k")
    rb[1] += fb
    rb[2] += gnd

    # 3.3V：内部用と固定出力用で LDO を分ける（D13）
    for out in (v3_int, v3_out):
        ldo = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U", value="AMS1117-3.3",
                        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2", LCSC="C6186")
        ldo["VI"] += v5
        ldo["VO"] += out
        ldo["GND"] += gnd
        ci = C("10u", C0805)
        ci[1] += v5
        ci[2] += gnd
        co = C("22u", C0805)
        co[1] += out
        co[2] += gnd
