"""Scenario-aware bounded routing for the exploration slice (Python 3.9+)."""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import math
import os
import time
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo

from map_api import BOUNDS, request_plan, stamp
from spike import inspect, variables

ROOT = Path(__file__).resolve().parents[1]
DENVER = ZoneInfo("America/Denver")
POLICY = "exploration-v2"
HORIZON_MINUTES = 90


@dataclass(frozen=True)
class Scenario:
    mode: str = "both"
    changes: int = 1
    arrival: str = "2026-10-20T11:00"
    target: int = 30
    fringe: int = 10
    destination: str = "art"

    @classmethod
    def parse(cls, data: dict) -> Scenario:
        if set(data) - set(cls.__dataclass_fields__):
            raise ValueError("Unknown scenario field")
        s = cls(**data)
        if s.destination != "art":
            raise ValueError("This study supports the verified ART entrance only")
        if s.mode not in ("bus", "trax", "both", "bike"):
            raise ValueError("Select bus, TRAX, both or bike")
        if type(s.changes) is not int or s.changes not in (0, 1, 2):
            raise ValueError("Vehicle changes must be 0, 1 or 2")
        if type(s.target) is not int or not 10 <= s.target <= 60:
            raise ValueError("Target must be 10–60 minutes")
        if type(s.fringe) is not int or s.fringe != 10:
            raise ValueError("This study uses a 10-minute fringe")
        arrival = dt.datetime.fromisoformat(s.arrival)
        if arrival.tzinfo is not None or arrival.second or arrival.microsecond:
            raise ValueError("Use a local Denver date and time at minute precision")
        bounds = service_bounds()
        if not bounds["arrival_min"] <= s.arrival <= bounds["arrival_max"]:
            raise ValueError(
                f"Loaded graph supports arrivals {bounds['arrival_min']} through {bounds['arrival_max']} America/Denver"
            )
        aware = arrival.replace(tzinfo=DENVER)
        if (
            aware.astimezone(dt.timezone.utc).astimezone(DENVER).replace(tzinfo=None)
            != arrival
        ):
            raise ValueError("This local time does not exist in America/Denver")
        if (
            arrival.replace(tzinfo=DENVER, fold=0).utcoffset()
            != arrival.replace(tzinfo=DENVER, fold=1).utcoffset()
        ):
            raise ValueError(
                "Choose an unambiguous Denver arrival time outside the clock change"
            )
        return s

    def latest(self) -> dt.datetime:
        return dt.datetime.fromisoformat(self.arrival).replace(tzinfo=DENVER)

    def earliest(self) -> dt.datetime:
        return self.latest() - dt.timedelta(minutes=15)

    def identity(self) -> str:
        payload = {
            "scenario": asdict(self),
            "policy": POLICY,
            "inputs": input_identity(),
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[
            :20
        ]


def service_bounds():
    # OTP bounds are inclusive service dates, not wall-clock itinerary bounds.
    config = json.loads((ROOT / "data/graph/build-config.json").read_text())
    start = dt.date.fromisoformat(config["transitServiceStart"])
    end = dt.date.fromisoformat(config["transitServiceEnd"])
    # Reserve the first service day for overnight trips and the search horizon.
    if start >= end:
        raise ValueError("Graph needs at least two service dates")
    return {
        "service_start": str(start),
        "service_end": str(end),
        "arrival_min": f"{start + dt.timedelta(days=1)}T00:00",
        "arrival_max": f"{end}T23:59",
    }


@lru_cache(maxsize=1)
def input_identity() -> dict:
    paths = [
        "config/scenario.json",
        "config/bike-scenario.json",
        "config/input-manifest.json",
        "config/bike-input-manifest.json",
        "data/graph/build-config.json",
        "data/graph/graph.obj",
        "data/bike-graph/graph.obj",
    ]
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in paths}


def check(it: dict, scenario: Scenario, mode: str, allowed: list) -> dict:
    result = inspect(it, scenario.latest().isoformat(), mode, scenario.changes, allowed)
    # The spike's fixed 30-minute cutoff is replaced, not used as a retrieval limit.
    result["reasons"] = [r for r in result["reasons"] if r != "duration"]
    if result["elapsed_seconds"] < 0:
        raise ValueError("Negative journey duration")
    if stamp(result["arrival"]) < scenario.earliest():
        result["reasons"].append("too_early")
    totals = {"walk": 0, "ride": 0, "bike": 0}
    for leg in result["legs"]:
        seconds = (
            stamp(leg["end"]["scheduledTime"]) - stamp(leg["start"]["scheduledTime"])
        ).total_seconds()
        if seconds < 0:
            raise ValueError("Negative leg duration")
        totals[
            "ride"
            if leg["transitLeg"]
            else "bike"
            if leg["mode"] == "BICYCLE"
            else "walk"
        ] += seconds
    waiting = result["elapsed_seconds"] - sum(totals.values())
    if waiting < -0.01:
        raise ValueError("Overlapping legs")
    result["breakdown"] = {
        **totals,
        "wait": max(0, waiting),
        "total": result["elapsed_seconds"],
    }
    seconds = result["elapsed_seconds"]
    result["qualifies"] = not result["reasons"]
    result["band"] = (
        "rejected"
        if result["reasons"]
        else "target"
        if seconds <= scenario.target * 60
        else "fringe"
        if seconds <= (scenario.target + scenario.fringe) * 60
        else "beyond"
    )
    return result


def journey_key(it: dict) -> str:
    return json.dumps(
        [
            it["start"],
            it["end"],
            [(l.get("trip"), l["mode"], l["start"]) for l in it["legs"]],
        ],
        sort_keys=True,
    )


def route_point(origin: dict, scenario: Scenario, request=request_plan) -> dict:
    began = time.perf_counter()
    lat, lon = float(origin["lat"]), float(origin["lon"])
    if not math.isfinite(lat) or not math.isfinite(lon):
        raise ValueError("Finite coordinates required")
    out = {
        "origin": {"lat": lat, "lon": lon},
        "scenario": asdict(scenario),
        "scenario_id": scenario.identity(),
        "status": "not_evaluated",
        "itineraries": [],
        "searches": [],
        "retrieval_minutes": HORIZON_MINUTES,
        "arrival_earliest": scenario.earliest().isoformat(),
        "arrival_latest": scenario.latest().isoformat(),
    }
    if not BOUNDS[0] <= lon <= BOUNDS[2] or not BOUNDS[1] <= lat <= BOUNDS[3]:
        return dict(out, error="Outside the loaded SLC street extract")
    # Combined exploration preserves rail and bus alternatives using separate bounded searches.
    modes = ["both", "trax", "bus"] if scenario.mode == "both" else [scenario.mode]
    seen = set()
    for mode in modes:
        config = json.loads(
            (
                ROOT
                / "config"
                / ("bike-scenario.json" if mode == "bike" else "scenario.json")
            ).read_text(encoding="utf-8")
        )
        config["arrival_local"] = scenario.arrival
        v = variables(origin, config, mode, scenario.changes)
        endpoint = os.environ.get(
            "OTP_BIKE_URL" if mode == "bike" else "OTP_TRANSIT_URL",
            f"http://127.0.0.1:{8081 if mode == 'bike' else 8080}/otp/gtfs/v1",
        )
        search = {"mode": mode, "complete": False, "errors": []}
        out["searches"].append(search)
        allowed = config["routes"].get(mode, [])

        def consume(plan):
            search["errors"].extend(plan.get("routingErrors") or [])
            for edge in plan.get("edges") or []:
                it = edge["node"]
                key = journey_key(it)
                if key not in seen:
                    seen.add(key)
                    result = check(it, scenario, mode, allowed)
                    result["retrieved_by"] = mode
                    out["itineraries"].append(result)

        try:
            consume(request(endpoint, v, "PT90M"))
            if mode == "bike":
                search["complete"] = True
                continue
            # Independent of target; supports longer tradeoffs and arrival-window holes.
            v = copy.deepcopy(v)
            v["time"] = {
                "earliestDeparture": (
                    scenario.earliest() - dt.timedelta(minutes=HORIZON_MINUTES)
                ).isoformat()
            }
            cursor = None
            for _ in range(3):
                plan = request(endpoint, v, "PT105M", cursor)
                consume(plan)
                nodes = [e["node"] for e in plan.get("edges") or []]
                if not plan["pageInfo"]["hasNextPage"] or (
                    nodes and min(stamp(n["start"]) for n in nodes) > scenario.latest()
                ):
                    search["complete"] = True
                    break
                cursor = plan["pageInfo"].get("endCursor")
                if not cursor:
                    break
        except (OSError, ValueError, KeyError, TypeError) as exc:
            search["errors"].append({"code": "REQUEST_FAILED", "description": str(exc)})
    out["search_complete"] = all(
        s["complete"] and not s["errors"] for s in out["searches"]
    )
    good = [i for i in out["itineraries"] if i["qualifies"]]
    if good:
        out["status"] = min(
            (i["band"] for i in good), key=["target", "fringe", "beyond"].index
        )
    elif any(s["errors"] for s in out["searches"]):
        out["status"] = "error"
    elif not out["search_complete"] or any(
        "elevation_gap" in i["reasons"] for i in out["itineraries"]
    ):
        out["status"] = "unknown"
    else:
        out["status"] = "no_qualifying_returned_route"
    out["itineraries"].sort(key=lambda i: (not i["qualifies"], i["elapsed_seconds"]))
    out["latency_ms"] = round((time.perf_counter() - began) * 1000, 2)
    return out
