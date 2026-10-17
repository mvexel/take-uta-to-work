# Working quick start (verified on this Mac)

Read AGENTS.md. Existing inputs and graph are in ignored data/. No host Java installation needed; mise Java 25 is installed. Run `sh scripts/build.sh` to rebuild, `sh scripts/serve.sh` in a foreground terminal, then `sh scripts/run-matrix.sh` in another. The matrix includes a static timetable cross-check. Server binds only 127.0.0.1. Stop it with Ctrl-C when finished. No ongoing collector is involved.

The following preparation notes describe input provenance and prerequisites. Several are now completed; docs/status.md is the current source of truth.

# Reproduce the routing spike

Public input downloads were performed for the local experiment; no legal acceptance, credentials, deployments or collectors. Downloads and outputs stay under ignored data/ and results/. Never redistribute UTA snapshots without verified rights. OSM is ODbL: attribute © OpenStreetMap contributors and preserve source/license information (https://www.openstreetmap.org/copyright).

Create local working directories: `mkdir -p data/graph results`.

1. Verify terms linked from https://www.rideuta.com/About-UTA/Terms-of-Use (developer terms at https://developer.rideuta.com/TermsOfUse.aspx could not be retrieved on setup). Public feed https://gtfsfeed.rideuta.com/GTFS.zip is identified but not downloaded. Once review permits local use, save as data/uta.gtfs.zip. Audit without extracting:

   `python3 scripts/spike.py audit data/uta.gtfs.zip --date 2026-10-20 > results/feed-audit.json`

   Inspect timezone America/Denver, active services/trips and calendar exceptions. Coverage range alone does not prove service exists that Tuesday. Record acquisition timestamp and source alongside SHA-256. Verify route short/long names and actual IDs; classify TRAX, bus, S-Line, FrontRunner separately.
2. Verify the pedestrian entrance using official campus information and mapped pedestrian access. Official building identity: https://map.utah.edu/index.html?code=ART ; address confirmation: https://www.finearts.utah.edu/about/contact-us . These establish ART, not a specific entrance. Set config/scenario.json coordinates, entrance_source and verified only after checking. Do not substitute UMFA or campus centroid.
3. Prepare a small SLC OSM PBF, buffered enough to avoid clipping valid paths; record source, SHA-256, bounds and timestamp. OTP consumes PBF. Do not download the full state before checking available memory. Current Colima docker profile has 2 GiB; this is not a measured graph requirement. Directional bike elevation remains a prerequisite for validated bike output. Set directional_elevation_verified only after checking the DEM input and uphill/downhill routes; the runner gates bike requests until then.
4. Supply the pinned OTP shaded JAR locally at data/otp-shaded-2.10.0.jar, verify its publisher checksum, and provide Java 25+. Upstream instructions: https://docs.opentripplanner.org/en/v2.10.0/Basic-Tutorial/ . Alternatively use an explicitly pinned upstream OTP 2.10.0 container after checking its supported architecture and digest. Existing Docker context is colima-docker. Do not silently change the user's global Docker context or resize Colima.
5. Put only the chosen OSM PBF and GTFS ZIP in data/graph/. Run the graph build in the foreground and record actual resources on macOS:

   `/usr/bin/time -l java -Xmx1G -jar data/otp-shaded-2.10.0.jar --build --save data/graph > results/build.log 2> results/build-resources.txt`

   The 1 GiB heap is a bounded starting experiment, not a recommended production size. Stop and reassess on memory failure. Then foreground serve:

   `mise exec java@temurin-25.0.3+9.0.LTS -- java -Xmx1G -jar data/otp-shaded-2.10.0.jar --load --serve --bindAddress 127.0.0.1 data/graph`

   Keep access local; do not expose publicly. Query the graph's routes { gtfsId shortName longName type } via its GTFS GraphQL API to resolve namespaced IDs; fill bus/trax/both allowlists. Feed IDs are not assumed to be UTA. The measured graph uses namespace 1. Configure no realtime updaters.
6. Create results/ and execute:

   `python3 scripts/spike.py run --mode both --changes 1 > results/both-1.json`

   Repeat bus/trax/both with 0/1/2; separately --mode bike --changes 0. This runs at most 50 serial requests per invocation, 60-second timeout each, 20 itineraries per origin, 30-minute search window. It is not an exhaustive accessibility calculation. Inspect results and query latency; preserve failure counts and warm/cold separation. Date defaults to proposed October 20, 2026, resolving to 11:00-06:00 using America/Denver.

Query fields were checked against pinned schema source: https://raw.githubusercontent.com/opentripplanner/OpenTripPlanner/v2.10.0/application/src/main/resources/org/opentripplanner/apis/gtfs/schema.graphqls . Runtime queries have now succeeded; see docs/status.md and ignored results/ for measured evidence. Tests use clearly synthetic leg/calendar fixtures, never real result claims.
