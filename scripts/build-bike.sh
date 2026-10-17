#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p results data/bike-graph
cp config/bike-build-config.json data/bike-graph/build-config.json
cp data/graph/slc.osm.pbf data/bike-graph/slc.osm.pbf
/usr/bin/time -l mise exec java@temurin-25.0.3+9.0.LTS -- java -Xmx1G -jar data/otp-shaded-2.10.0.jar --abortOnUnknownConfig --build --save data/bike-graph > results/bike-build.log 2> results/bike-build-resources.txt
