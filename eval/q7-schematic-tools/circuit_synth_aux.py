from circuit_synth import circuit, Component, Net

def R(v): return Component(symbol="Device:R", ref="R1", value=v, footprint="Resistor_SMD:R_0603_1608Metric")
def C(v, fp="Capacitor_SMD:C_0805_2012Metric"): return Component(symbol="Device:C", ref="C1", value=v, footprint=fp)

@circuit(name="aux")
def aux():
    vin, v5, v3, gnd = Net("VIN"), Net("+5V"), Net("+3V3"), Net("GND")
    sw, boot, fb, vcc = Net("SW"), Net("BOOT"), Net("FB"), Net("VCC")
    j = Component(symbol="Connector:Barrel_Jack", ref="J1", footprint="Connector_BarrelJack:BarrelJack_Horizontal")
    j[1] += vin; j[2] += gnd
    d = Component(symbol="Device:D_TVS", ref="D1", value="SMAJ22A", footprint="Diode_SMD:D_SMA")
    d[1] += vin; d[2] += gnd
    u1 = Component(symbol="Regulator_Switching:LMR33630ADDA", ref="U1", value="LMR33630ADDAR", footprint="Package_SO:TI_SO-PowerPAD-8_ThermalVias")
    u1["VIN"] += vin; u1["EN"] += vin; u1["GND"] += gnd; u1["SW"] += sw; u1["BOOT"] += boot; u1["FB"] += fb; u1["VCC"] += vcc
    c1=C("10u"); c1[1]+=vin; c1[2]+=gnd
    c2=C("100n","Capacitor_SMD:C_0603_1608Metric"); c2[1]+=boot; c2[2]+=sw
    c3=C("1u","Capacitor_SMD:C_0603_1608Metric"); c3[1]+=vcc; c3[2]+=gnd
    l = Component(symbol="Device:L", ref="L1", value="10u", footprint="Inductor_SMD:L_Bourns_SRP7028A")
    l[1]+=sw; l[2]+=v5
    c4=C("22u"); c4[1]+=v5; c4[2]+=gnd
    r1=R("100k"); r1[1]+=v5; r1[2]+=fb
    r2=R("24.9k"); r2[1]+=fb; r2[2]+=gnd
    u2 = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U2", value="AMS1117-3.3", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
    u2["VI"]+=v5; u2["VO"]+=v3; u2["GND"]+=gnd
    c5=C("10u"); c5[1]+=v3; c5[2]+=gnd

if __name__ == "__main__":
    c = aux()
    c.generate_kicad_project(project_name="aux_cs", generate_pcb=False)
