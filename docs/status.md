# Technical status

The local routing prototype runs OpenTripPlanner 2.10.0 with pinned inputs and separate transit and bicycle graphs. This document contains public technical evidence; organization coordination and participant records are maintained separately in a private repository.

## Working application

- Map: http://127.0.0.1:8002 . See [restart instructions](map.md).
- Transit engine: loopback 8080; bicycle/DEM engine: loopback 8081.
- Current map scenario: October 20, 2026, 10:45–11:00 America/Denver arrival; elapsed journey <=30 minutes. Earlier spike results used only the 11:00 deadline and are not interchangeable with map results.
- The initial map both/1 sample returned 4 qualifying, 36 bounded negatives, 5 unknown and 5 outside-extract/not-evaluated origins. Fifty synthetic points are not residences or continuous neighborhood coverage.
- 23 routing/adapter tests passed at the implementation milestone. Browser checks covered route geometry, transit/bike examples, filter invalidation and duration rejection. These checks do not establish complete alternatives, field accuracy or general usability.

## Inputs and measured experiment

UTA static feed: 8,760,119 bytes, service range August 16–December 5, 2026; 5,856 active trips across four services on October 20 after exceptions. Timezone America/Denver. Verified TRAX IDs are Blue 5907, Red 8246 and Green 39020, graph namespace 1; S-Line 45389 and FrontRunner 41065 are excluded. Input hashes and sources are in config/input-manifest.json. UTA redistribution terms remain unresolved; no feed is included.

OSM crop bounds [-111.99,40.68,-111.80,40.83], PBF 12,562,686 bytes. Transit graph built in 13.76 seconds, peak resident memory 892,944,384 bytes (~852 MiB), using a 1 GiB Java heap. Graph contains 128,820 vertices and 346,357 edges. These measurements apply to this local extract only. Out-of-area unlinked stops and clipped paths limit geographic validity.

The initial deadline-only transit experiment ran nine scenarios across 50 origins (450 queries). 2,070 boarding/alighting comparisons, representing 202 distinct events across 46 trips, matched the local static stop_times. This checks feed consistency, not independent field truth. Per-scenario warm serial p50 latency was approximately 27–34 ms and p95 43–59 ms; no controlled cold benchmark is claimed.

The separate bicycle graph built in 10.89 seconds with peak resident memory 773,423,104 bytes (~738 MiB). USGS native 1/3 arcsecond elevation inputs and directional checks are documented in [bicycle evidence](bicycle.md). Bicycle estimates lack empirical rider calibration; profile failures remain, and OTP aggregate elevation fields are untrusted and omitted from UI totals.

## Destination verification

ART southwest public entrance: 40.7609893415, -111.8451667792. Official university Building Access record OBJECTID 204 is marked not accessible. The mapped terminal footway and returned route geometry approach within about 3 m of the door. Ordinary walking only; no wheelchair or field-verification claim. Official entrance source is recorded in config/scenario.json. UMFA and campus centroid are not substituted.

## Known routing limitations

The combined-mode search may prune a qualifying rail alternative before it reaches the application, even when a TRAX-only search returns it. Correct allowlists, available seats in an output limit, and a successful query do not guarantee alternative completeness. No comfort weighting is configured. Any future correction needs a bounded regression test and independent review.

No qualifying returned route is a bounded observation, not proof of unreachable coverage. Incomplete search, missing elevation and transport errors remain separate. No reliability collector runs and no historical reliability values are validated. Planned facilities are not assumed usable.

## Private preview correction under review

The graph-derived arrival range is October 20–22, reserving October 19 for overnight search context. This replaces the incorrect feed-wide date acceptance. See [private preview](private-preview.md) for packaging, limits and outstanding runtime validation. No remote deployment has occurred.
