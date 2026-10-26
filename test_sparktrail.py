"""Smallest checks that fail if the core logic breaks. Run: python test_sparktrail.py"""
from sparktrail.physics.battery_thermal import BatteryThermal
from sparktrail.physics.feeder import Feeder
from sparktrail.physics.swing import Swing
from sparktrail.core import scenario


def test_thermal_heats_under_current_and_cools():
    b = BatteryThermal(T=35.0, T_ambient=35.0)
    for _ in range(100):
        b.step(1.0, 250.0, cooling_on=False)
    assert b.T > 35.0, "current should heat the pack"
    hot = b.T
    for _ in range(2000):
        b.step(1.0, 0.0, cooling_on=True)
    assert b.T < hot, "no current + cooling should drop temp"


def test_feeder_linear():
    load, drop = Feeder(S_rated_kVA=500, Z_pu=0.05).evaluate(500.0)
    assert abs(load - 100.0) < 1e-9 and abs(drop - 5.0) < 1e-9


def test_swing_drops_when_load_exceeds_gen():
    s = Swing(f=50.0)
    s.step(1.0, p_gen_pu=0.8, p_load_pu=1.0)
    assert s.f < 50.0, "load > gen must drop frequency"


def test_spoof_defeats_bms_so_pack_overheats():
    # headline: overcurrent + temp spoof -> pack passes 55C because BMS never derates
    r = scenario.run_file("scenarios/dcfast_overcurrent_tempspoof.yaml")
    assert r["score"]["peak_pack_temp_C"] > 55.0, "spoof should let pack overheat"
    assert r["score"]["monitor_alert_t_s"] is not None, "monitor must catch the lie"


def test_mass_command_overloads_transformer():
    r = scenario.run_file("scenarios/hub_mass_command.yaml")
    assert r["score"]["peak_transformer_load_pct"] > 150.0
    assert r["score"]["min_bus_voltage_pct"] < 100.0, "overload must drop bus voltage"


def test_cooling_suppression_rides_hotter_than_cooled_baseline():
    # with the temp spoofed low the BMS never cools; compare to the same run w/o attack
    cfg = scenario.load("scenarios/cooling_suppression.yaml")
    attacked = scenario.run(cfg)["score"]["peak_pack_temp_C"]
    cfg_clean = scenario.load("scenarios/cooling_suppression.yaml"); cfg_clean["attacks"] = []
    baseline = scenario.run(cfg_clean)["score"]["peak_pack_temp_C"]
    assert attacked > baseline + 2.0, f"spoof should keep it hotter: {attacked} vs {baseline}"


def test_replay_holds_stale_value_against_fresh_commands():
    from sparktrail.attacks.injector import Injector
    from sparktrail.attacks.schema import Attack
    from sparktrail.core.events import EventStore
    atk = Attack(id="R", entry_point="cyber.backend_link", mechanism="replay",
                 field="charging_profile.limit_A", start_s=10)
    inj = Injector([atk], EventStore())
    assert inj.transform_command("charging_profile.limit_A", 125, 10) == 125  # captures 125
    # a fresh "stop" command (0) arrives but the stale 125 is replayed instead
    assert inj.transform_command("charging_profile.limit_A", 0, 20) == 125


def test_desync_delays_the_signal():
    from sparktrail.attacks.injector import Injector
    from sparktrail.attacks.schema import Attack
    from sparktrail.core.events import EventStore
    atk = Attack(id="D", entry_point="cyber.hub_controller", mechanism="desync",
                 field="hub.load_shed", delay_s=3, start_s=0)
    inj = Injector([atk], EventStore())
    out = [inj.transform_command("hub.load_shed", (1.0 if t < 5 else 0.5), float(t))
           for t in range(10)]
    # the drop to 0.5 should appear ~3s after t=5, not immediately
    assert out[5] == 1.0 and out[8] == 0.5


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print("ok", name)
    print("all passed")
