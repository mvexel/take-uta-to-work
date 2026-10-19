# Private preview (draft for review)

Single trusted operator over SSH forwarding only. No public launch or remote deployment has occurred. Host selection and private infrastructure details are tracked separately.

## Dates and inputs

OTP 2.10.0 service bounds are inclusive: https://docs.opentripplanner.org/en/v2.10.0/BuildConfiguration/#transitserviceend . The loaded graph covers October 19–22, not the full feed period. The app admits October 20 00:00 through October 22 23:59 Denver, reserving the first service day for overnight/search context. The same range applies to bike comparisons. These limits do not promise transit service at every minute. Later feeds with unusually long service days need renewed boundary analysis.

Set PREVIEW_DATA to an absolute path containing the existing private data directory. No graph build/download occurs on startup. The app verifies config/preview-artifacts.json SHA-256 hashes of the JAR, graphs, graph configuration and display layer. Input files must remain immutable while running. Regenerate hashes deliberately after reviewed rebuilds and restart; graph hashes also invalidate cache identity. Data stays outside Git and images. UTA redistribution terms remain unresolved.

## Local validation

Use the existing Docker runtime, without resizing Colima or changing global context:

```sh
export PREVIEW_DATA="$PWD/data"
docker compose -f compose.preview.yaml -p uta-review config --quiet
docker compose -f compose.preview.yaml -p uta-review build app
python3 -m unittest discover -s tests -p 'test_*.py'
node --test tests/test_explore_ui.cjs
```

Tests currently use the local private graph configuration/identity; routing fixtures are synthetic. Both base images are pinned by digest. The app review tag is a draft local artifact: freeze exact source and target-architecture image/archive hashes before transfer. ARM validation does not prove amd64 execution. Target rollout must use an already reviewed/loaded image with --no-build, never implicitly build on a shared host.

Memory limits: each OTP 1536 MiB with 1 GiB heap, app 256 MiB; CPU ceilings .75/.75/.5. No container swap. Total 3.25 GiB/2 CPU ceilings. Existing Colima has 2 GiB; do not start all three there. Sequential smoke tests cannot establish full-stack performance. Limits bound impact; target-runtime memory and latency acceptance remain deployment gates.

## Access, bounds and rollback

Only 127.0.0.1:8003 is published; OTP uses an internal project network without published ports. Reach it through existing SSH forwarding to the same loopback port. Check local port availability: the original local app already uses 8003. Host-local processes/administrators can reach the preview. No per-user authentication or cancellation ownership is provided; tabs share a single-operator session.

Containers are non-root/read-only, with dropped capabilities, no-new-privileges and rotated logs (2 x 5 MiB each). Inputs are read-only, results use a project volume. Restart policy is no: this is explicitly started/stopped temporary preview. OTP health proves only TCP listening; a real itinerary is mandatory for acceptance.

Eight concurrent HTTP connections maximum (503 beyond this), two point requests and one area calculation (429 when busy). New scenarios no longer automatically cancel active work. Explicit cancellation waits for in-flight routing calls; Retry can briefly report busy. Socket timeout is 10 seconds; outbound OTP calls have 30-second timeouts and finite pagination, not a guaranteed total wall-clock deadline. Only regular, non-symlink files named `area-<20 lowercase hexadecimal characters>.json` are disposable cache entries; validation reports are excluded. Cache evicts on access/completion after 24 hours, eight files or 64 MiB; retain at most two terminal job records. Public multiuser serving remains out of scope.

Before rollout: independent review, exact hashes, selected-host/runtime checks, available port/disk/headroom and scoped execution authorization. Verify bindings, resource limits, health and real date-boundary itineraries, then access through SSH. No DNS/Caddy/firewall/credentials are needed for this access model. Podman compatibility or Komodo registration must be established separately.

Affected resources: one project, three containers, one internal network, one results volume and a private input directory. Rollback stops only the new project and preserves inputs/results. No volume pruning, shared ingress restart, broad resource sync, or changes to existing workloads.
