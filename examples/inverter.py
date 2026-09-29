"""
Hierarchical ring oscillator built from CMOS inverters.

Demonstrates:
- module() with parameter declarations (names-only and name+default tuples)
- add_terminal() for module I/O
- module_reference() with parameter overrides via kwargs and via parameters list
- connect() with ("", terminal) for parent-level endpoints
- external_library() + add_library() + ext_module() with library_name
- Circuit.add() / add_ext()
"""
import morphnet

# --------------------------------------------------------------------------
# Leaf inverter cell
# --------------------------------------------------------------------------

# Declare parameter names only — no defaults
inv = morphnet.module("inverter", parameters=["l", "w"])
inv.add_terminal("vdd", direction=morphnet.PortDirection.INPUT)
inv.add_terminal("gnd", direction=morphnet.PortDirection.INPUT)
inv.add_terminal("inp", direction=morphnet.PortDirection.INPUT)
inv.add_terminal("out", direction=morphnet.PortDirection.OUTPUT)

# Sub-instances with parameter overrides via kwargs
inv.add(
    morphnet.module_reference("mn", "nfet", l=100e-9, w=500e-9),
    morphnet.module_reference("mp", "pfet", l=100e-9, w=1000e-9),
)

# ("", terminal) = this module's own terminal (parent hierarchical level)
inv.connect("net_out", ("mn", "drain"), ("mp", "drain"), ("", "out"))
inv.connect("net_inp", ("", "inp"), ("mn", "gate"), ("mp", "gate"))
inv.connect("vdd", ("", "vdd"), ("mp", "source"))
inv.connect("gnd", ("", "gnd"), ("mn", "source"))

# --------------------------------------------------------------------------
# Ring oscillator — three inverters chained
# --------------------------------------------------------------------------

ring = morphnet.module("ring_osc")
ring.add_terminal("vdd", direction=morphnet.PortDirection.INPUT)
ring.add_terminal("gnd", direction=morphnet.PortDirection.INPUT)
ring.add_terminal("osc_out", direction=morphnet.PortDirection.OUTPUT)

# One instance overrides w via parameters list; the others use defaults
ring.add(
    morphnet.module_reference("inv1", "inverter", parameters=[("w", 600e-9)]),
    morphnet.module_reference("inv2", "inverter"),
    morphnet.module_reference("inv3", "inverter"),
)
ring.connect("n1", ("inv1", "out"), ("inv2", "inp"))
ring.connect("n2", ("inv2", "out"), ("inv3", "inp"))
ring.connect("n3", ("inv3", "out"), ("inv1", "inp"), ("", "osc_out"))
ring.connect("vdd", ("", "vdd"), ("inv1", "vdd"), ("inv2", "vdd"), ("inv3", "vdd"))
ring.connect("gnd", ("", "gnd"), ("inv1", "gnd"), ("inv2", "gnd"), ("inv3", "gnd"))

# --------------------------------------------------------------------------
# Circuit — declare PDK library and wire everything together
# --------------------------------------------------------------------------

tt_lib = morphnet.external_library(
    "path/to/tt.lib",
    model_type="tt",
    external_model_names=["nfet", "pfet"],
)

ckt = morphnet.circuit("ring_osc_top", top_module="ring_osc")
ckt.add_library("tt", tt_lib)
ckt.add_ext(
    morphnet.ext_module("nfet", class_name="nmos", library_name="tt"),
    morphnet.ext_module("pfet", class_name="pmos", library_name="tt"),
)
ckt.add(ring, inv)

# --------------------------------------------------------------------------
# Verify + dump
# --------------------------------------------------------------------------

assert ckt.top_module == "ring_osc"
assert len(ckt.modules) == 2
assert "tt" in ckt.libraries
assert ckt.libraries["tt"].path == "path/to/tt.lib"
assert len(ckt.ext_modules) == 2

print(ckt.to_yaml())
print("inverter.py: all assertions passed")
