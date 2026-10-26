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

    def as_dict(self) -> dict:
        return asdict(self)


class EventStore:
    """Append-only list of events plus a DiGraph builder for replay."""

    def __init__(self) -> None:
        self._events: list[Event] = []

    def emit(self, ev: Event) -> Event:
        self._events.append(ev)
        return ev

    def add(self, **kw) -> Event:
        return self.emit(Event(**kw))

    def all(self) -> list[Event]:
        return list(self._events)

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
