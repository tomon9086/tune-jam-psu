"""最上位の回路。ブロック（サブ回路）をつなぐ。"""
from circuit_synth import Net, circuit

from .aux_power import aux_power
from .mcu_ui import mcu_ui
from .rails import rails
from .var_power import var_power


@circuit(name="tune_jam_psu")
def top():
    vin, gnd = Net("VIN"), Net("GND")
    v5, v3, v3_out, var_out = Net("+5V"), Net("+3V3"), Net("+3V3_OUT"), Net("VAR_OUT")
    mcu = dict(dac1=Net("DAC1"), dac2=Net("DAC2"), inj_en=Net("INJ_EN"), out_off=Net("OUT_OFF"),
               cp_pwm=Net("CP_PWM"), latch_rst=Net("LATCH_RST"), short_n=Net("SHORT_N"), pg_var=Net("PG_VAR"),
               adc_vbuck=Net("ADC_VBUCK"), adc_vout=Net("ADC_VOUT"), adc_iout=Net("ADC_IOUT"))
    aux_power(vin, gnd, v5, v3, v3_out)
    var_power(vin, gnd, v5, v3, var_out, **mcu)
    mcu_ui(gnd, v3, vin, **mcu)
    rails(gnd, var_out, v5, v3_out)
