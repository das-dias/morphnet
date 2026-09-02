from __future__ import annotations

from morphnet.morphnet_schema import Connection, PortReference, SignalDomain

# Type alias: net name → list of port references on that net
NetMap = dict[str, list[PortReference]]


def net_map_to_connections(net_map: NetMap) -> list[Connection]:
    """Convert a net-based connectivity map to point-to-point Connection objects.

    For each net with N port references, produces N-1 Connection objects.
    The first port reference (in insertion order) becomes the source for
    all connections on that net.

    Complexity: O(n) where n = total port references across all nets.
    """
    connections: list[Connection] = []
    for net_name, port_refs in net_map.items():
        if len(port_refs) < 2:
            continue
        source = port_refs[0]
        for target in port_refs[1:]:
            connections.append(
                Connection(
                    name=net_name,
                    source=source,
                    target=target,
                    domain=SignalDomain.UNSPECIFIED,
                )
            )
    return connections


def connections_to_instance_nets(
    connections: list[Connection],
) -> dict[tuple[str, str], str]:
    """Build (instance_name, port_name) → net_name lookup from Connection objects.

    Single pass over connections — O(n).  Used by writers to reconstruct
    instance lines with the correct net names in port order.
    """
    mapping: dict[tuple[str, str], str] = {}
    for conn in connections:
        net_name = conn.name
        if conn.source is not None:
            key = (conn.source.instance_name, conn.source.port_name)
            mapping[key] = net_name
        if conn.target is not None:
            key = (conn.target.instance_name, conn.target.port_name)
            mapping[key] = net_name
    return mapping


def add_port_to_net(
    net_map: NetMap,
    net_name: str,
    instance_name: str,
    port_name: str,
) -> None:
    """Register a port reference on a net — O(1) amortized."""
    ref = PortReference(instance_name=instance_name, port_name=port_name)
    if net_name not in net_map:
        net_map[net_name] = []
    net_map[net_name].append(ref)
