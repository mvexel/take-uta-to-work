#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p results
cp config/build-config.json data/graph/build-config.json
/usr/bin/time -l mise exec java@temurin-25.0.3+9.0.LTS -- java -Xmx1G -jar data/otp-shaded-2.10.0.jar --build --save data/graph > results/build.log 2> results/build-resources.txt
