"""Run a scenario headless -> trace.json.

    python -m sparktrail.cli scenarios/dcfast_overcurrent_tempspoof.yaml
    python -m sparktrail.cli <scenario.yaml> -o out.json
"""
from __future__ import annotations

import argparse
import json
import sys

from .core import scenario


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="SparkTrail headless runner")
    ap.add_argument("scenario", help="path to scenario YAML")
    ap.add_argument("-o", "--out", default="trace.json", help="output JSON path")
    ap.add_argument("-q", "--quiet", action="store_true")
    args = ap.parse_args(argv)

    result = scenario.run_file(args.scenario)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    if not args.quiet:
        s = result["score"]
        print(f"[{result['name']}]  ->  {args.out}  ({len(result['events'])} events)")
        print(f"  peak pack temp      : {s['peak_pack_temp_C']} C")
        print(f"  peak transformer    : {s['peak_transformer_load_pct']} %")
        print(f"  time-to-impact      : {s['time_to_impact_s']} s")
        print(f"  monitor alert at    : {s['monitor_alert_t_s']} s")
        print(f"  detection delay     : {s['detection_delay_s']} s")
        print(f"  impact score        : {s['impact_score']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
