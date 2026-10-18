# Product specification and architecture

An open-source, self-hostable website for exploring where to live based on a commute to a known workplace. Initial scope is Salt Lake City and the University of Utah Art Building (ART, building 38). Neighborhood discovery is the product direction; evidence remains attached to evaluated origins. Return journeys, rental listings, accounts and historical reliability are outside current implementation scope.

## Routing contract

The current technical scenario is Tuesday October 20, 2026, arriving 10:45–11:00 America/Denver with at most 1,800 seconds elapsed. These are prototype test settings, not universal product constraints. Elapsed time includes access/egress walking, waiting, riding and transfers; earliness is reported separately. Separate bicycle-only from transit-with-walking. Transit selectors are bus, TRAX, or both, with maximum 0/1/2 vehicle changes. TRAX excludes S-Line and FrontRunner. Stay-seated interlining does not count as a vehicle change.

## Architecture

- OpenTripPlanner 2.10.0 with the stable GTFS GraphQL planConnection API. The original isochrone API was removed in 2.6; this application uses sampled-origin itineraries, not built-in reachability polygons.
- Python standard-library loopback server and routing adapter; a local Leaflet 1.9.4 frontend uses vendored assets and an OSM display layer. No external tile service or paid API is required at runtime.
- Separate transit/street graph on port 8080 and bicycle/DEM graph on port 8081. Map server on port 8002. Route allowlists are inspected against returned legs, not inferred from generic rail mode alone.
- Arrive-by search is supplemented by bounded forward search if no qualifying transit journey is found. Unknown, request error, not evaluated and no qualifying returned route remain distinct. No result implies exhaustive search or optimality.
- Bicycle speed is a maximum 4.17 m/s on flat ground, with directional elevation treatment from USGS 3DEP. Missing profiles are unknown. Calibration and graph profile failures remain limitations.

## Evidence and limits

See [technical status](status.md), [bicycle evidence](bicycle.md), [map instructions](map.md) and [development guide](development.md). Combined-mode routing can omit qualifying rail alternatives that a rail-only search returns. The current interface does not promise a complete set of mode alternatives. Schedule estimates are not observed reliability or field-validated travel times.

OSM inputs require ODbL attribution. UTA reuse/redistribution terms remain unresolved; raw feed snapshots are not distributed. Source URLs and hashes are recorded in config/. Organization coordination, participant records and internal design planning are maintained separately in a private repository; they are not part of this public specification.
