# Parameters-first exploration slice

This local implementation starts with the commute parameters and then draws an approximate target/fringe contour. Select any supported origin to inspect real scheduled journeys; compare up to six points under the same scenario. Neighborhood boundaries, suitability rankings, accounts, persistent shortlists, return trips and reliability are not part of this slice.

## Run locally

Python 3.9+ standard library, the existing OTP 2.10.0 graph on 127.0.0.1:8080, and the bicycle/DEM graph on 8081 are required. Do not start duplicate engine processes. See [map instructions](map.md) for graph startup. From this checkout:

```sh
python3 scripts/explore_server.py
```

Open http://127.0.0.1:8003 . The original prototype can remain on 8002. All servers bind to loopback. No external tiles, runtime assets, account or paid service is needed. Inputs remain under ignored `data/`. An isolated worktree can symlink its ignored `data` directory to existing local inputs. Stop the web server with Ctrl-C.

ART's verified southwest entrance is the only destination in this first study. It has steps and is not an accessible entrance. Arrival defaults to October 20, 2026 at 11:00 America/Denver, with arrival permitted up to 15 minutes earlier. Date/time can be changed within the loaded static feed range (August 16–December 5). Ambiguous daylight-saving times are rejected. Target duration is 10–60 minutes; the clearly labeled fringe extends ten minutes beyond it. This is a soft preference, not a filter that removes longer returned journeys.

## Area method and geographic accuracy

The contour study bounds are west −111.91, south 40.735, east −111.825, north 40.79, inside the larger loaded street extract. The initial grid has cells no larger than approximately 250 m in latitude/longitude converted with a local metres-per-degree scale. Each cell queries its four corners and center; corners are shared with adjacent cells. This is 1,505 unique origins, not the original 50-point sample.

A target cell requires all five origins to return a valid journey within target. A fringe cell requires all five to be within target plus ten minutes. Mixed, error, incomplete or unsupported samples cannot be interpolated into a positive cell. They remain gray/unknown. A bounded outside-band cell requires all five origins to have completed searches without a returned journey in target/fringe. Its label is a bounded observation, not proof of inaccessibility. A valid positive journey can support a positive sample even when another mode search is incomplete; the area still does not claim the fastest or complete set of alternatives.

The visible contour follows raster boundaries, retaining separate components and holes. There is no convex hull, kernel smoothing or triangulation across gaps. This is a conservative *sample-supported approximate area guide*, not guaranteed coverage of every coordinate inside a polygon. Discontinuities, street snapping, barriers and schedule effects may occur between queried origins. Exact point checks remain authoritative. Outside the contour study no area inference is made; clicks inside the larger street extract still receive actual routing checks.

The reproducible validation script queries four additional quarter-cell positions inside every target/fringe cell, independently of the five classification points:

```sh
python3 scripts/validate_area.py --mode both --cell-metres 250
```

Raw grid and validation evidence stays in ignored `results/`. These checks estimate band disagreement for the tested scenario, not a universal spatial or travel-time error bound, and do not measure missed reachable islands in unknown cells. The preliminary 400 m pilot queried 611 origins in 97.04 seconds. Its 576 held-out positive-cell points had two band disagreements (0.35%): one exceeded target by 78 seconds and one exceeded fringe by 9 seconds. The 250 m run queried 1,505 origins in 213.61 seconds and classified 212 target, 186 fringe, 291 unknown and 36 bounded outside-band cells. Of 1,592 held-out positive-cell checks, seven crossed a duration band (1–52 seconds beyond its boundary) and one returned a routing error: 0.50% combined disagreement/uncomputed. These measurements apply only to the default both/1 October 20 scenario; other modes, caps, dates and targets do not inherit that measured rate. No production accuracy guarantee follows.

## Routing and alternative visibility

Each transit query uses the reviewed route allowlists, walking access/egress/transfers, and 0/1/2 maximum vehicle changes. Bus + TRAX searches combined, TRAX-only and bus-only, then deduplicates itineraries. The known qualifying Red Line alternative is retained even when the combined OTP response prunes it. TRAX excludes S-Line and FrontRunner. Stay-seated interlining does not count as a change. Returned legs are checked independently for allowed routes/modes, elapsed duration, arrival window and changes.

The retrieval horizon is independent of target/fringe: arrive-by search with a 90-minute window, plus up to three forward pages of 20 results from 90 minutes before the earliest permitted arrival, over a 105-minute departure window. Page exhaustion and errors are explicit. This does not enumerate every itinerary or prove an optimum. Later and longer returned journeys remain inspectable. Each point exposes departure/arrival (including date), elapsed, earliness, walk/wait/ride/bike breakdown and legs. No reliability claim.

Bike is separate from transit, uses the DEM graph with maximum flat speed 4.17 m/s, and preserves missing elevation as unknown. No e-bike adjustments or aggregate ascent claims. See [bicycle limitations](bicycle.md).

## Jobs, identity and interaction safety

Only one area calculation runs at a time, using three query workers. A changed mode/date/cap cancels the obsolete job after in-flight requests return. The two point-query slots remain separate so point inspection can work during area computation. This is explicit on-demand work, not an ongoing collector. Requests have bounded timeouts.

Completed grids are cached locally under an identity derived from scenario, routing policy and input-manifest/configuration hashes. Duration changes reclassify measured origin times without rerouting; they do not invent interpolated times. No point shortlist is persisted. Restart after rebuilding either graph, updating manifests, or changing routing policy. Local disk caches are disposable and never published.

Parameter edits immediately clear area geometry, route geometry and point evidence; selected coordinates remain marked “Needs recheck.” Applying parameters rechecks retained points. Each response is bound to a request generation; aborted or older responses cannot replace the current scenario. Remove affects only the selected point. Errors, pending, unknown, bounded negatives and outside-study results remain separate.

## Verification

```sh
python3 -m unittest discover -s tests -v
node --check web/explore.js
node --test tests/test_explore_ui.cjs
```

Tests cover time/target boundaries, allowlists, transfer caps, rail alternatives, partial failures, cancelled-job restart, mixed-cell uncertainty and cached duration reclassification. Browser QA must include two points (one beyond target), alternative selection, removal, parameter changes, interrupted requests, and mobile layout. A working local slice and tests do not substitute for independent review.

Local verification of four new routing cases (both/1, TRAX/0, bus/2, bike/0) checked 284 transit boarding/alighting events against the exact static feed with zero mismatches. The bike case correctly remained unknown for missing elevation. Warm point latencies in that small uncontrolled run were 88–424 ms; no broad latency percentile is inferred.

Route-overlay consistency: selecting a different itinerary clears the shown route until Show this journey is pressed; rechecking clears the route immediately while pending. Node handler regressions verify selection, failed recheck, repeated requests and parameter invalidation using synthetic DOM/Leaflet doubles. This is not a substitute for browser verification.
