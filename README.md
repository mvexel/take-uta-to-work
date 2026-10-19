# Take UTA to Work

A local, open-source website project asking where a person could live within 30 minutes of the University of Utah Art Building by transit with walking, or by bicycle. Includes a bounded OTP routing experiment and a working local commute map.

## Local development

Python 3.9+ with standard library is sufficient for tests and the report viewer. OTP 2.10.0 needs Java 25+ or a compatible container runtime. No system packages are installed by this project.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/map_server.py
```

Open http://127.0.0.1:8002. See [map instructions](docs/map.md) to start the two local routing servers, then inspect exact-origin journeys or evaluate sampled locations. The map uses local assets and OSM streets. The older saved-results viewer remains available with `python3 scripts/viewer.py` on port 8000.

Read [development instructions](docs/development.md), [product specification and architecture](docs/project.md), and [technical status](docs/status.md) before attempting routing. The transit spike has measured results for nine scenarios; bicycle directional elevation tests also passed for the bounded experiment. See [bike evidence](docs/bicycle.md). See the status document for evidence and limitations. Code is MIT licensed; third-party data has separate terms.

Organization coordination, team charters, participant feedback and internal planning are maintained separately in a private repository. This repository contains code and public technical documentation.

## Parameters-first exploration

The new local exploration slice runs at http://127.0.0.1:8003 with `python3 scripts/explore_server.py`. It provides an approximate target/fringe raster contour and exact point comparisons. See [method, measured limits and development instructions](docs/exploration.md). The original sampled-point prototype remains on port 8002.
