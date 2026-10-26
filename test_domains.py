"""Checks for the multi-domain layer. Run: python test_domains.py"""
from sparktrail.domains import REGISTRY, CASE_STUDIES
from sparktrail.domains.base import bfs_depths


def test_registry_has_six_domains():
    assert set(REGISTRY) == {"ev_hub", "power_sub", "water", "robot_cell", "hvac", "pipeline"}


def test_bfs_depths():
    d = bfs_depths([["A", "B"], ["B", "C"], ["B", "D"]], "A")
    assert d == {"A": 0, "B": 1, "C": 2, "D": 2}


def test_every_scene_builds_and_has_shape():
    for did, dom in REGISTRY.items():
        sc = dom.scene()
        assert sc["nodes"] and sc["links"] and sc["metrics"] and sc["scenarios"], did
        for s in sc["scenarios"]:
            for v in ("undefended", "defended"):
                var = s["variants"][v]
                assert var["timeline"], f"{did}/{s['id']}/{v} empty timeline"
                assert var["depths"], f"{did}/{s['id']}/{v} no depths"


def test_undefended_breaches_defended_is_safer():
    for did, dom in REGISTRY.items():
        for s in dom.scene()["scenarios"]:
            u = s["variants"]["undefended"]["flags"]
            d = s["variants"]["defended"]["flags"]
            assert u["variance_at"] is not None, f"{did}/{s['id']} undefended should breach"
            # defended must EITHER block/catch OR at least not breach (process stays in band)
            defended_ok = d["proxy_blocked"] or d["fusion_caught"] or d["variance_at"] is None
            assert defended_ok, f"{did}/{s['id']} defended did nothing"


def test_ev_hub_reuses_real_engine():
    ev = REGISTRY["ev_hub"]
    sc = next(s for s in ev.scenarios() if s.id == "overcurrent_tempspoof")
    frames, markers, proxy, fusion = ev.series(sc, defended=False)
    peak = max(f["metrics"]["pack_temp_C"] for f in frames)
    assert peak > 55.0, "EV overcurrent+spoof should overheat the pack (real engine)"
    assert fusion, "fusion should catch the temp spoof"


def test_case_study_gallery_cited():
    assert len(CASE_STUDIES) >= 6
    assert all(c.get("incident") and c.get("consequence") for c in CASE_STUDIES)
    assert any(c["human_harm"] for c in CASE_STUDIES), "human-harm domains present as cited-only"


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("all passed")
