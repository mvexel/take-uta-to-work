"""Private preview bounds, overload behavior and cache eviction."""

import json
import os
import time
import pathlib
import sys
import tempfile
import unittest
from dataclasses import replace
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from explore_api import Scenario, service_bounds
from explore_server import AreaJobs, BusyError, BoundedServer, Handler


class PreviewTests(unittest.TestCase):
    def test_graph_bounds_not_feed_dates(self):
        with tempfile.TemporaryDirectory() as d:
            root = pathlib.Path(d)
            (root / "data/graph").mkdir(parents=True)
            (root / "data/graph/build-config.json").write_text(
                json.dumps(
                    {
                        "transitServiceStart": "2026-10-19",
                        "transitServiceEnd": "2026-10-22",
                    }
                )
            )
            with patch("explore_api.ROOT", root):
                self.assertEqual(service_bounds()["arrival_min"], "2026-10-20T00:00")
                for day in ("2026-10-20T00:00", "2026-10-22T23:59"):
                    Scenario.parse({"arrival": day})
                for day in ("2026-10-19T23:59", "2026-10-23T00:00", "2026-12-01T11:00"):
                    with self.assertRaisesRegex(ValueError, "Loaded graph"):
                        Scenario.parse({"arrival": day})

    def test_missing_provenance_fails_closed(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch("explore_api.ROOT", pathlib.Path(d)),
        ):
            with self.assertRaises(FileNotFoundError):
                Scenario.parse({})

    def test_new_scenario_cannot_cancel_active_job(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch("explore_server.ROOT", pathlib.Path(d)),
            patch("explore_server.threading.Thread"),
        ):
            jobs = AreaJobs()
            key = jobs.start(Scenario())
            with self.assertRaises(BusyError):
                jobs.start(replace(Scenario(), changes=2))
            self.assertFalse(jobs.jobs[key]["cancel"].is_set())
            self.assertEqual(len(jobs.jobs), 1)

    def test_cache_eviction_and_metadata_bound(self):
        with (
            tempfile.TemporaryDirectory() as d,
            patch("explore_server.ROOT", pathlib.Path(d)),
            patch("explore_server.threading.Thread"),
        ):
            root = pathlib.Path(d) / "results"
            root.mkdir()
            for i in range(20):
                (root / f"area-{i:020x}.json").write_text("{}")
            jobs = AreaJobs()
            jobs.prune_cache()
            self.assertEqual(len(list(root.glob("area-*.json"))), 8)
            for day in range(20, 23):
                key = jobs.start(replace(Scenario(), arrival=f"2026-10-{day}T11:00"))
                jobs.jobs[key]["status"] = "failed"
            self.assertLessEqual(len(jobs.jobs), 2)

    def test_eviction_preserves_validation_evidence(self):
        for limit in ("age", "count", "size"):
            with (
                self.subTest(limit=limit),
                tempfile.TemporaryDirectory() as d,
                patch("explore_server.ROOT", pathlib.Path(d)),
            ):
                root = pathlib.Path(d) / "results"
                root.mkdir()
                evidence = root / "area-validation-both-250.json"
                content = b'{"synthetic_validation_evidence":true}'
                evidence.write_bytes(content)
                os.utime(evidence, (time.time() - 172800,) * 2)
                # An oversized unrelated report must neither be deleted nor count
                # against the disposable cache budget.
                report = root / "area-validation-large.json"
                with report.open("wb") as f:
                    f.truncate(65 * 1024 * 1024)
                count = 10 if limit == "count" else 1
                caches = []
                for i in range(count):
                    cache = root / f"area-{i:020x}.json"
                    cache.write_text("{}")
                    caches.append(cache)
                    if limit == "age":
                        os.utime(cache, (time.time() - 172800,) * 2)
                    elif limit == "size":
                        with cache.open("wb") as f:
                            f.truncate(65 * 1024 * 1024)
                AreaJobs().prune_cache()
                self.assertEqual(evidence.read_bytes(), content)
                self.assertEqual(report.stat().st_size, 65 * 1024 * 1024)
                self.assertEqual(
                    sum(p.exists() for p in caches), 8 if limit == "count" else 0
                )

    def test_connection_capacity_rejects_without_thread(self):
        from unittest.mock import Mock

        server = BoundedServer(("127.0.0.1", 0), Handler)
        try:
            for _ in range(8):
                self.assertTrue(server.connections.acquire(False))
            request = Mock()
            with patch.object(server, "shutdown_request") as shutdown:
                server.process_request(request, ("127.0.0.1", 1))
                self.assertIn(b"503", request.sendall.call_args[0][0])
                shutdown.assert_called_once_with(request)
        finally:
            server.server_close()
