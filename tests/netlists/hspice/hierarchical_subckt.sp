* untitled
.subckt inverter in_ out vdd vss
R1 in_ out 1k
R2 out vss 1k
.ends inverter
.subckt buffer a b vdd vss
X1 a mid vdd vss inverter
X2 mid b vdd vss inverter
.ends buffer
.end
