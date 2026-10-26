"""Applies attack events to the right link at the right time.

The sim asks the injector to transform a value as it crosses a modelled link:
  - command path (backend/hub -> charger):  transform_command(field, value, t)
  - sensor path  (sensor -> controller):    transform_reading(field, value, t)

The injector emits one 'attack' Event when each attack first fires, and tags
the returned value's downstream events via last_cause[field].
"""
from __future__ import annotations

from .schema import Attack
from ..core.events import EventStore


class Injector:
    def __init__(self, attacks: list[Attack], store: EventStore) -> None:
        self.attacks = attacks
        self.store = store
        self._fired: dict[str, str] = {}        # attack id -> event id (cause handle)
        self._active_cause: dict[str, str] = {}  # field -> current driving attack event
        self._replay_hold: dict[str, object] = {}       # attack id -> captured stale value
        self._desync_buf: dict[str, list] = {}          # attack id -> [(t, value), ...]

    def _fire(self, atk: Attack, t: float, note: str) -> str:
        if atk.id not in self._fired:
            ev = self.store.add(
                t=t, layer="attack", node=atk.entry_point, kind="command",
                field=atk.field, value=note, caused_by=None,
            )
            self._fired[atk.id] = ev.id
        return self._fired[atk.id]

    def cause_for(self, field: str) -> str | None:
        """Most recent attack-event id that currently drives this field."""
        return self._active_cause.get(field)

    # ---- link transforms -------------------------------------------------
    def transform_command(self, field: str, value, t: float, node: str | None = None):
        for atk in self.attacks:
            if atk.field != field or not atk.active(t):
                continue
            if atk.mechanism == "command_override":
                self._active_cause[field] = self._fire(atk, t, f"{field} -> {atk.to}")
                return atk.to
            if atk.mechanism == "mass_command":
                if atk.targets is None or node in atk.targets:
                    self._active_cause[field] = self._fire(atk, t, f"mass {field} -> {atk.to}")
                    return atk.to
            if atk.mechanism == "dos_blackhole":
                self._active_cause[field] = self._fire(atk, t, f"{field} dropped")
                return None  # message never arrives; caller keeps previous
            if atk.mechanism == "setpoint_drift":
                self._active_cause[field] = self._fire(atk, t, f"{field} drifting")
                return value + (atk.rate_per_s or 0.0) * (t - atk.start_s)
            if atk.mechanism == "replay":
                # capture the last legit value at onset, then re-apply it forever
                # so real updates (a stop/derate command) never land
                if atk.id not in self._replay_hold:
                    self._replay_hold[atk.id] = atk.hold_value if atk.hold_value is not None else value
                self._active_cause[field] = self._fire(atk, t, f"{field} replayed (stale {self._replay_hold[atk.id]})")
                return self._replay_hold[atk.id]
            if atk.mechanism == "desync":
                # release the value presented delay_s ago; the fresh one is held back
                buf = self._desync_buf.setdefault(atk.id, [])
                buf.append((t, value))
                delay = atk.delay_s or 0.0
                released = buf[0][1]
                while len(buf) > 1 and t - buf[0][0] >= delay:
                    released = buf.pop(0)[1]
                self._active_cause[field] = self._fire(atk, t, f"{field} delayed {delay}s")
                return released
        return value

    def transform_reading(self, field: str, value, t: float):
        for atk in self.attacks:
            if atk.field != field or not atk.active(t):
                continue
            if atk.mechanism == "sensor_spoof":
                self._active_cause[field] = self._fire(atk, t, f"{field} held {atk.hold_value}")
                return atk.hold_value
        return value
