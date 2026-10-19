"""Conservative raster contours; never hull or smooth across disconnected cells."""

from __future__ import annotations

import concurrent.futures
import copy
import math
import time

from explore_api import route_point

STUDY = [-111.91, 40.735, -111.825, 40.79]
CELL_METRES = 250


def grid(bounds=STUDY, cell_metres=CELL_METRES):
    west, south, east, north = bounds
    nx = math.ceil(
        (east - west)
        * 111320
        * math.cos(math.radians((south + north) / 2))
        / cell_metres
    )
    ny = math.ceil((north - south) * 111320 / cell_metres)
    dx, dy = (east - west) / nx, (north - south) / ny
    points, cells = {}, []
    for y in range(ny):
        for x in range(nx):
            keys = [
                (2 * x, 2 * y),
                (2 * x + 2, 2 * y),
                (2 * x + 2, 2 * y + 2),
                (2 * x, 2 * y + 2),
                (2 * x + 1, 2 * y + 1),
            ]
            for a, b in keys:
                points[(a, b)] = {"lat": south + b * dy / 2, "lon": west + a * dx / 2}
            cells.append(
                {
                    "x": x,
                    "y": y,
                    "keys": keys,
                    "bounds": [
                        west + x * dx,
                        south + y * dy,
                        west + (x + 1) * dx,
                        south + (y + 1) * dy,
                    ],
                }
            )
    return points, cells


def classify(results):
    states = [r["status"] for r in results]
    if all(s == "target" for s in states):
        return "target"
    if all(s in ("target", "fringe") for s in states):
        return "fringe"
    if all(
        s in ("beyond", "no_qualifying_returned_route") and r["search_complete"]
        for s, r in zip(states, results)
    ):
        return "outside_band"
    return "unknown"


def summary(result):
    good = [i["elapsed_seconds"] for i in result["itineraries"] if i["qualifies"]]
    return {
        "status": result["status"],
        "search_complete": result.get("search_complete", False),
        "minimum_seconds": min(good) if good else None,
        "latency_ms": result.get("latency_ms"),
    }


def compute(
    scenario, *, bounds=STUDY, cell_metres=CELL_METRES, progress=None, cancelled=None
):
    started = time.perf_counter()
    points, cells = grid(bounds, cell_metres)
    results = {}

    def evaluate(entry):
        key, point = entry
        return key, summary(route_point(point, scenario))

    # Bounded concurrency; only one area job is admitted by the web job manager.
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        pending = {}
        entries = iter(points.items())
        for _ in range(3):
            entry = next(entries, None)
            if entry:
                pending[pool.submit(evaluate, entry)] = entry[0]
        while pending:
            done, _ = concurrent.futures.wait(
                pending, return_when=concurrent.futures.FIRST_COMPLETED
            )
            for future in done:
                pending.pop(future)
                key, value = future.result()
                results[key] = value
                if progress:
                    progress(len(results), len(points))
                if cancelled and cancelled():
                    return {"status": "cancelled"}
                entry = next(entries, None)
                if entry:
                    pending[pool.submit(evaluate, entry)] = entry[0]
    features = []
    counts = {}
    for cell in cells:
        band = classify([results[k] for k in cell["keys"]])
        counts[band] = counts.get(band, 0) + 1
        w, s, e, n = cell["bounds"]
        features.append(
            {
                "type": "Feature",
                "properties": {"band": band, "x": cell["x"], "y": cell["y"]},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[[w, s], [e, s], [e, n], [w, n], [w, s]]],
                },
            }
        )
    return {
        "status": "complete",
        "type": "FeatureCollection",
        "features": features,
        "counts": counts,
        "scenario_id": scenario.identity(),
        "cell_metres_max": cell_metres,
        "bounds": bounds,
        "sample_count": len(points),
        "elapsed_seconds": round(time.perf_counter() - started, 2),
        "method": "Five actual origins per cell (shared corners and center); no interpolation or smoothing. Mixed cells are unknown.",
        "accuracy": "Approximate raster guide, not address coverage. Barriers and timetable changes can occur inside a cell. Click to verify.",
        "grid_results": {f"{a},{b}": v for (a, b), v in results.items()},
    }


def reclassify(area, scenario):
    """A target change reuses measured journey times, never interpolated travel times."""
    out = copy.deepcopy(area)
    _, cells = grid(out["bounds"], out["cell_metres_max"])
    counts = {}
    for cell, feature in zip(cells, out["features"]):
        values = []
        for a, b in cell["keys"]:
            value = dict(out["grid_results"][f"{a},{b}"])
            seconds = value["minimum_seconds"]
            if seconds is not None:
                value["status"] = (
                    "target"
                    if seconds <= scenario.target * 60
                    else "fringe"
                    if seconds <= (scenario.target + scenario.fringe) * 60
                    else "beyond"
                )
            values.append(value)
        band = classify(values)
        feature["properties"]["band"] = band
        counts[band] = counts.get(band, 0) + 1
    out["counts"] = counts
    out["scenario_id"] = scenario.identity()
    out.pop("grid_results")
    return out
