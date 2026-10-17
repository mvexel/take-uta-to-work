## Current direction — vision draft complete; product choices pending

Working local map: http://127.0.0.1:8002 . Restart and semantics: docs/map.md. Approved inclusive 10:45–11:00 America/Denver arrival window plus <=30min elapsed door-to-door journey; proposed October 20 test date retained. Local Leaflet/OSM streets, sampled statuses, mode/transfer controls and exact clicked-origin itinerary lines/time breakdown work. Backend complements arrive-by with bounded forward search; incomplete searches remain unknown.

23 tests passed. Independent routing review and real browser checks passed: transit and bike journeys, geometry, rejected over-duration candidate, filter invalidation, bicycle changes disabled, all sample states counted, no console errors. Bike time is labeled Bike / pushing. Initial both/1 samples: 4 qualifying, 36 bounded no qualifying returned, 5 unknown, 5 outside extract/not evaluated. No exhaustive coverage or optimality claim. UT-01 feedback has been received. Martijn requested a longer-term product vision before further POC additions. Noa completed the product/design vision draft; Martijn’s two product choices are pending. The previous patch proposal is deferred, not awaiting approval. Calibration and wider coverage remain backlog.

### Feedback received — patch proposal deferred for product vision

Martijn tested 300 E / 300 S and reported missing TRAX alternatives, difficulty discovering the alternatives dropdown, and mistaking a bus option for TRAX. Rue owns participant evidence and findings in docs/feedback.md; the original UT-01 request has been answered. This is one qualitative response, not broad usability validation.

Ash reproduced the routing issue at 40.7628276, -111.8825088 and all four intersection corners. Combined mode returns qualifying buses 455 and 220 but omits a qualifying Red Line 703 journey that TRAX-only returns: depart 10:23:08, Library 10:31–Stadium 10:40, arrive ART 10:49:47, elapsed 26m39s, zero changes. Train stop times match local GTFS. Raw combined OTP output already omits it; allowlists and app constraint filters are not the cause, and only three options returned, below the 20-option limit. Diagnostic output points to search-stage pruning; the precise internal decision was not traced. Bus 455 has lower generalized cost, leaves later and arrives earlier. No comfort weighting is configured.

Dot shared the diagnosis in personal Slack thread 1792273761.604929 and proposed preserving qualifying TRAX alternatives and clarifying alternatives/modes without comfort weighting. Martijn did not approve implementation; he instead requested a longer-term product vision rather than further POC additions. That patch proposal is deferred, not awaiting approval. UT-01 and the technical diagnosis remain evidence for design decisions, not an approved feature list.

Noa completed [docs/product-vision.md](product-vision.md), her charter and the team/project links in task 01a14bdc-5d28-72ab-abb3-1bb9485ad035. The draft recommends a place shortlist supported by a map, with a neighborhood-first alternative; evidence, hypotheses and staged acceptance outcomes are explicit. Dot presented the draft and two questions in Slack: discover neighborhoods versus compare known buildings; morning-only versus a return journey needed for the first useful product. Awaiting those product choices, not implementation approval. Martijn retains product authority; dot coordinates. No implementation is underway; the patch proposal remains deferred. No repeat message or additional approval request is needed.

The completed map cycle remains complete with 23 passing tests and its existing routing/browser evidence. The first review is no longer pending. Sampled coverage and bicycle calibration/profile gaps remain limitations; reliability collection stays backlog. Running services are preserved. Rue's feedback notes retain the participant evidence; this status supplies the later technical diagnosis and coordinator handoff.

The historical sections below record the earlier feasibility milestone and its earlier <=11:00-only semantics; their counts are not the new arrival-window map results. The new map supersedes the old viewer as the primary interface. Routine map status updates on the existing dashboard were delegated to the technical lead; unrelated cards/UI remain preserved.

# Durable handoff — 2026-10-17

## Actual outcome

The initial bounded transit AND bicycle feasibility spike ran against OTP 2.10.0. See docs/bicycle.md for complete bike evidence and reproduction. Local Git repository is initialized on main; files remain uncommitted. No remote, deployment, accounts, credentials, agreements, or ongoing collectors.

- Existing mise Java `temurin-25.0.3+9.0.LTS` works. Initial /usr/bin/java probe was misleading; AGENTS.md records the correct setup.
- Existing Colima docker profile started without requested configuration changes; official arm64 OTP image pinned at sha256:8d54e5c589186707ee365417f2202dc878c451fa3001b8edff07019531100933 downloaded. Colima's normal startup auto-activated its context; we restored the previous context. Martijn subsequently started the default profile and active context became colima. We did not override that later choice. Actual graph build used mise Java, not Docker; no duplicate build.
- Public UTA static feed downloaded locally (8,760,119 bytes). Calendar range Aug 16–Dec 5, 2026, timezone America/Denver, 5,856 active trips and four active services on proposed Oct 20 after calendar exceptions. TRAX route IDs: Blue 5907, Red 8246, Green 39020. S-Line 45389 and FrontRunner 41065 excluded. Live graph namespace is `1`.
- Geofabrik Utah PBF cropped with installed osmium complete_ways to [-111.99,40.68,-111.80,40.83]; resulting PBF 12,562,686 bytes. Full original remains ignored locally. Build restricted to Oct 19–22. Exact hashes/sources in config/input-manifest.json. OSM © OpenStreetMap contributors, ODbL.
- OTP graph: 128,820 vertices, 346,357 edges; build wall time 13.76s; maximum resident set 892,944,384 bytes (~852 MiB), 1 GiB heap. This measures this Mac/extract only. Logs in results/build.log and build-resources.txt. Cropped-network warnings and unlinked out-of-area UTA stops are expected limitations, not fixed or hidden.
- Completed nine transit scenarios × 50 sampled origins. See results table below. 2,070 returned boarding/alighting comparisons (202 distinct events across 46 trips) matched the exact local static stop_times; results/timetable-check.json has zero mismatches. This is feed consistency, not independent field truth or validation of every calendar/transfer rule.
- Thirteen unit tests pass, including interlining/stay-seated vehicle changes, boundaries, route exclusion, calendar exceptions and mocked query timeout. Independent live review checked qualifying legs and ART approach geometry.

## Results (50 origins per scenario)

| Modes | Max changes | Qualifying | No qualifying returned | Unknown | p50 ms | p95 ms |
|---|---:|---:|---:|---:|---:|---:|
| bus | 0 | 7 | 34 | 9 | 32.73 | 58.15 |
| bus | 1 | 8 | 35 | 7 | 31.75 | 51.91 |
| bus | 2 | 8 | 35 | 7 | 32.46 | 49.81 |
| TRAX | 0 | 2 | 15 | 33 | 26.79 | 45.22 |
| TRAX | 1 | 2 | 26 | 22 | 26.31 | 46.00 |
| TRAX | 2 | 2 | 26 | 22 | 27.20 | 41.96 |
| both | 0 | 7 | 35 | 8 | 30.40 | 47.53 |
| both | 1 | 8 | 35 | 7 | 33.92 | 56.96 |
| both | 2 | 8 | 35 | 7 | 33.74 | 60.64 |

Latency is observed local serial HTTP request plus validation; matrix was warm after the first 50-query run. First observed query was 349.6ms; this is not a controlled cold benchmark. p95 uses sorted index floor(.95*(n-1)). Origins are synthetic geographic samples, not validated homes. Search is bounded to 20 returned itineraries and PT30M window, with no pagination. A negative returned set is not proof of no possible route. Unknown includes routing errors such as no nearby stops, no connection in window, and walking preferable to transit. None is silently colored unreachable.

Real boundary example, grid-3-4: bus 1 departs 10:29:41, arrives 10:59:54, elapsed 30m13s → rejected. Red Line option departs 10:20:14, arrives 10:49:47, elapsed 29m33s and earliness 10m13s → qualifies. Each includes actual walking and waiting, not ride time alone. Exact 30m/late-by-one-second edges tested synthetically. No exhaustive timetable validation claimed.

## ART entrance evidence

Official public southwest entrance: 40.7609893415,-111.8451667792, active Building Access, OBJECTID 204, marked Not Accessible. University source: https://fmags.fm.utah.edu/arcgis/rest/services/mapservices/accessibility_wm/MapServer/0/query?where=OBJECTID%3D204&outFields=*&outSR=4326&f=pjson . Building record: https://fmags.fm.utah.edu/arcgis/rest/services/mapservices/structures/MapServer/0/query?where=building_number%3D38&outFields=*&outSR=4326&f=pjson .

OSM way33633143 identifies ART/ref38. Terminal footway1132502624 reaches node10559833024, 1.57m from official door. Independent decoded OTP geometry follows sidewalk/crossing/footway/steps453082091 and terminal footway, ending ~2.9m from official entrance. Evidence results/independent-entrance-geometry.json. Ordinary walking only; no wheelchair-accessibility claim, no UMFA/centroid substitution, no field verification.

## Remaining work and blockers

- Bicycle elevation work completed using official public USGS native 1/3-arcsecond DEM. Separate bike graph built in10.89s, peakRSS773,423,104bytes. Four named pairs tested uphill/downhill and against no-DEM graph;50 samples yielded11 qualifying/39 no qualifying returned. Library84.53m missing profile is unknown; three other named pairs have complete returned profiles. OTP aggregate elevation totals are untrusted due to upstream double-counting behavior; per-step profiles checked against DEM endpoints. See docs/bicycle.md. Remaining graph profile failures/calibration are team backlog, not a user blocker.
- UTA reuse/redistribution terms unresolved. Official terms point to developer.rideuta.com/TermsOfUse.aspx; hostname failed DNS resolution. Local public ingestion proceeded under the user's scope; no agreement accepted or redistribution. Resolve before publication, not a blocker to this completed local reading test.
- Oct 20, 2026 remains the proposed Tuesday test date, not explicitly chosen by user. All results label it.
- Wider geographic coverage, street snapping for sample origins, timetable/transfer edge cases, controlled cold benchmark and complete error categorization remain. SLC crop is not a full UTA accessibility model.
- Frontend is a browsable saved-results prototype at http://127.0.0.1:8000. Browser verified named transit and bike files load, with Denver-time clocks. MapLibre map and polished UI are later work. dashboard/ is owned by a separate task and was not modified.

Technical lead owns input/routing follow-through. Coordinator owns product/date decisions and broader independent acceptance. Available collaborator tools support direct messages, shared files, follow-ups and independent review; no orchestration framework added.

## Runtime at handoff

OTP development server remains on 127.0.0.1:8080 (PID 7894 at handoff), using mise Java. Stop that process when finished or restart via sh scripts/serve.sh. The extra docker Colima profile started by this task was empty and stopped after tests; Martijn's default Colima profile and active colima context were preserved. No recurring process/collector was created.

## Bicycle and viewer runtime

Separate bike OTP server on127.0.0.1:8081; read-only results viewer on127.0.0.1:8000. Existing transit server8080 retained. Restart with scripts/serve-bike.sh and python3 scripts/viewer.py; rerun sh scripts/run-bike.sh. No scheduled collector. Initial feasibility milestone complete; calibration/full-area mapping and feed redistribution review remain backlog. No user action currently blocks local development.
