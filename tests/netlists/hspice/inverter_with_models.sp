* untitled
.model nch nmos level=49 tox=9n vth0=0.4
.model pch pmos level=49 tox=9n vth0=-0.4
.subckt cmos_inverter in_ out vdd vss
M1 out in_ vdd vdd pch L=0.18u W=1u
M2 out in_ vss vss nch L=0.18u W=0.5u
.ends cmos_inverter
.end
