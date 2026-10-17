#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p results
python3 scripts/validate_bike.py > results/bike-direction-validation.json
python3 scripts/spike.py run --config config/bike-scenario.json --origins config/named-origins.json --endpoint http://localhost:8081/otp/gtfs/v1 --mode bike --changes 0 > results/named-bike.json
python3 scripts/spike.py run --config config/bike-scenario.json --endpoint http://localhost:8081/otp/gtfs/v1 --mode bike --changes 0 > results/bike-sample.json
python3 scripts/spike.py run --origins config/named-origins.json --mode both --changes 1 > results/named-transit.json
