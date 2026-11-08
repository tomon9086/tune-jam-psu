import os
os.environ.setdefault('KICAD9_SYMBOL_DIR','/usr/share/kicad/symbols')
os.environ.setdefault('KICAD9_FOOTPRINT_DIR','/usr/share/kicad/footprints')
from skidl import *
set_default_tool(KICAD9)

def R(v, fp='Resistor_SMD:R_0603_1608Metric', lcsc=''):
    r = Part('Device','R', value=v, footprint=fp); r.fields['LCSC']=lcsc; return r
def C(v, fp='Capacitor_SMD:C_0805_2012Metric', lcsc=''):
    c = Part('Device','C', value=v, footprint=fp); c.fields['LCSC']=lcsc; return c

vin, v5, v3, gnd, sw, boot, fb, vcc = Net('VIN'), Net('+5V'), Net('+3V3'), Net('GND'), Net('SW'), Net('BOOT'), Net('FB'), Net('VCC')
j = Part('Connector','Barrel_Jack', footprint='Connector_BarrelJack:BarrelJack_Horizontal')
j[1] += vin; j[2] += gnd
tvs = Part('Device','D_TVS', value='SMAJ22A', footprint='Diode_SMD:D_SMA'); tvs.fields['LCSC']='C41376403'
tvs[1] += vin; tvs[2] += gnd
u1 = Part('Regulator_Switching','LMR33630ADDA', footprint='Package_SO:TI_SO-PowerPAD-8_ThermalVias'); u1.fields['LCSC']='C841384'
u1['VIN'] += vin; u1['EN'] += vin; u1['GND'] += gnd; u1['SW'] += sw; u1['BOOT'] += boot; u1['FB'] += fb; u1['VCC'] += vcc
for p in u1.pins:
    if p.name in ('PG','NC'): p += NC
C('10u', lcsc='')[1,2] += vin, gnd
C('100n')[1,2] += boot, sw
C('1u')[1,2] += vcc, gnd
l = Part('Device','L', value='10u', footprint='Inductor_SMD:L_Bourns_SRP7028A'); l.fields['LCSC']='C2687402'
l[1,2] += sw, v5
C('22u')[1,2] += v5, gnd
R('100k')[1,2] += v5, fb
R('24.9k')[1,2] += fb, gnd
u2 = Part('Regulator_Linear','AMS1117-3.3', footprint='Package_TO_SOT_SMD:SOT-223-3_TabPin2'); u2.fields['LCSC']='C6186'
u2['VI'] += v5; u2['VO'] += v3; u2['GND'] += gnd
C('10u')[1,2] += v3, gnd
pf = Part('power','PWR_FLAG'); pf[1] += vin
pf2 = Part('power','PWR_FLAG'); pf2[1] += gnd
ERC()
generate_netlist(file_='aux.net')
try:
    generate_schematic(filepath='.', top_name='aux')
    print('SCHEMATIC OK')
except Exception as e:
    print('SCHEMATIC FAIL:', type(e).__name__, e)
