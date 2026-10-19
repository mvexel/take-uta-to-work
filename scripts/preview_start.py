"""Verify private artifacts before serving; no downloads or graph builds."""

import hashlib
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parents[1]
for relative, expected in json.loads(
    (root / "config/preview-artifacts.json").read_text()
).items():
    with (root / relative).open("rb") as source:
        actual = hashlib.file_digest(source, "sha256").hexdigest()
    if actual != expected:
        raise SystemExit(f"Artifact hash mismatch: {relative}")
os.execvp("python", ["python", str(root / "scripts/explore_server.py")])
