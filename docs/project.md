# Brief, milestones, and decisions

Owner: Martijn (product and decisions). Parent conversation: coordinator and independent testing; dedicated feedback specialist: short user tests and feedback synthesis. This local thread: technical lead for setup, routing harness and documentation. Future work should update docs/status.md. See the [team roster and individual charters](team.md) for stable role identities and file ownership.

Question: which sampled origins permit a journey of at most 1,800 seconds to ART, University of Utah building 38, 375 S 1530 E? Separate bicycle-only from transit-with-walking. Transit selectors: bus, TRAX, both; maximum vehicle changes 0/1/2. S-Line and FrontRunner are excluded from TRAX and require explicit separate future options. No rental listings or accounts.

Tuesday at 11:00 America/Denver is requested. October 20, 2026 is a proposed test date, not confirmed. Arrival is a deadline. Duration is actual destination arrival minus departure, including access/egress walking, boarding waits, riding and transfer waits. Earliness is deadline minus actual arrival; it is reported separately, not added to elapsed time. These are schedule estimates, not reliability observations.

## Product and design direction

[Draft product vision](product-vision.md) proposes a place shortlist with a supporting map: explore candidates, compare meaningful commute tradeoffs and revisit the decision with its assumptions intact. [noa](team/noa.md) is assigned product/design lead on demand, not continuously running; Martijn remains human product owner and dot coordinates. This responds to Martijn’s request for a coherent longer-term direction; the proposed UT-01 patch cycle is superseded as the immediate plan. The vision is a reviewable proposal, not implementation authorization. Ash owns technical feasibility and rue owns feedback/testing; their evidence and historical handoffs below remain preserved.

## Architecture decisions

1. Pin OTP 2.10.0, use stable GTFS GraphQL planConnection/latestArrival. Sample 50 geographic origins before any polygon. The old isochrone API was removed in OTP 2.6: https://docs.opentripplanner.org/en/latest/Analysis/ . R5/r5r only after measured performance justifies it.
2. Enforce route allowlists in query and inspect returned legs. TRAM alone cannot distinguish TRAX from S-Line. Resolve actual feed namespace from the built OTP graph, and exact route IDs from the audited static feed. Do not infer from route type alone.
3. Dependency-free Python harness now; MapLibre web UI after routing correctness. Self-host all services and map assets eventually; no proprietary API required.
4. Bicycle flat-ground maximum speed 4.17 m/s (15 km/h); walking 1.33 m/s. Elevation is not configured yet. Before presenting bike reachability, build with documented USGS 3DEP elevation, preserve directional slopes, and validate uphill/downhill asymmetry. Never treat planned bikeways as usable streets. Utah bikeways are an optional later cross-check.
5. Conservative result states: unknown on failed/uncomputed search; qualifying_route for inspected positive results; no_qualifying_returned_route for a bounded successful search with no passing result. This last state is not proof that no route exists, especially with pagination/filtering. Vehicle changes count new vehicle boardings after the first, excluding OTP interlineWithPreviousLeg stay-seated transitions; synthetic regression coverage exists, while live interlined examples remain to check.

## Milestones/backlog

- M0 setup: local repository, documentation, data auditor, query runner, response contract tests and local result viewer.
- M1 inputs: verify ART pedestrian entrance and street connection, review UTA terms, inspect service coverage/timezone/exceptions and route IDs, choose small buffered SLC OSM extract, record hashes/license/date/bounds. Grid origins are synthetic coverage samples, not verified residences; replace/snap representative downtown, west/east bench, Sugar House, transit corridor and boundary origins.
- M2 routing: build graph, record elapsed build time/maximum RSS, run all bus/TRAX/both × 0/1/2 and bike scenarios. Record cold/warm latency p50/p95 and failures. Validate returned legs and independently check timetable cases near 30 minutes, 11:00 arrival, early arrival, missed transfers, 0/1/2 changes, S-Line exclusion, FrontRunner exclusion, out-of-coverage, and no-service dates. Compare access/egress distances at entrance.
- M3 website: MapLibre with honest sampled coverage, no smoothing into invented polygons; filters and itinerary evidence; accessible controls and data provenance.
- Later only: historical GTFS-RT reliability. No collector started. Distinguish observed events from predictions, explicit cancellations from missing data; deduplicate trip/stop events; expose date range/sample size/coverage; segment route/direction/weekday/time and archive matching static feed versions. No reliability values currently validated.

## Initial milestone outcome

M0 complete. Bounded M1/M2 feasibility demonstrated for transit and bicycle; see docs/status.md and docs/bicycle.md. Further work: investigate OTP elevation aggregate double-counting, graph profile failures/gaps, calibrate bicycle speed/terrain response with observed rides, improve representative origin sampling, broaden geographic coverage and timetable edge validation, and review redistribution terms before publication. Separate dashboard task owns dashboard/. These technical items are team work, not actions blocked on Martijn.

## User testing and feedback

The dedicated feedback specialist owns docs/feedback.md and this section; the parent owns delivery through Martijn's verified personal Slack DM and forwards replies. The specialist prepares one concrete task with one or two neutral questions, records observed and reported behavior, expectations and quotes separately from interpretation, and proposes reproducible issues with impact, priority and acceptance checks. Martijn chooses the next implementation priority; the technical lead owns app changes and an independent reviewer checks routing changes.

Active test UT-01: assess one familiar origin with Bus + TRAX / at most 1 change for the proposed October 20 scenario (10:45–11:00 arrival, <=30 minutes door-to-door). The exact message and evidence are in docs/feedback.md. This replaces the earlier broad map review; dot sent UT-01 to Martijn's personal Slack DM on 2026-10-17 at 21:38:43 UTC (reference `slack:D0CA2HRA4GJ::1792273123.770189`); Martijn's first response is recorded in docs/feedback.md; Ash's TRAX diagnosis and product prioritization are pending. Do not repeat the request. After each reply the specialist drives the next focused follow-up through the parent, without reminders or a fixed schedule. Feature work remains paused pending feedback/prioritization. Treat this single participant's feedback as qualitative evidence, not general usability validation; sampled coverage, bike calibration and reliability limits remain explicit.

UT-01 update, 2026-10-17: Martijn's first reply is recorded verbatim in docs/feedback.md. Initial task is answered; Rue proposes findings on missing TRAX, mode identification and alternate-trip discovery. Ash is investigating TRAX; dot will present evidence and priorities before a new implementation cycle. No repeat task or nudge is needed.
