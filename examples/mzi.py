"""
Mach-Zehnder Interferometer (MZI) photonic circuit.

Demonstrates:
- Photonic domain (SignalDomain.WAVEGUIDE) on terminals
- Hierarchical design: dc_coupler sub-cell assembled into mzi top cell
- External waveguide modules from a PDK library
- parameter defaults as (name, value) tuples
- build up using connect() chaining
"""
import morphnet

# --------------------------------------------------------------------------
# DC coupler sub-cell (50/50 directional coupler)
# --------------------------------------------------------------------------

dc = morphnet.module("dc_coupler", parameters=[("gap", 200e-9), ("length", 10e-6)])
for name in ("i1", "i2", "o1", "o2"):
    direction = (
        morphnet.PortDirection.INPUT if name.startswith("i") else morphnet.PortDirection.OUTPUT
    )
    dc.add_terminal(name, direction=direction, domain=morphnet.SignalDomain.WAVEGUIDE)

dc.add(morphnet.module_reference("wg_coupler", "wg_directional_coupler"))
dc.connect("wg_in1", ("", "i1"), ("wg_coupler", "i1"))
dc.connect("wg_in2", ("", "i2"), ("wg_coupler", "i2"))
dc.connect("wg_out1", ("wg_coupler", "o1"), ("", "o1"))
dc.connect("wg_out2", ("wg_coupler", "o2"), ("", "o2"))

# --------------------------------------------------------------------------
# MZI top cell — two couplers connected by delay arms
# --------------------------------------------------------------------------

mzi = morphnet.module("mzi", parameters=[("arm_length", 100e-6)])
mzi.add_terminal("in1", direction=morphnet.PortDirection.INPUT, domain=morphnet.SignalDomain.WAVEGUIDE)
mzi.add_terminal("in2", direction=morphnet.PortDirection.INPUT, domain=morphnet.SignalDomain.WAVEGUIDE)
mzi.add_terminal("out1", direction=morphnet.PortDirection.OUTPUT, domain=morphnet.SignalDomain.WAVEGUIDE)
mzi.add_terminal("out2", direction=morphnet.PortDirection.OUTPUT, domain=morphnet.SignalDomain.WAVEGUIDE)

mzi.add(
    morphnet.module_reference("dc1", "dc_coupler"),
    morphnet.module_reference("dc2", "dc_coupler"),
    morphnet.module_reference("arm_top", "wg_delay"),
    morphnet.module_reference("arm_bot", "wg_delay"),
)

# Input coupling
mzi.connect("port_in1", ("", "in1"), ("dc1", "i1"))
mzi.connect("port_in2", ("", "in2"), ("dc1", "i2"))

# Delay arms between couplers
mzi.connect("arm_top_wg", ("dc1", "o1"), ("arm_top", "inp"), ("dc2", "i1"))
mzi.connect("arm_bot_wg", ("dc1", "o2"), ("arm_bot", "inp"), ("dc2", "i2"))

# Output coupling
mzi.connect("port_out1", ("dc2", "o1"), ("", "out1"))
mzi.connect("port_out2", ("dc2", "o2"), ("", "out2"))

# --------------------------------------------------------------------------
# Circuit — PDK waveguide library + external modules
# --------------------------------------------------------------------------

pdk_lib = morphnet.external_library(
    "path/to/photonic_pdk.lib",
    model_type="photonic",
    external_model_names=["wg_directional_coupler", "wg_delay"],
)

ckt = morphnet.circuit("mzi_chip", top_module="mzi")
ckt.add_library("photonic_pdk", pdk_lib)
ckt.add_ext(
    morphnet.ext_module(
        "wg_directional_coupler",
        class_name="dc",
        library_name="photonic_pdk",
    ),
    morphnet.ext_module(
        "wg_delay",
        class_name="delay_line",
        library_name="photonic_pdk",
    ),
)
ckt.add(mzi, dc)

# --------------------------------------------------------------------------
# Verify + dump
# --------------------------------------------------------------------------

assert ckt.top_module == "mzi"
assert len(ckt.modules) == 2, f"expected 2 modules, got {len(ckt.modules)}"
assert "photonic_pdk" in ckt.libraries
assert len(ckt.ext_modules) == 2

# Check MZI terminals have waveguide domain
mzi_module = next(m for m in ckt.modules if m.name == "mzi")
for t in mzi_module.ports:
    assert t.domain == morphnet.SignalDomain.WAVEGUIDE, f"terminal {t.name} should be WAVEGUIDE"

print(ckt.to_yaml())
print("mzi.py: all assertions passed")
