export default () => (
  <board width="40mm" height="30mm">
    <chip name="J1" footprint="pinrow2" pinLabels={{ pin1: "VIN", pin2: "GND" }} />
    <diode name="D1" footprint="smb" connections={{ cathode: "net.VIN", anode: "net.GND" }} />
    <chip
      name="U1"
      footprint="soic8"
      supplierPartNumbers={{ jlcpcb: ["C841384"] }}
      manufacturerPartNumber="LMR33630ADDAR"
      pinLabels={{ pin1: "PGND", pin2: "VIN", pin3: "EN", pin4: "PG", pin5: "FB", pin6: "VCC", pin7: "BOOT", pin8: "SW" }}
      connections={{ VIN: "net.VIN", EN: "net.VIN", PGND: "net.GND", FB: "net.FB", VCC: "net.VCC", BOOT: "net.BOOT", SW: "net.SW" }}
      noConnect={["PG"]}
    />
    <capacitor name="C1" capacitance="10uF" footprint="0805" connections={{ pin1: "net.VIN", pin2: "net.GND" }} />
    <capacitor name="C2" capacitance="100nF" footprint="0603" connections={{ pin1: "net.BOOT", pin2: "net.SW" }} />
    <capacitor name="C3" capacitance="1uF" footprint="0603" connections={{ pin1: "net.VCC", pin2: "net.GND" }} />
    <inductor name="L1" inductance="10uH" footprint="1210" supplierPartNumbers={{ jlcpcb: ["C2687402"] }} connections={{ pin1: "net.SW", pin2: "net.V5" }} />
    <capacitor name="C4" capacitance="22uF" footprint="0805" connections={{ pin1: "net.V5", pin2: "net.GND" }} />
    <resistor name="R1" resistance="100k" footprint="0603" connections={{ pin1: "net.V5", pin2: "net.FB" }} />
    <resistor name="R2" resistance="24.9k" footprint="0603" connections={{ pin1: "net.FB", pin2: "net.GND" }} />
    <chip
      name="U2"
      footprint="sot223"
      supplierPartNumbers={{ jlcpcb: ["C6186"] }}
      pinLabels={{ pin1: "GND", pin2: "VO", pin3: "VI" }}
      connections={{ VI: "net.V5", VO: "net.V3V3", GND: "net.GND" }}
    />
    <capacitor name="C5" capacitance="10uF" footprint="0805" connections={{ pin1: "net.V3V3", pin2: "net.GND" }} />
    <trace from=".J1 > .VIN" to="net.VIN" />
    <trace from=".J1 > .GND" to="net.GND" />
  </board>
)
