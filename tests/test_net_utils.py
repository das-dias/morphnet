from hubnet.hubnet_schema import Connection, PortReference
from hubnet.netlist.net_utils import (
    NetMap,
    add_port_to_net,
    connections_to_instance_nets,
    net_map_to_connections,
)


class TestNetMapToConnections:
    def test_two_port_net(self) -> None:
        net_map: NetMap = {
            "net1": [
                PortReference(instance_name="", port_name="a"),
                PortReference(instance_name="R1", port_name="p"),
            ],
        }
        conns = net_map_to_connections(net_map)
        assert len(conns) == 1
        assert conns[0].name == "net1"
        assert conns[0].source == PortReference(instance_name="", port_name="a")
        assert conns[0].target == PortReference(instance_name="R1", port_name="p")

    def test_three_port_net(self) -> None:
        net_map: NetMap = {
            "vdd": [
                PortReference(instance_name="", port_name="vdd"),
                PortReference(instance_name="R1", port_name="p"),
                PortReference(instance_name="R2", port_name="p"),
            ],
        }
        conns = net_map_to_connections(net_map)
        assert len(conns) == 2
        assert all(c.name == "vdd" for c in conns)
        assert all(c.source.port_name == "vdd" for c in conns)

    def test_single_port_net_produces_no_connections(self) -> None:
        net_map: NetMap = {
            "floating": [PortReference(instance_name="R1", port_name="p")],
        }
        conns = net_map_to_connections(net_map)
        assert conns == []

    def test_empty_net_map(self) -> None:
        assert net_map_to_connections({}) == []

    def test_multiple_nets(self) -> None:
        net_map: NetMap = {
            "a": [
                PortReference(instance_name="", port_name="a"),
                PortReference(instance_name="R1", port_name="p"),
            ],
            "b": [
                PortReference(instance_name="", port_name="b"),
                PortReference(instance_name="R1", port_name="n"),
            ],
        }
        conns = net_map_to_connections(net_map)
        assert len(conns) == 2
        net_names = {c.name for c in conns}
        assert net_names == {"a", "b"}


class TestConnectionsToInstanceNets:
    def test_basic_lookup(self) -> None:
        conns = [
            Connection(
                name="net1",
                source=PortReference(instance_name="", port_name="a"),
                target=PortReference(instance_name="R1", port_name="p"),
            ),
        ]
        mapping = connections_to_instance_nets(conns)
        assert mapping[("", "a")] == "net1"
        assert mapping[("R1", "p")] == "net1"

    def test_multiple_connections(self) -> None:
        conns = [
            Connection(
                name="vin",
                source=PortReference(instance_name="", port_name="vin"),
                target=PortReference(instance_name="R1", port_name="p"),
            ),
            Connection(
                name="vout",
                source=PortReference(instance_name="R1", port_name="n"),
                target=PortReference(instance_name="R2", port_name="p"),
            ),
        ]
        mapping = connections_to_instance_nets(conns)
        assert mapping[("", "vin")] == "vin"
        assert mapping[("R1", "p")] == "vin"
        assert mapping[("R1", "n")] == "vout"
        assert mapping[("R2", "p")] == "vout"

    def test_empty_connections(self) -> None:
        assert connections_to_instance_nets([]) == {}


class TestAddPortToNet:
    def test_creates_new_net(self) -> None:
        net_map: NetMap = {}
        add_port_to_net(net_map, "vdd", "R1", "p")
        assert "vdd" in net_map
        assert len(net_map["vdd"]) == 1

    def test_appends_to_existing_net(self) -> None:
        net_map: NetMap = {}
        add_port_to_net(net_map, "vdd", "R1", "p")
        add_port_to_net(net_map, "vdd", "R2", "p")
        assert len(net_map["vdd"]) == 2


class TestRoundTrip:
    def test_net_map_round_trip(self) -> None:
        """NetMap → Connections → instance_nets lookup → verify consistency."""
        net_map: NetMap = {
            "vin": [
                PortReference(instance_name="", port_name="vin"),
                PortReference(instance_name="R1", port_name="p"),
            ],
            "vout": [
                PortReference(instance_name="", port_name="vout"),
                PortReference(instance_name="R1", port_name="n"),
                PortReference(instance_name="R2", port_name="p"),
            ],
            "gnd": [
                PortReference(instance_name="", port_name="gnd"),
                PortReference(instance_name="R2", port_name="n"),
            ],
        }
        conns = net_map_to_connections(net_map)
        inst_nets = connections_to_instance_nets(conns)

        # Verify all port refs map to correct net names
        assert inst_nets[("", "vin")] == "vin"
        assert inst_nets[("R1", "p")] == "vin"
        assert inst_nets[("R1", "n")] == "vout"
        assert inst_nets[("R2", "p")] == "vout"
        assert inst_nets[("R2", "n")] == "gnd"
