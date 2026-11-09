"""最上位の回路。ブロック（サブ回路）をつなぐ。"""
from circuit_synth import Net, circuit

from .aux_power import aux_power


@circuit(name="tune_jam_psu")
def top():
    vin, gnd = Net("VIN"), Net("GND")
    v5, v3_int, v3_out = Net("+5V"), Net("+3V3"), Net("+3V3_OUT")
    aux_power(vin, gnd, v5, v3_int, v3_out)
