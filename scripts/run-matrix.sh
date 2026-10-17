#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
mkdir -p results
for mode in bus trax both; do
  for cap in 0 1 2; do
    python3 scripts/spike.py run --mode "$mode" --changes "$cap" > "results/$mode-$cap.json"
  done
done
python3 scripts/check_timetable.py > results/timetable-check.json
