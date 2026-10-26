"""Phase 1 — Zero-Trust Physics Proxy (in-flight interceptor).

Sits in front of the device controllers. Even a perfectly *authenticated*
command is refused if obeying it would push the plant past a physical limit —
the "authorized but dangerous" case: the attacker owns the backend, the command
is well-formed, but the physics says no. The proxy never trusts a reported
sensor value; it checks the *commanded* action against static physical limits.

Wired into the charger current path and the microgrid load-shed path
(`targets/charger.py`, `targets/microgrid.py`) when a scenario sets `proxy:`.
On a refusal it logs a `control / reject` event so the defence is visible in
the trace and the 3D damage report.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PhysicsProxy:
    thermal_limit_A: float = 160.0   # max safe continuous current per charger
    grid_max_kW: float = 500.0       # max total power the hub may carry
    v_min_pu: float = 0.94           # minimum allowed bus voltage

    # ---- charger current limit (defends overcurrent + mass_command) --------
    def guard_current(self, store, t, node, amps, cause=None):
        """Return the approved current. Over-limit commands are clamped to the
        safe continuous limit and a reject event is logged."""
        if amps is None or amps <= self.thermal_limit_A:
            return amps
        store.add(t=t, layer="control", node=node, kind="reject", field="limit_A",
                  value=round(self.thermal_limit_A, 1), caused_by=cause,
                  flag="modelled")
        return self.thermal_limit_A

    # ---- load-shed / safety signal (defends suppression + desync drop) -----
    def guard_load_shed(self, store, t, node, wanted, delivered, cause=None):
        """Refuse to let a needed load-shed signal be dropped. If the hub wanted
        to shed (wanted < 1.0) but the delivered signal was blackholed (None),
        re-apply the shed and log the refusal."""
        if delivered is None and wanted is not None and wanted < 1.0:
            store.add(t=t, layer="control", node=node, kind="reject", field="load_shed",
                      value=round(wanted, 2), caused_by=cause, flag="modelled")
            return wanted
        return delivered


if __name__ == "__main__":  # ponytail: one runnable check
    from ..core.events import EventStore
    s = EventStore()
    p = PhysicsProxy(thermal_limit_A=150)
    assert p.guard_current(s, 1, "c1", 125) == 125          # safe passes
    assert p.guard_current(s, 1, "c1", 250) == 150          # over-limit clamped
    assert p.guard_load_shed(s, 1, "hub", 0.5, None) == 0.5  # dropped shed restored
    assert any(e.kind == "reject" for e in s.all())
    print("proxy ok")
