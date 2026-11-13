"""最上位の回路。ブロック（サブ回路）をつなぐ。"""
from circuit_synth import Net, circuit

from .aux_power import aux_power
from .var_power import var_power


@circuit(name="tune_jam_psu")
def top():
    vin, gnd = Net("VIN"), Net("GND")
    v5, v3_int, v3_out = Net("+5V"), Net("+3V3"), Net("+3V3_OUT")
    var_out = Net("VAR_OUT")
    aux_power(vin, gnd, v5, v3_int, v3_out)
    # MCU とつなぐネット（MCU ブロックはまだない）
    var_power(vin, gnd, v5, v3_int, var_out,
              Net("DAC1"), Net("DAC2"), Net("INJ_EN"), Net("OUT_OFF"), Net("CP_PWM"),
              Net("LATCH_RST"), Net("SHORT_N"), Net("PG_VAR"),
              Net("ADC_VBUCK"), Net("ADC_VOUT"), Net("ADC_IOUT"))
