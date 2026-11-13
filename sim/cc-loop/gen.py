#!/usr/bin/env python3
"""CC ループ（INA180A1 ＋ MCP6002 ＋ FB 注入）のシミュレーション用ネットリストを作る。

LMR33630A は TI のモデル（sim/lmr33630/get_model.sh で取得）。INA180A1 と MCP6002 は
データシートの特性に合わせた簡易モデル（VER-07 の「理想化モデルで代用してよい」）。
起動の 4ms を省くため、ソフトスタートを終えた状態（MODE=1.25）から始める。

条件：VIN 20V、Vset 5V、Iset 1A。0.6ms で負荷 2.5A 相当をつなぎ、1.6ms で外す。
"""
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
MODEL = "../lmr33630/models/lmr33630a_ng.lib"

# FB 注入（hw/calc/var_network.py と同じ値）
R1, R2, RA, RB, RINJ = "100k", "500k", "14.7k", "7.5k", "2.7k"
VDAC1 = 2.097   # Vset 5V
VDAC2 = 0.867   # Iset 1A（0.2V の下駄 + 0.667V/A × 1A）

VARIANTS = {
    # 名前: (Ri, Rf, Cf, Rcc, Chold)
    #   CC アンプ：反転入力に DAC2 を Ri で入れ、帰還に Rf + Cf（PI）
    #   Chold：ダイオードの後ろ（CC_D）と GND の間のコンデンサ。CC を抜くときに注入をゆっくり減らし、
    #          降圧 IC の行き過ぎを抑える（かけるときはダイオード経由ですぐ充電される）
    "a_slow": ("10k", "4.7k", "10n", "10k", None),
    "b_mid": ("10k", "10k", "2.2n", "10k", None),
    "c_fast": ("10k", "22k", "1n", "10k", None),
    "d_mid_h4n7": ("10k", "10k", "2.2n", "10k", "4.7n"),
    "e_mid_h10n": ("10k", "10k", "2.2n", "10k", "10n"),
    "f_fast_h10n": ("10k", "22k", "1n", "10k", "10n"),
}

TEMPLATE = """* CC loop {name}
.include {model}
VIN vin 0 20
CIN vin 0 10u
X1 0 boot en fb pg 0 sw vcc vin LMR33630A_TRANS PARAMS: MODE=1.25 FASTSS=0
REN vin en 100k
CBOOT boot sw 100n
CVCC vcc 0 1u
RPG pg vcc 100k
L1 sw bout 10u
COUT bout 0 44u IC=5
* シャント 33.3mOhm（100mOhm × 3 並列）
RSH bout vs 33.3m
* 出力（スイッチは理想として省略）。負荷：常時 10Ω、0.6〜1.6ms に 2.5Ω を追加
RL1 vs 0 10
SLD vs ld ctl 0 SWL
RL2 ld 0 2.5
VCTL ctl 0 PWL(0 0 0.6m 0 0.601m 1 1.6m 1 1.601m 0)
.model SWL SW(Ron=1m Roff=1G Vt=0.5 Vh=0.1)
* FB の分圧（VS から。シャントの電圧降下は補償される）
R1 vs fb {r1}
R2 fb 0 {r2}
* Vset 注入（DAC1 → Ra/Rb → Rinj → INJ スイッチ（ON）→ FB）
VDAC1 dac1 0 {vdac1}
RA dac1 th {ra}
RB th 0 {rb}
RINJ th inj {rinj}
RSWINJ inj fb 1
* INA180A1：ゲイン 20、帯域 350kHz、出力 0〜4.97V（電源 5V）
BCSA csa_raw 0 V = max(0, min(4.97, 20*(V(bout)-V(vs))))
RCSA csa_raw csa 1k
CCSA csa 0 455p
* 下駄 0.2V（VDDA の分圧。ここでは理想電圧源で足す）
BOFF csp 0 V = V(csa) + 0.2
* MCP6002（CC アンプ）：GBW 1MHz（A0 = 1e5、主極 10Hz）、出力 0〜5V（RRIO）
* 内部の主極の電圧を −1〜6V に制限する（制限しないと出力が張り付いている間に内部の値がたまり続け、
* 戻るのに 150µs かかる。本物のオペアンプの内部電圧は電源の範囲を大きく超えない）
VDAC2 dac2 0 {vdac2}
RI dac2 inn {ri}
RF inn fbn {rf}
CF fbn ccout {cf}
BOA oa_int 0 V = 1e5*(V(csp)-V(inn))
ROA oa_int oa_p 1k
COA oa_p 0 15.9u
DOAH oa_p oah DID
VOAH oah 0 6
DOAL oal oa_p DID
VOAL oal 0 -1
.model DID D(Is=1e-14 N=0.05)
BOUT ccout 0 V = max(0.02, min(4.98, V(oa_p)))
* ダイオード（1N4148W 相当）＋ Rcc で INJ スイッチの手前に注入
DCC ccout ccd D4148
RCC ccd inj {rcc}
{chold}
.model D4148 D(Is=2.5n N=1.75 Rs=0.6 Cjo=2p)
.save v(vs) v(bout) i(L1) v(csa) v(ccout) v(fb)
.tran 10n 2.4m 0 20n uic
.control
run
wrdata {name}.txt v(vs) i(L1) v(csa) v(ccout) v(fb)
.endc
.end
"""


def main():
    for name, (ri, rf, cf, rcc, chold) in VARIANTS.items():
        (HERE / f"{name}.cir").write_text(TEMPLATE.format(
            name=name, model=MODEL, r1=R1, r2=R2, ra=RA, rb=RB, rinj=RINJ, vdac1=VDAC1, vdac2=VDAC2,
            ri=ri, rf=rf, cf=cf, rcc=rcc, chold=f"CHOLD ccd 0 {chold}" if chold else "* Chold なし"))
        print(name)


if __name__ == "__main__":
    main()
