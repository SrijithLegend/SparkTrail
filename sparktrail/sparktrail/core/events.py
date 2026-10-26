"""Event store: the single append-only log that the whole sim writes to.

The trace IS the product. Every module emits Events; `caused_by` links them
into a propagation graph (injector -> control -> physics -> threshold).
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field, asdict
from typing import Optional

import networkx as nx

_ids = itertools.count(1)


@dataclass
class Event:
    t: float                      # sim seconds
    layer: str                    # attack | cyber | control | physics | monitor
    node: str                     # e.g. "charger_01", "hub_tx"
    kind: str                     # command | reading | state | alert
    field: str                    # "limit_A", "pack_temp_C", ...
    value: object                 # float | str
    caused_by: Optional[str] = None
    flag: str = "modelled"        # modelled | illustrative  (honesty in UI)
    id: str = field(default_factory=lambda: f"e{next(_ids)}")
    # Phase 3 — propagation tracking: hops from the root attack (root = 0) and
    # the node where this causal chain began. The 3D heatmap colours by depth.
    propagation_depth: int = 0
    source_node: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)


class EventStore:
    """Append-only list of events plus a DiGraph builder for replay."""

    def __init__(self) -> None:
        self._events: list[Event] = []
        self._by_id: dict[str, Event] = {}

    def emit(self, ev: Event) -> Event:
        # Phase 3: derive propagation depth / source node from the parent event.
        parent = self._by_id.get(ev.caused_by) if ev.caused_by else None
        if parent is None:
            ev.propagation_depth = 0
            ev.source_node = ev.node
        else:
            ev.propagation_depth = parent.propagation_depth + 1
            ev.source_node = parent.source_node or ev.node
        self._events.append(ev)
        self._by_id[ev.id] = ev
        return ev

    def add(self, **kw) -> Event:
        return self.emit(Event(**kw))

    def all(self) -> list[Event]:
        return list(self._events)

    def _root(self, ev: Event) -> Event:
        cur = ev
        while cur.caused_by and cur.caused_by in self._by_id:
            cur = self._by_id[cur.caused_by]
        return cur

    def node_depths(self) -> dict[str, int]:
        """Shallowest propagation depth per node among attack-rooted chains.
        depth 0 = root cause, 1 = direct impact, 2+ = cascade. Benign chains
        are ignored so an un-attacked node never lights up as a root cause."""
        depths: dict[str, int] = {}
        for e in self._events:
            if self._root(e).layer != "attack":
                continue
            if e.node not in depths or e.propagation_depth < depths[e.node]:
                depths[e.node] = e.propagation_depth
        return depths

    def graph(self) -> nx.DiGraph:
        g = nx.DiGraph()
        for ev in self._events:
            g.add_node(ev.id, **ev.as_dict())
        for ev in self._events:
            if ev.caused_by:
                g.add_edge(ev.caused_by, ev.id)
        return g

    def to_json(self) -> list[dict]:
        return [ev.as_dict() for ev in self._events]
