"""Synthetic contracts for scenario routing, evidence bands and area-job lifecycle."""

import copy
import pathlib
import sys
import threading
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from explore_api import Scenario, check, route_point
from explore_area import classify, grid, reclassify
from explore_server import AreaJobs
from test_map_api import itinerary, plan


class ScenarioTests(unittest.TestCase):
    def test_input_boundaries(self):
        for data in [
            {"mode": "rail"},
            {"changes": True},
            {"target": 61},
            {"fringe": 20},
            {"arrival": "2027-01-01T11:00"},
            {"arrival": "2026-11-01T01:30"},
            {"destination": "umfa"},
        ]:
            with self.subTest(data=data), self.assertRaises((ValueError, TypeError)):
                Scenario.parse(data)
        self.assertEqual(
            Scenario.parse({}).latest().isoformat(), "2026-10-20T11:00:00-06:00"
        )

    def test_target_is_not_retrieval_cutoff(self):
        s = Scenario()
        it = itinerary(seconds=2100)
        self.assertEqual(check(it, s, "trax", ["1:8246"])["band"], "fringe")
        self.assertEqual(
            check(it, replace(s, target=20), "trax", ["1:8246"])["band"], "beyond"
        )
        self.assertNotEqual(s.identity(), replace(s, target=20).identity())

    def test_exact_boundaries(self):
        for seconds, band in [
            (1800, "target"),
            (1801, "fringe"),
            (2400, "fringe"),
            (2401, "beyond"),
        ]:
            self.assertEqual(
                check(itinerary(seconds=seconds), Scenario(), "trax", ["1:8246"])[
                    "band"
                ],
                band,
            )
        for arrival in ["2026-10-20T10:44:59-06:00", "2026-10-20T11:00:01-06:00"]:
            self.assertFalse(
                check(itinerary(arrival), Scenario(), "trax", ["1:8246"])["qualifies"]
            )

    def test_combined_retains_mode_specific_rail(self):
        calls = []

        def request(endpoint, v, window, after=None):
            calls.append(copy.deepcopy(v))
            only = [x["mode"] for x in v["modes"]["transit"]["transit"]] == ["TRAM"]
            return plan([itinerary()] if only else [])

        result = route_point({"lat": 40.76, "lon": -111.88}, Scenario(), request)
        self.assertEqual(result["status"], "target")
        self.assertEqual(len(result["itineraries"]), 1)
        self.assertEqual(
            [s["mode"] for s in result["searches"]], ["both", "trax", "bus"]
        )
        self.assertTrue(
            all(
                v["preferences"]["transit"]["transfer"]["maximumTransfers"] == 1
                for v in calls
            )
        )
        self.assertTrue(
            any(
                v["time"].get("earliestDeparture") == "2026-10-20T09:15:00-06:00"
                for v in calls
            )
        )

    def test_partial_mode_failure_preserves_positive_and_unknown(self):
        def request(endpoint, v, *args):
            modes = [x["mode"] for x in v["modes"]["transit"]["transit"]]
            if modes == ["TRAM"]:
                raise TimeoutError("synthetic timeout")
            return plan([itinerary(route_id="1:2116", mode="BUS")])

        r = route_point({"lat": 40.76, "lon": -111.88}, Scenario(), request)
        self.assertEqual(r["status"], "target")
        self.assertFalse(r["search_complete"])
        self.assertTrue(r["searches"][1]["errors"])

    def test_empty_failure_and_truncation_distinct(self):
        origin = {"lat": 40.76, "lon": -111.88}
        s = Scenario(mode="trax")
        self.assertEqual(
            route_point(origin, s, lambda *a: plan([]))["status"],
            "no_qualifying_returned_route",
        )
        self.assertEqual(
            route_point(origin, s, lambda *a: plan([], True, "cursor"))["status"],
            "unknown",
        )

        def fail(*a):
            raise TimeoutError("test")

        self.assertEqual(route_point(origin, s, fail)["status"], "error")
        self.assertEqual(
            route_point({"lat": 41, "lon": -111.88}, s, fail)["status"], "not_evaluated"
        )

    def test_allowlist_and_changes_are_checked(self):
        self.assertIn(
            "route_or_mode",
            check(itinerary(route_id="1:45389"), Scenario(), "trax", ["1:8246"])[
                "reasons"
            ],
        )
        it = itinerary()
        leg = it["legs"][0]
        it["legs"] = [dict(leg), dict(leg)]
        # Non-overlapping vehicle legs with one change.
        it["legs"][0]["end"] = {"scheduledTime": "2026-10-20T10:30:00-06:00"}
        it["legs"][1]["start"] = {"scheduledTime": "2026-10-20T10:30:00-06:00"}
        self.assertIn(
            "changes", check(it, Scenario(changes=0), "trax", ["1:8246"])["reasons"]
        )


class AreaTests(unittest.TestCase):
    def test_mixed_cells_not_smoothed(self):
        def values(states):
            return [{"status": s, "search_complete": True} for s in states]

        self.assertEqual(classify(values(["target"] * 5)), "target")
        self.assertEqual(classify(values(["target"] * 4 + ["fringe"])), "fringe")
        for state in [
            "unknown",
            "error",
            "not_evaluated",
            "no_qualifying_returned_route",
            "beyond",
        ]:
            self.assertEqual(classify(values(["target"] * 4 + [state])), "unknown")
        self.assertEqual(classify(values(["beyond"] * 5)), "outside_band")
        self.assertEqual(
            classify([{"status": "beyond", "search_complete": False}] * 5), "unknown"
        )

    def test_grid_has_shared_corners_and_independent_centers(self):
        points, cells = grid([-111.88, 40.76, -111.87, 40.77], 500)
        self.assertTrue(all(len(c["keys"]) == 5 for c in cells))
        self.assertLess(len(points), len(cells) * 5)

    def test_reclassification_uses_measured_times(self):
        bounds = [-111.88, 40.76, -111.879, 40.761]
        points, cells = grid(bounds, 250)
        raw = {
            "bounds": bounds,
            "cell_metres_max": 250,
            "features": [{"properties": {"band": "target"}}],
            "grid_results": {
                f"{a},{b}": {
                    "status": "target",
                    "minimum_seconds": 2100,
                    "search_complete": True,
                }
                for a, b in points
            },
        }
        result = reclassify(raw, Scenario())
        self.assertEqual(result["features"][0]["properties"]["band"], "fringe")
        self.assertEqual(raw["features"][0]["properties"]["band"], "target")

    def test_cancelled_job_can_restart_same_scenario(self):
        jobs = AreaJobs()
        s = Scenario()
        key = s.identity()
        cancel = threading.Event()
        cancel.set()
        jobs.jobs[key] = {"status": "running", "cancel": cancel}
        with (
            tempfile.TemporaryDirectory() as directory,
            patch("explore_server.ROOT", pathlib.Path(directory)),
            patch("explore_server.threading.Thread") as thread,
        ):
            jobs.start(s)
            self.assertTrue(thread.called)
            self.assertFalse(jobs.jobs[key]["cancel"].is_set())


if __name__ == "__main__":
    unittest.main()
