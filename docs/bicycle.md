# Bicycle feasibility evidence

Completed 2026-10-17. Source: USGS 1/3 Arc Second n41w112 20260519, public-domain 3DEP bare-earth DEM, metres NAVD88; native geographic NAD83 EPSG:4269. Source URL and SHA-256 are in config/bike-input-manifest.json. Official dataset metadata: https://data.usgs.gov/datacatalog/data/USGS%3A3a81321b-c153-416f-98b7-cc8e5f0e17c3 .

Installed GDAL cropped the dated official S3 GeoTIFF via byte-range access, avoiding a full 403 MB download. Local crop is ~20 MB, 2215×1837 pixels, native 1/3 arcsecond (~8×10m), bounds [-111.995,40.6699074,-111.7899074,40.84]. Float32, declared NoData -999999, 100% valid pixels, tiled 512×512. No reprojection/resampling. The earlier dynamic-service export completed but was not downloaded or used.

```sh
mkdir -p data/bike-graph
gdal_translate -projwin -111.995 40.84 -111.79 40.67 -projwin_srs EPSG:4326 -co TILED=YES -co BLOCKXSIZE=512 -co BLOCKYSIZE=512 /vsicurl/https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/13/TIFF/historical/n41w112/USGS_13_n41w112_20260519.tif data/bike-graph/slc.dem.tif
gdalinfo -stats -json data/bike-graph/slc.dem.tif > results/dem-info.json
sh scripts/build-bike.sh
```

Do not overwrite an existing crop casually; retain hashes and update the manifest if regeneration changes bytes. Build config uses demDefaults.elevationUnitMultiplier=1 and distanceBetweenElevationSamples=10. --abortOnUnknownConfig prevents silently ignored settings. The bike graph contains streets/DEM only and preserves the original transit graph. Final build:10.89s wall time;773,423,104 bytes maximum RSS (~738 MiB);1 GiB heap.

In separate foreground terminals:

```sh
sh scripts/serve.sh       # original graph, localhost:8080
sh scripts/serve-bike.sh  # DEM graph, localhost:8081
```

Then reproduce and view:

```sh
sh scripts/run-bike.sh
python3 -m unittest discover -s tests -v
python3 scripts/viewer.py # http://127.0.0.1:8000
```

Bike speed is maximum 4.17m/s on flat ground, not average journey speed. Journey includes permitted walking/pushing segments; no transit, rental or mixed bike/transit. No empirical rider calibration. Compare arrival deadline11:00 America/Denver on proposed2026-10-20. All bike examples arrive at11:00 with zero earliness; return journeys use the same deadline for controlled directional comparison.

| Named public landmark | To ART, DEM | ART to landmark, DEM | To ART, no DEM | Profile status |
|---|---:|---:|---:|---|
| Library eastbound platform |49m10s|22m30s|28m25s|84.53m unprofiled; unknown qualification|
| Trolley eastbound platform |40m03s|13m53s|20m19s|complete returned profiles|
| 900 East eastbound platform |34m22s|9m48s|15m59s|complete returned profiles|
| Stadium Station |10m53s|3m18s|5m41s|complete returned profiles; qualifies|

Named coordinates come from exact GTFS stops, not residential addresses. Directional preflight makes16 real requests:4 landmarks×2 directions×2 graphs. It verifies bike/walk modes with no transit, profile endpoints within3m of independently sampled DEM, and uphill/downhill duration differences. For this experiment only, partial profile comparison permits at most100m AND5% missing; actual reachability runner labels any positive-length missing profile unknown. Library is not silently treated as validated.

The50 geographic bike samples returned11 qualifying routes and39 no qualifying returned routes. This is a sampled, model-dependent result—not a polygon or exhaustive area coverage.

## OTP issue and limitations

OTP2.10.0 itinerary elevationGained/Lost add two internally computed totals, giving roughly doubled values here. Pinned source contains an explicit TODO about this: https://github.com/opentripplanner/OpenTripPlanner/blob/v2.10.0/application/src/main/java/org/opentripplanner/model/plan/Itinerary.java . We retain raw fields with _untrusted names, omit them from viewer summary, and validate per-step profiles instead. We do not simply divide by two. ART DEM1436.62m and Library1300.70m agree with profile endpoints1436.55m/1299.90m; profile net136.65m, not the API aggregate~270m.

Build reports22 flattened profiles,77 profile failures and1 outside-DEM issue. Thus pixel completeness is not graph completeness. Three named pairs have complete returned profiles, not proof every street is correct. Bare-earth DEMs do not model bridge decks/building stairs perfectly. Library gap and upstream aggregate issue remain backlog. No field validation or full bike suitability/safety claim.

Independent agent checked source/units, DEM metadata/endpoints, actual saved bike legs/statuses and13 passing tests. Browser verified actual saved runs and fixed UTC strings incorrectly displayed as local clock times; all viewer clocks now use America/Denver explicitly.
