# Product vision — a commute-informed housing decision

Owner: [noa, product and design lead](team/noa.md). **Draft for Martijn, 2026-10-17; direction proposed, no implementation commissioned.** Martijn is the human product owner; dot coordinates priorities. This draft responds to his request for a longer-term vision and supersedes treating the proposed UT-01 patch cycle as the next product direction. [Feedback](feedback.md) retains the evidence; [status](status.md) retains technical truth.

## The decision we help someone make

“Which places should I seriously consider living in, given the commute I am willing to make?” The product should help a person narrow a housing search, compare concrete candidates and leave with a defensible shortlist and the uncertainties still worth checking. A useful outcome may be “keep both places and try the walk to the train,” not a single winner.

**Proposed core user:** someone considering a move who has a known work destination and meaningful commute constraints. Start with Martijn and ART; whether this should serve other people or destinations is an open choice. Housing cost, availability and the rest of life matter, but this product supplies the commute part of the decision rather than pretending to evaluate the whole home.

## What is established, and what is not

- **Established requirements:** local operation now; open-source and self-hostable ambition without paid APIs; ART as the current destination; at most 30 minutes door-to-door, transit with walking or bicycle, transit mode and vehicle-change limits. Current approved arrival window is 10:45–11:00 America/Denver. October 20 is a proposed test date, not a confirmed recurring schedule. Elapsed time includes walking, waiting, riding and transfers; the arrival window is separate. TRAX excludes S-Line and FrontRunner. No listings or accounts are required.
- **Evidence:** the POC computes clicked-origin journeys and sampled results. In UT-01, Martijn reported trying an intersection near a building under consideration, preferring TRAX comfort, overlooking alternate trips initially and confusing a bus with rail. Ash reproduced a qualifying TRAX journey absent from combined search. These support legible, meaningful alternatives; one self-reported session does not establish a general user journey or a need for comfort weights.
- **Known limits:** sampled origins are not residences or exhaustive coverage; bounded search can miss alternatives; bike times are uncalibrated; reliability is not measured. UTA redistribution rights remain unresolved. ART's verified southwest entrance includes steps and carries no accessibility claim. A schedule match is not a dependable daily commute guarantee.
- **Hypotheses to test:** people benefit more from comparing a few places across explicit tradeoffs than from finding the fastest trip; they need to revisit their reasoning; broader neighborhood exploration is useful before an exact address is known. These are design proposals, not observed requirements.

## Two directions, one recommendation

**Recommend a place shortlist with a supporting map.** Begin with a commute brief, explore places, and keep a few candidates in a comparison workspace. Routes explain each candidate. This connects exploration to an actual decision and accommodates the concrete building in UT-01 without assuming every user already has an address.

**Alternative: a map-first neighborhood explorer.** Begin with an overview of promising areas and drill into places. This may suit an early housing search, but currently risks making sparse samples look like comprehensive neighborhood judgments. Retain it as a possible entry point once broader representative evidence exists; do not make a colored reachability surface the product's central promise now.

## The eventual journey

1. **Describe the commute.** A compact, always-visible brief records destination/entrance, date or schedule scenario, arrival window, duration limit, allowed modes and changes. Distinguish hard constraints from preferences: “TRAX preferred” need not mean “exclude buses.” Show current assumptions rather than silently inventing a typical weekday.
2. **Explore possible places.** Locate an intersection, landmark or exact candidate on a map, or inspect evaluated samples. The map answers where the evidence is, with a matching list for navigation without map precision. Neighborhood names provide orientation; each commute finding remains attached to an evaluated point. Do not call an entire neighborhood viable because one point qualifies.
3. **Understand a candidate.** A place summary gives the finding in plain language, the scenario and the consequential tradeoffs: mode/line, door-to-door time, walking, departure/arrival and changes. A few visible alternative summaries make differences apparent before opening full legs. Selection reveals walking and vehicle legs with text and symbols as well as color. No fastest-trip default should imply that other modes are unsuitable or absent.
4. **Compare places on equal terms.** Keep perhaps two to four candidates side by side under the same brief. Compare the commute someone would actually choose at each place, not just each place's fastest returned time. Show why a slower rail option could remain attractive without converting comfort into an invented score. Mark different scenarios or incomplete searches explicitly; never present them as a clean like-for-like ranking. A bike estimate can inform investigation while its calibration warning stays beside the time.
5. **Revisit the decision.** Retain candidate labels, selected alternatives, short personal notes and the scenario/evidence date in a lightweight local record. On return, make clear what is saved evidence and what has been recomputed. Let the user change the brief and reassess without silently treating old results as current. Local persistence or a portable file is a design choice for later validation; accounts and property feeds are unnecessary prerequisites.

## Information architecture and trust

Three primary concepts: **commute brief → places → journeys**. Explore and Compare are views of the same places, not separate tools. “How this was calculated” is contextual evidence available from a finding, with detailed provenance behind it. The project dashboard stays a team tool, not part of the housing journey.

The first-level finding distinguishes “a journey meets this brief,” “no matching journey returned in this search,” and “not enough information,” with an explanation for uncomputed, outside-area or incomplete results. Positive findings also say alternatives may be missing. Use clear language beside the decision, not a blanket disclaimer in a footer or a fabricated confidence percentage. Mode distinctions must survive color loss and be available in text. Changing the brief makes stale comparisons visible immediately.

## Product principles and MVP boundary

Explain choices before optimizing them. Preserve user agency over comfort and tradeoffs. Make uncertainty specific and actionable. Start with places people recognize, minimize input and do not require private home addresses. Keep results inspectable and reproducible using open tooling and attributable inputs. Accessibility of the interface matters; it must not be confused with verified accessibility of a route.

**Proposed first useful MVP:** one destination, a clearly bounded local study area and one explicit commute scenario; explore exact places, understand meaningful returned alternatives, compare a small shortlist and retain enough context to revisit it. Transit must be trustworthy for the supported scenario; bike remains explicitly experimental until calibrated. Preserve the current constraints unless Martijn changes them. The MVP should let Martijn explain why he would keep or reject two candidates and what he still needs to verify, without coaching.

**Non-goals:** rental inventory, accounts, automated neighborhood/property rankings, inferred comfort scores, daily navigation or live departure alerts, comprehensive UTA coverage, unsupported reliability claims, and public launch. Return journeys, multiple household destinations and other schedules may matter later, but are open scope decisions rather than silently added MVP requirements. Reliability feed analysis remains backlog; no collection is authorized here.

## A staged path, with evidence gates

1. **Agree the decision and sketch its flow.** Use two familiar candidate places to review the proposed brief/place/compare journey with rue. No redesign build is commissioned. Gate: Martijn confirms which decision comes first and what a useful comparison must explain.
2. **Make one comparison credible.** Ash assesses the smallest technical slice supporting that journey, including meaningful mode alternatives and honest search limits. Noa specifies information hierarchy and states; rue tests interpretation; independent review checks routing changes. Gate: verified calculations plus an unaided comparison in which the participant distinguishes bus/rail, understands uncertainty and can explain a preference. A technical pass alone is insufficient.
3. **Make the decision reusable.** Validate revisiting a shortlist, scenario changes and representative exploration beyond the initial examples. Expand tested origins and calibrate bike estimates as evidence allows. Gate: a returning user can tell what changed and which places still warrant consideration; no extrapolation from one successful session.
4. **Broaden only against a demonstrated need.** Consider other destinations/schedules, return journeys and measured reliability. Public availability requires a separate scope decision, data-rights review and operational plan. Open-source ambition does not imply permission to redistribute feeds or deploy now.

## Two questions for Martijn, via dot

1. When you next use this, is the first decision **which neighborhoods to investigate**, or **which of a few known buildings/places to keep considering**? This determines the starting view and how urgently broader geographic evidence is needed.
2. For a place to make your shortlist, is a qualifying **morning trip to ART** enough for this first useful version, or must it also demonstrate a workable **trip home or another regular arrival time**? This determines whether a one-scenario comparison answers the real decision.

Until answered, recommend starting with known candidate places and explicitly judging only the morning ART scenario. These assumptions bound a draft, not final priorities. Noa hands design rationale to dot; ash supplies feasibility and evidence limits; rue chooses a focused, neutral test. Martijn sets scope and priorities.
