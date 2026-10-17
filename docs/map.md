# Local commute map

Open http://127.0.0.1:8002 . Leaflet 1.9.4 and its license are vendored in web/vendor; there are no external tiles or runtime asset requests. The local OSM display layer is deliberately sparse. It is not the routing graph or a continuous reachability polygon.

## Restart

From /Users/mvexel/dev/take-uta-to-work, run each server in its own terminal (skip a command if that port is already serving):

```sh
sh scripts/serve.sh
sh scripts/serve-bike.sh
python3 scripts/map_server.py
```

These use existing local graphs and mise Java. The map server needs Python 3.9+ and no Python packages. Stop with Ctrl-C. All bind to loopback. No Docker host is needed for these Java processes; Martijn uses Colima for Docker. See development.md and bicycle.md for input preparation and graph rebuilding.

To regenerate the display layer from the local OSM graph input with installed osmium:

```sh
python3 scripts/prepare_map.py
```

This reads data/graph/slc.osm.pbf, writes only data/map-streets.geojson, and makes no network requests. Major/residential/pedestrian streets and campus paths provide orientation; proposed/construction facilities are excluded. OSM attribution remains visible. Downloaded inputs and generated results remain ignored by Git.

## Meaning of results

Select bus, TRAX, both, or bike and a maximum of 0, 1, or 2 vehicle changes. Bike disables the vehicle-change control. Evaluate the 50 synthetic sample locations, choose one from the list, or click an exact origin on the map. Click queries use that coordinate, not the nearest sample. A returned journey shows its geometry, leg details, departure/arrival, elapsed time, earliness and walking/waiting/riding breakdown. Bike / pushing includes dismount sections.

The test date is proposed Tuesday October 20, 2026. The approved arrival window is inclusive 10:45–11:00 America/Denver, with elapsed journey <=1800 seconds. All walking, inter-leg waiting and riding count. Earliness is separate. TRAX uses verified route IDs; S-Line and FrontRunner are excluded. The destination is the verified ART southwest public entrance, with steps and no accessibility claim.

The adapter first searches arrive-by 11:00. If transit has no qualifying returned option, it searches forward from 10:15 (the earliest possible departure for a qualifying journey), up to three pages of 20 options. Hitting the page limit is unknown. A bounded negative means only no qualifying returned route, never proof that a location is unreachable. Engine errors, incomplete searches, elevation gaps and outside-extract coordinates retain distinct states. Positive results also do not claim optimality or complete alternative enumeration.

Samples are synthetic points, not homes; five fall outside the tested crop and are explicitly not evaluated. Bicycle speed is 4.17 m/s maximum on flat terrain with directional DEM treatment; rider calibration and some graph elevation gaps remain unresolved. Untrusted OTP aggregate elevation totals are omitted. See bicycle.md for evidence.

/api/sample caches by mode/change cap for the life of the map process and saves ignored results/map-*.json. Restart after changing inputs or routing policy to invalidate the cache. Exact-origin queries are uncached. The initial both/1 run returned 4 qualifying, 36 bounded negatives, 5 unknown and 5 not evaluated. Timing and counts depend on the local graph and current search bounds.

## Verification

```sh
python3 -m unittest discover -s tests -v
node --check web/map.js
```

23 tests passed. Independent routing review checked arrival boundaries, capped-search unknown behavior and a real Stadium bicycle journey. Browser checks covered local street/sample rendering, route geometry, transit/bike journeys, rejected over-duration candidate, filter invalidation and disabled bike transfer control, with no console errors. Examples observed in the browser: grid-3-4 both/1 26m39s arriving 10:52:07; grid-3-6 bike 14m25s arriving 11:00. These are computed examples, not guarantees.
