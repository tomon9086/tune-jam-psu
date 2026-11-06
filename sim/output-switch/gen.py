#!/usr/bin/env python3
"""出力スイッチ（N-FET バックツーバック＋チャージポンプ）の ngspice ネットリストを作る。

使い方（このディレクトリで）:
    python3 gen.py && for f in case_*.cir; do ngspice -b $f; done
"""
import sys
def net(vin,vout,name,extra=''):
    return f"""* output switch {name}: VIN={vin} Vout={vout}
.include models.lib
VIN vin 0 {vin}
* 降圧の出力（理想電圧源＋内部抵抗）
VB buck 0 {vout}
RB buck bout 5m
CB bout 0 44u
* MCU の PWM（3.3V、100kHz）
VPWM pwm 0 PULSE(0 3.3 0 20n 20n 4.98u 10u)
* チャージポンプ（VIN の上に積む）：CP ~= VIN + 3.3 - 2Vf
C1 pwm a 100n
D1 vin a BAV99
D2 a cp BAV99
C2 cp vin 100n
* ゲート駆動：CP から 100k、Vgs をツェナーで 10V にクランプ
RG cp g 100k
DZ s g Z10V
* バックツーバック（ソース共通）
M1 bout g s AO3400A
M2 out g s AO3400A
* OFF 用のプルダウン（LM393 のオープンコレクタ / MCU の代わり）。t>=2ms で ON
SOFF g 0 ctl 0 SWOFF
VCTL ctl 0 PULSE(0 1 2m 10n 10n 10 20)
.model SWOFF SW(Ron=20 Roff=1G Vt=0.5 Vh=0.1)
* 負荷 2A
RL out 0 {vout/2 if vout>0 else 1}
COUT out 0 1u
{extra}
.tran 20n 2.2m 0 50n uic
.control
run
let vgs=v(g)-v(s)
let vcpx=v(cp)-v(vin)
let vdr=v(bout)-v(out)
meas tran vgs_on AVG vgs from=1.8m to=2m
meas tran vcp AVG vcpx from=1.8m to=2m
meas tran vdrop AVG vdr from=1.8m to=2m
meas tran vout_on AVG v(out) from=1.8m to=2m
meas tran ton WHEN v(out)={0.9*vout} RISE=1
meas tran toff WHEN v(out)={0.1*vout} FALL=1
meas tran t90 WHEN vgs=3 RISE=1
let ib=-i(VB)
meas tran ioff WHEN ib=0.2 FALL=LAST
meas tran vgsmin MIN vgs from=2m to=2.2m
meas tran vgsmax MAX vgs from=0 to=2m
print vdrop
.endc
.end
"""
cases=[(20,0.8),(20,5),(20,12),(15,12),(12,10),(9,7)]
for vin,vout in cases:
    n=f"case_v{vin}_{str(vout).replace('.','p')}"
    open(n+'.cir','w').write(net(vin,vout,n))
    print(n)
