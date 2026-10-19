"""Loopback exploration UI. Explicit bounded jobs, cancellation, and no collectors."""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import re
import time
import threading
from dataclasses import asdict, replace
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit

from explore_api import ROOT, Scenario, route_point, service_bounds
from explore_area import CELL_METRES, STUDY, compute, reclassify
from map_api import BOUNDS


class BusyError(Exception):
    pass


class BoundedServer(ThreadingHTTPServer):
    # Reject excess connections before creating threads; no unbounded waiters.
    request_queue_size = 8

    def __init__(self, *args, **kwargs):
        self.connections = threading.BoundedSemaphore(8)
        super().__init__(*args, **kwargs)

    def process_request(self, request, address):
        request.settimeout(10)
        if not self.connections.acquire(blocking=False):
            try:
                request.sendall(
                    b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n"
                )
            finally:
                self.shutdown_request(request)
            return
        try:
            super().process_request(request, address)
        except Exception:
            self.connections.release()
            raise

    def process_request_thread(self, request, address):
        try:
            super().process_request_thread(request, address)
        finally:
            self.connections.release()


class AreaJobs:
    def __init__(self):
        self.lock = threading.Lock()
        self.jobs = {}
        self.worker = threading.Semaphore(1)

    def prune_cache(self):
        directory = ROOT / "results"
        files = sorted(
            (
                p
                for p in directory.glob("area-*.json")
                if re.fullmatch(r"area-[0-9a-f]{20}\.json", p.name)
                and not p.is_symlink()
                and p.is_file()
            ),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        size = 0
        for index, path in enumerate(files):
            size += path.stat().st_size
            if (
                index >= 8
                or size > 64 * 1024 * 1024
                or time.time() - path.stat().st_mtime > 86400
            ):
                path.unlink(missing_ok=True)

    def start(self, scenario):
        base = replace(scenario, target=30)
        key = base.identity()
        with self.lock:
            self.prune_cache()
            terminal = [
                k
                for k, j in self.jobs.items()
                if j["status"] not in ("queued", "running") and k != key
            ]
            for k in terminal[:-1]:
                self.jobs.pop(k)
            cache = ROOT / "results" / f"area-{key}.json"
            if (
                key not in self.jobs or self.jobs[key]["cancel"].is_set()
            ) and cache.is_file():
                try:
                    result = json.loads(cache.read_text(encoding="utf-8"))
                    if (
                        result.get("scenario_id") == key
                        and result.get("cell_metres_max") == CELL_METRES
                        and result.get("bounds") == STUDY
                    ):
                        self.jobs[key] = {
                            "status": "complete",
                            "done": result["sample_count"],
                            "total": result["sample_count"],
                            "scenario": base,
                            "cancel": threading.Event(),
                            "result": result,
                        }
                except (OSError, ValueError, KeyError):
                    pass  # A missing/corrupt cache is recomputed, never treated as no-route.
            old = self.jobs.get(key)
            if (
                old
                and old["status"] not in ("cancelled", "failed")
                and not old["cancel"].is_set()
            ):
                return key
            if any(j["status"] in ("queued", "running") for j in self.jobs.values()):
                raise BusyError(
                    "An area calculation is active; cancel it and retry after it stops"
                )
            # One active worker and at most two retained terminal job records.
            for k in list(self.jobs)[:-1]:
                self.jobs.pop(k)
            job = {
                "status": "queued",
                "done": 0,
                "total": 0,
                "scenario": base,
                "cancel": threading.Event(),
            }
            self.jobs[key] = job
        threading.Thread(target=self.run, args=(key, job), daemon=True).start()
        return key

    def run(self, key, job):
        with self.worker:
            if job["cancel"].is_set():
                job["status"] = "cancelled"
                return
            job["status"] = "running"

            def progress(done, total):
                with self.lock:
                    job.update(done=done, total=total)

            try:
                result = compute(
                    job["scenario"], progress=progress, cancelled=job["cancel"].is_set
                )
                with self.lock:
                    if job["cancel"].is_set() or result["status"] == "cancelled":
                        job["status"] = "cancelled"
                    else:
                        job.update(status="complete", result=result)
                        directory = ROOT / "results"
                        directory.mkdir(exist_ok=True)
                        temporary = directory / f"area-{key}.tmp"
                        temporary.write_text(json.dumps(result), encoding="utf-8")
                        temporary.replace(directory / f"area-{key}.json")
                        self.prune_cache()
            except Exception as exc:
                # Boundary: worker failures must become a visible failed job, never no-match.
                with self.lock:
                    job.update(status="failed", error=str(exc))

    def read(self, key, target):
        with self.lock:
            job = self.jobs.get(key)
            if job is None:
                return None
            scenario = Scenario.parse({**asdict(job["scenario"]), "target": target})
            status = {k: job[k] for k in ("status", "done", "total")}
            status.update(job_id=key, scenario_id=scenario.identity())
            if "error" in job:
                status["error"] = job["error"]
            result = job.get("result")
        if result:
            status["area"] = reclassify(result, scenario)
        return status

    def cancel(self, key):
        with self.lock:
            if key in self.jobs and self.jobs[key]["status"] in ("queued", "running"):
                self.jobs[key]["cancel"].set()


class Handler(BaseHTTPRequestHandler):
    def json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def local_request(self):
        origin = self.headers.get("Origin")
        allowed = (
            f"http://127.0.0.1:{self.server.server_port}",
            f"http://localhost:{self.server.server_port}",
        )
        if origin and origin not in allowed:
            self.json({"error": "Local origin required"}, 403)
            return False
        return True

    def do_GET(self):
        url = urlsplit(self.path)
        if url.path == "/api/config":
            config = json.loads(
                (ROOT / "config/scenario.json").read_text(encoding="utf-8")
            )
            self.json(
                {
                    "destination": config["destination"],
                    "defaults": asdict(Scenario()),
                    "study_bounds": STUDY,
                    "routing_bounds": BOUNDS,
                    "cell_metres": CELL_METRES,
                    "service_bounds": service_bounds(),
                }
            )
            return
        if url.path.startswith("/api/area/"):
            try:
                target = int(parse_qs(url.query).get("target", ["30"])[0])
                result = self.server.jobs.read(url.path.rsplit("/", 1)[-1], target)
                self.json(
                    result if result else {"error": "Area job not found"},
                    200 if result else 404,
                )
            except ValueError as exc:
                self.json({"error": str(exc)}, 400)
            return
        if url.path == "/map-data/streets.geojson":
            path = ROOT / "data/map-streets.geojson"
        else:
            relative = "explore.html" if url.path == "/" else url.path.lstrip("/")
            path = ROOT / "web" / relative
            if path.is_symlink() or not path.resolve().is_relative_to(
                (ROOT / "web").resolve()
            ):
                self.send_error(404)
                return
        if not path.is_file():
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header(
            "Content-Type",
            mimetypes.guess_type(str(path))[0] or "application/octet-stream",
        )
        self.end_headers()
        try:
            self.wfile.write(path.read_bytes())
        except (BrokenPipeError, ConnectionResetError):
            pass

    def do_POST(self):
        if not self.local_request():
            return
        if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
            self.json({"error": "Expected JSON"}, 415)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError("Invalid request size")
            data = json.loads(self.rfile.read(length))
            scenario = Scenario.parse(data["scenario"])
            if self.path == "/api/area":
                key = self.server.jobs.start(scenario)
                self.json(self.server.jobs.read(key, scenario.target))
                return
            if self.path == "/api/point":
                if not self.server.point_slots.acquire(blocking=False):
                    raise BusyError("Point calculation slots are busy; retry shortly")
                try:
                    self.json(route_point(data["origin"], scenario))
                finally:
                    self.server.point_slots.release()
                return
            self.send_error(404)
        except BusyError as exc:
            self.json({"error": str(exc)}, 429)
        except (ValueError, KeyError, TypeError) as exc:
            self.json({"error": str(exc)}, 400)

    def do_DELETE(self):
        if not self.local_request():
            return
        if not self.path.startswith("/api/area/"):
            self.send_error(404)
            return
        self.server.jobs.cancel(self.path.rsplit("/", 1)[-1])
        self.json({"status": "cancellation_requested"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8003)
    args = parser.parse_args()
    service_bounds()  # Fail closed if graph provenance is unavailable.
    server = BoundedServer(
        (os.environ.get("APP_BIND", "127.0.0.1"), args.port), Handler
    )
    server.jobs = AreaJobs()
    server.point_slots = threading.Semaphore(2)
    print(f"Exploration: http://127.0.0.1:{args.port}", flush=True)
    server.serve_forever()
