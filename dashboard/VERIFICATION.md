# Dashboard verification — 2026-10-17

Working URL: http://127.0.0.1:8765/

Four focused unittest groups pass: state counts and empty states; stale-source/age and escaped request rendering; invalid data; HTTP routes/errors. All seven allowlisted artifact routes return 200. Arbitrary paths return 404, nonlocal Host returns 403, malformed board data returns visible 503.

Verified in the user’s Firefox on macOS: actual page load, all four states and generated counts, empty Decisions/Actions, live source-change warning during concurrent routing update, refreshed reconciled data, keyboard Space toggling completion details, and bicycle evidence navigation. Desktop and 390×844 Firefox responsive-mode screenshots were captured in the task tool transcript; no standalone screenshot file was saved. Mobile header/scope layout visually checked; not a full device/accessibility audit.

Final coordination-only update closes the approved arrival-window decision and marks the map cycle in progress. Current counts: Planned 1, In progress 1, Done 4, Backlog 3. Routing and docs/status.md were not edited.

Server remains running in execution session 36896. Stop by Ctrl-C in that session, or identify the dashboard listener with lsof -nP -iTCP:8765 -sTCP:LISTEN and terminate that PID. Restart: python3 dashboard/server.py from project root. No pending approval or execution blocker.

## Visible-tab refresh enhancement

15-second refresh added without modifying board.json. Tested actual server-rendered before/after fixtures in jsdom using test_refresh.cjs: a changed card moved from Done to Planned, new source text and reconciliation warning appeared, the same disclosure/focused summary nodes remained open/focused, and scroll stayed at 450px. Hidden visibility canceled the timer and made no fetch calls; simulated offline failure retained existing content and displayed retry feedback. Test fixture changes were in memory/temp files only. jsdom was installed only under /tmp/uta-dashboard-check, not as a runtime dependency.

Run the browser-state regression with NODE_PATH=/tmp/uta-dashboard-check/node_modules node dashboard/test_refresh.cjs /tmp/uta-dashboard-check/before.html /tmp/uta-dashboard-check/after.html while those fixtures exist. Browser needs one reload to load refresh.js. Server restart retains port 8765.
