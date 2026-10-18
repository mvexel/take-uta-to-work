"""Repeatable local contour experiment; raw outputs stay in ignored results/."""

import argparse
import concurrent.futures
import json
import time
from dataclasses import asdict

from explore_api import ROOT, Scenario, route_point
from explore_area import compute


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=["bus", "trax", "both", "bike"], default="both"
    )
    parser.add_argument("--cell-metres", type=int, default=250)
    args = parser.parse_args()
    scenario = Scenario.parse({"mode": args.mode})
    last = [0]

    def progress(done, total):
        if time.monotonic() - last[0] > 20:
            print(f"Area {done}/{total}", flush=True)
            last[0] = time.monotonic()

    area = compute(scenario, cell_metres=args.cell_metres, progress=progress)
    out = ROOT / "results"
    out.mkdir(exist_ok=True)
    (out / f"area-{scenario.identity()}.json").write_text(
        json.dumps(area), encoding="utf-8"
    )
    tasks = []
    for f in area["features"]:
        if f["properties"]["band"] not in ("target", "fringe"):
            continue
        coords = f["geometry"]["coordinates"][0]
        w, s = coords[0]
        e, n = coords[2]
        for x, y in [(0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)]:
            tasks.append(
                (
                    {"lat": s + (n - s) * y, "lon": w + (e - w) * x},
                    f["properties"]["band"],
                )
            )

    def check(task):
        point, expected = task
        r = route_point(point, scenario)
        accepted = (
            r["status"] == "target"
            if expected == "target"
            else r["status"] in ("target", "fringe")
        )
        seconds = [i["elapsed_seconds"] for i in r["itineraries"] if i["qualifies"]]
        return {
            "point": point,
            "expected": expected,
            "actual": r["status"],
            "passed": accepted,
            "minimum_seconds": min(seconds) if seconds else None,
        }

    print(
        "Grid complete",
        area["counts"],
        area["elapsed_seconds"],
        "seconds; holdouts",
        len(tasks),
        flush=True,
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        results = []
        for result in pool.map(check, tasks):
            results.append(result)
            if len(results) % 200 == 0:
                print("Holdouts", len(results), "/", len(tasks), flush=True)
    failures = [r for r in results if not r["passed"]]
    report = {
        "scenario": asdict(scenario),
        "scenario_id": scenario.identity(),
        "cell_metres_max": args.cell_metres,
        "grid_seconds": area["elapsed_seconds"],
        "origins": area["sample_count"],
        "cells": area["counts"],
        "holdout_count": len(results),
        "band_failures": len(failures),
        "failure_details": failures,
        "holdouts": results,
    }
    (out / f"area-validation-{args.mode}-{args.cell_metres}.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(
        json.dumps({k: v for k, v in report.items() if k != "holdouts"}, indent=2),
        flush=True,
    )


if __name__ == "__main__":
    main()
