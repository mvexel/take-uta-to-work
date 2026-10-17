# Local project dashboard

Run from the project root with Python 3.9+ (standard library only):

```sh
python3 dashboard/server.py
```

Open http://127.0.0.1:8765. The server binds only 127.0.0.1; it does not use OTP's port 8080. Stop with Ctrl-C in its terminal. If needed, choose another port with `--port 8766`. There is no build, package install, external asset, browser storage, collector.

## Source of truth and updates

`docs/status.md` remains authoritative for routing facts. The server reads and displays it live on every refresh; this dashboard never writes it. `dashboard/board.json` holds only a reviewed coordination snapshot, not a second routing report. Parent/coordinator owns this file. The routing lead updates their own status document; the coordinator then reconciles affected cards. A changed SHA-256 produces a prominent warning immediately. Age over `stale_after_hours` (24 by default) also warns; refresh does not make verification newer.

After checking the source and updating cards, update `reviewed_at`, affected `verified_at` values (ISO 8601 with timezone), and `status_sha256`. To obtain the current hash without changing anything:

```sh
python3 -c 'import hashlib,pathlib; print(hashlib.sha256(pathlib.Path("docs/status.md").read_bytes()).hexdigest())'
```

Do not refresh timestamps or hashes merely to remove a warning. Read the new evidence first. Older project/development notes can describe prerequisites already completed; current status takes precedence. The initial October 20 date is provisional and displayed as such, not a new demand on Martijn.

## Data contract

Top level: `schema_version: 1`, `reviewed_at`, `status_sha256`, positive `stale_after_hours`, `cards`, `requests`, `technical_constraints`.

Each card needs a unique `id`, `state` (`planned`, `in_progress`, `done`, `backlog`), `title`, `summary`, `owner`, `done_when`, `next_step`, `evidence`, and `verified_at`. Planned contains next steps; proposals must explicitly say not started and not yet approved; backlog means later and uncommitted. In progress means active ownership. Done is bounded to the card's criteria, never a claim the entire product is done. Owners can be roles; explicitly mark unassigned roles.

Requests default to `[]`. Add a request only when evidence verifies a real ask of the user. Required fields: `kind` (`decision` or `action`), `ask` (exact request), `owner`, `impact` (what it unblocks and whether work is actually blocked), `recommendation` (options where meaningful), `evidence`, `verified_at`. Resolve/remove requests after the main conversation records the outcome. There are no approval buttons: a board edit does not grant permission. Technical constraints go in `technical_constraints` with `title`, `detail`, `evidence`, not in the user's inbox.

Evidence keys: `decisions`, `status`, `bicycle`, `project`, `development`, `readme`, `dashboard`. These map to seven exact, read-only documents in server.py. Artifact pages render escaped, wrapped source text. They cannot browse directories or arbitrary paths; data/, results/, credentials, symlinks and traversal URLs are not served. Add any future evidence document explicitly to this allowlist after inspecting its contents. Raw GTFS/results are intentionally excluded. Errors produce a visible 503 page rather than an apparently empty board.

A small local script refreshes every 15 seconds while the tab is visible (15 seconds after a completed request or returning to the tab). Hidden tabs cancel pending requests and do not poll. Refresh errors keep existing content and show a retry message. Keyed cards preserve expanded disclosures, scroll position and focus across updates; manual Refresh status uses the same behavior. One initial browser reload is needed after installing this enhancement. Source changes refresh the source and warning, not card classifications.

The board uses native links, headings and disclosure controls support keyboard use. CSS adapts four columns to two and one. Counts are generated from data, not maintained separately.

## Verification

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s dashboard -p 'test_*.py' -v
```

Tests exercise source drift, stale data, counts, empty states, request rendering, validation, escaping, actual HTTP artifact routes, traversal rejection and malformed-data errors. Browser verification details are in `dashboard/VERIFICATION.md`.

## Team documentation

The [team roster and individual charters](../docs/team.md) live in docs/team.md and docs/team/. The dashboard already exposes this maintenance document and the project brief under Evidence; both point to the roster. Use the local files for the individual charters; no artifact allowlist or application behavior changed. Names identify roles, not continuously running agents.
