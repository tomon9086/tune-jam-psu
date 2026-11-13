"""MCU（STM32G071C8T6）と操作部：OLED、エンコーダ、出力ボタン、LED、NTC、SWD、UART。

要件：UI-01〜13、MTR-01〜07、FW-01/02、PRT-07、PRT-12、TST-01、D14、D20

記号：KiCad 標準ライブラリに STM32G071 の 48 ピン品がないので、STM32G061C8Tx を使う。
データシート（DS12232、Figure 5・Table 12）と全ピンを照合し、46 本が一致。違いは 29・32 番
（G061 の記号では未接続、G071 では PA9・PA10）だけで、29・32・33・34 番は使わない。

ピンの割り当て（データシートの代替機能表 Table 13・14 で確認）：
  PA0 ADC_IN0  ← ADC_VOUT      PA4 DAC_OUT1 → DAC1（Vset）   PA8  TIM1_CH1 → CP_PWM
  PA1 ADC_IN1  ← ADC_IOUT      PA5 DAC_OUT2 → DAC2（Iset）   PB8  I2C1_SCL → OLED
  PB0 ADC_IN8  ← ADC_VBUCK     PA6 TIM3_CH1 ← エンコーダ A   PB9  I2C1_SDA → OLED
  PB1 ADC_IN9  ← ADC_VIN       PA7 TIM3_CH2 ← エンコーダ B   PA2/PA3 USART2 TX/RX（テストパッド）
  PB2 ADC_IN10 ← ADC_NTC       PA13 SWDIO / PA14 SWCLK       PF2 NRST
  GPIO：PB3 INJ_EN、PB4 OUT_OFF、PB5 LATCH_RST、PB6 SHORT_N（入力）、PB7 PG_VAR（入力）、
        PB10 エンコーダ押し、PB11 出力ボタン、PB12 出力 LED
"""
from circuit_synth import Component, Net, circuit

from .parts import C, R, hand

TP = "TestPoint:TestPoint_Pad_D1.5mm"


def rc_input(src, mcu_pin, v3, gnd):
    """スイッチ入力の RC（UI-13）：10k プルアップ、10k 直列、10nF。"""
    r = R("10k"); r[1] += v3; r[2] += src
    r = R("10k"); r[1] += src; r[2] += mcu_pin
    c = C("10n"); c[1] += mcu_pin; c[2] += gnd


@circuit(name="mcu_ui")
def mcu_ui(gnd, v3, vin,
           dac1, dac2, inj_en, out_off, cp_pwm, latch_rst, short_n, pg_var,
           adc_vbuck, adc_vout, adc_iout):
    vref, nrst, scl, sda = Net("VREF"), Net("NRST"), Net("I2C_SCL"), Net("I2C_SDA")
    swdio, swclk, tx, rx = Net("SWDIO"), Net("SWCLK"), Net("UART_TX"), Net("UART_RX")
    adc_vin, adc_ntc = Net("ADC_VIN"), Net("ADC_NTC")
    enc_a, enc_b, enc_sw, btn, led = Net("ENC_A"), Net("ENC_B"), Net("ENC_SW"), Net("BTN_OUT"), Net("LED_OUT")

    u = Component(symbol="MCU_ST_STM32G0:STM32G061C8Tx", ref="U", value="STM32G071C8T6",
                  footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm", LCSC="C529341")
    u["VDD"] += v3; u["VBAT"] += v3; u["VSS"] += gnd; u["VREF+"] += vref; u["PF2"] += nrst
    for pin, net in (("PA0", adc_vout), ("PA1", adc_iout), ("PB0", adc_vbuck), ("PB1", adc_vin), ("PB2", adc_ntc),
                     ("PA4", dac1), ("PA5", dac2), ("PA8", cp_pwm), ("PB8", scl), ("PB9", sda),
                     ("PA2", tx), ("PA3", rx), ("PA13", swdio), ("PA14", swclk),
                     ("PB3", inj_en), ("PB4", out_off), ("PB5", latch_rst), ("PB6", short_n), ("PB7", pg_var),
                     ("PA6", enc_a), ("PA7", enc_b), ("PB10", enc_sw), ("PB11", btn), ("PB12", led)):
        u[pin] += net
    for v in ("100n", "100n", "4.7u"):
        c = C(v); c[1] += v3; c[2] += gnd
    # VREF+：10Ω と 1µF ＋ 100nF で VDD から分ける（DAC と ADC の基準）
    r = R("10"); r[1] += v3; r[2] += vref
    for v in ("1u", "100n"):
        c = C(v); c[1] += vref; c[2] += gnd
    c = C("100n"); c[1] += nrst; c[2] += gnd

    # ADC：入力電圧（25V で 2.68V）と NTC（10k の分圧）
    r = R("100k"); r[1] += vin; r[2] += adc_vin
    r = R("12k"); r[1] += adc_vin; r[2] += gnd
    c = C("100n"); c[1] += adc_vin; c[2] += gnd
    r = R("10k"); r[1] += vref; r[2] += adc_ntc
    ntc = hand("Device:Thermistor_NTC", "TH", "103AT-2", "Resistor_THT:R_Axial_DIN0204_L3.6mm_D1.6mm_P2.54mm_Vertical",
               "秋月 107258（DigiKey 4316-103AT-2-ND）")   # TODO: フットプリント（P3）。付けるかは発注ごとに選ぶ
    ntc[1] += adc_ntc; ntc[2] += gnd
    c = C("100n"); c[1] += adc_ntc; c[2] += gnd

    # OLED（0.96" SSD1306、I2C、4 ピン：GND、VCC、SCL、SDA の順の品を買う。D14）
    oled = hand("Connector_Generic:Conn_01x04", "J", "OLED", "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical",
                "0.96インチ SSD1306 I2C モジュール（GND/VCC/SCL/SDA の順）")
    oled[1] += gnd; oled[2] += v3; oled[3] += scl; oled[4] += sda
    for n in (scl, sda):
        r = R("4.7k"); r[1] += v3; r[2] += n

    # エンコーダ（EC11、押しボタン付き）と出力ボタン：RC でチャタリングを抑える（UI-13）
    enc = hand("Device:RotaryEncoder_Switch", "SW", "EC11", "Rotary_Encoder:RotaryEncoder_Alps_EC11E-Switch_Vertical_H20mm",
               "EC11 系（押しボタン付き、クリックあり）")
    ea, eb, es = Net("ENC_A_RAW"), Net("ENC_B_RAW"), Net("ENC_SW_RAW")
    enc["A"] += ea; enc["B"] += eb; enc["C"] += gnd; enc["S1"] += es; enc["S2"] += gnd
    rc_input(ea, enc_a, v3, gnd); rc_input(eb, enc_b, v3, gnd); rc_input(es, enc_sw, v3, gnd)
    sw = hand("Switch:SW_Push", "SW", "OUTPUT", "Button_Switch_THT:SW_PUSH_6mm", "タクトスイッチ 6mm")
    bs = Net("BTN_OUT_RAW")
    sw[1] += bs; sw[2] += gnd
    rc_input(bs, btn, v3, gnd)

    # 出力 ON の LED
    lk = Net("LED_K")
    r = R("1k"); r[1] += led; r[2] += Net("LED_A")
    d = Component(symbol="Device:LED", ref="D", value="LED", footprint="LED_SMD:LED_0603_1608Metric", LCSC="TODO")
    d["A"] += Net("LED_A"); d["K"] += gnd

    # SWD（WCH-Link / ST-Link 用、FW-01）と UART のテストパッド（FW-02）
    swd = hand("Connector_Generic:Conn_01x05", "J", "SWD", "Connector_PinHeader_2.54mm:PinHeader_1x05_P2.54mm_Vertical",
               "ピンヘッダ 1x5")
    swd[1] += v3; swd[2] += swclk; swd[3] += gnd; swd[4] += swdio; swd[5] += nrst
    for n in (tx, rx):
        tp = Component(symbol="Connector:TestPoint", ref="TP", value=str(n.name), footprint=TP, Assembly="HAND",
                       Supplier="パッドのみ（部品なし）")
        tp[1] += n
