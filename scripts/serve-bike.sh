#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
exec mise exec java@temurin-25.0.3+9.0.LTS -- java -Xmx1G -jar data/otp-shaded-2.10.0.jar --load --serve --bindAddress 127.0.0.1 --port 8081 data/bike-graph
