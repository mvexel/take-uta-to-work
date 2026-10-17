# User feedback

Owner: dedicated user-testing and feedback specialist. Parent coordinates Martijn's verified personal Slack DM; the specialist does not message Slack independently. No reminders or fixed schedule. Feature work waits for Martijn's feedback and prioritization.

## Active round UT-01 — one familiar transit origin

State: sent by dot to Martijn's personal Slack DM on 2026-10-17 at 21:38:43 UTC; reference `slack:D0CA2HRA4GJ::1792273123.770189`. First response received from Martijn via dot; evidence and proposed findings below. Initial task fulfilled; Ash has reproduced a qualifying TRAX alternative omitted from the combined response. The earlier bounded patch proposal is deferred pending longer-term product direction, superseding the approval request. Noa is drafting docs/product-vision.md; no further UI retest or comfort question is scheduled. No repeat request. This replaces the broad two-or-three-location review request. Allow about three minutes, stop at the first obstacle, and do not coach through it before recording what happened.

Prompt sent by the parent:

> Let's make the map review a three-minute task. On your Mac, open http://127.0.0.1:8002. With Bus + TRAX and at most 1 change, use the map to assess one familiar place as a possible home for reaching ART on Tuesday Oct 20, arriving 10:45–11:00 a.m. in at most 30 minutes door-to-door. Stop when you have an answer or get stuck. Which place did you try, and what did you do? What do you think the result says about that commute, and what on the screen led you to that conclusion?

This is the proposed test date, not a newly confirmed travel date. A nearby public landmark or intersection is sufficient; no home address is needed. If Martijn opens the loopback URL on a phone, direct him to the same Mac; this is a local-only app.

## How we follow through

For each reply, record the attempted place, mode/change cap, relevant visible result and steps. Separate directly observed actions, participant-reported actions, expectations, exact quotes, and our interpretation; leave missing evidence unknown. Slack descriptions are self-report unless we actually observe the action. Ask at most one or two neutral follow-ups about the first obstacle or decision (for example, “What did you expect to happen there?”), then return a concise finding and proposed priority to the parent. Do not automatically send a second test.

Turn a supported finding into a short issue here: ID/title; evidence and source; reproducible steps/settings/location; actual versus expected behavior; impact; proposed priority (P1 prevents or misleads the commute decision, P2 adds friction, P3 polish); acceptance checks. Keep hypotheses marked as such and assign final priority to Martijn. The technical lead owns implementation, with independent routing review when applicable. After a chosen fix, offer one focused retest and record its outcome before closing the issue. One user's feedback is qualitative evidence, not broad usability validation.

## UT-01 evidence — preparation only, 2026-10-17

Specialist observation in Firefox on this Mac, fresh app tab: default Bus + TRAX / 1 change; 50 samples, 4 qualifying, 36 no qualifying returned, 5 unknown, 0 errors, 5 not evaluated. The map showed sparse streets, ART label and sample dots; sample selector used grid IDs. Selecting grid-3-4 (40.766000, -111.884000) displayed a qualifying 26m39s journey, departure 10:25:28, arrival 10:52:07 Denver, zero changes; walk 13m58s, wait 0m0s, bus 220 ride 12m41s, then walk from Stadium to ART. These are bounded computed results, not field observations or exhaustive coverage.

Hypothesis for the first test: identifying a familiar place and interpreting the result may need attention. This has not been established by participant behavior. We deliberately test those steps before asking Martijn to compare filters. Bicycle calibration is incomplete and reliability collection is backlog; neither is validated by this test.

## UT-01 first participant response — 2026-10-17

Source: Martijn's personal Slack DM, workspace `T03L5BRH0`, conversation `D0CA2HRA4GJ`, thread `1792273761.604929`, forwarded by dot. This is participant self-report, not a directly observed session. No exact click coordinate, screenshot, selected option IDs, measured elapsed interaction time or explicit filter confirmation accompanied the reply. The requested scenario was Bus + TRAX / at most 1 change, proposed Oct 20 arrival 10:45–11:00, <=30 minutes door-to-door; do not assume every setting was verified.

### Verbatim reply

> I tried 300 E 300 S (there's a building there we are considering.) Noticing that there is not a TRAX option even though the stop is  right there. TRAX is much more comfortable. But I guess we do not weigh that.
>
> I clicked on the intersection and it gave me a route right away. It took me a while to figure out that you could select other trip options from the dropdown. At frst I thought the second option was a TRAX option (the map does not make a distinction) but upon further inspection it was a bus that follows the same route as TRAX for the most part.

### Evidence separated from interpretation

- Directly observed participant behavior: none. The earlier specialist preparation is separate and does not reproduce this session.
- Participant-reported behavior: clicked 300 E / 300 S; received a route “right away”; took time to discover alternate trips in the dropdown; initially interpreted the second option as TRAX, then identified it as a bus after further inspection.
- Reported expectation/preference: expected a TRAX option because a stop is nearby; considers TRAX more comfortable. The participant reply alone does not establish trip feasibility; Ash subsequently verified a qualifying TRAX journey as recorded below. The comfort statement is a preference, not a request for a numeric weighting, new ranking model or relaxed constraints.
- Interpretation: the basic click-to-route action worked for this participant. Alternative-trip discovery caused friction; mode presentation permitted an initial mistaken reading. Ash subsequently reproduced a qualifying TRAX alternative omitted from the combined OTP response. App filtering and the 20-option cap were ruled out in that diagnosis; exact internal cause remains untraced. We have no evidence yet that Martijn reached a final “could I live here?” decision.
- Scope: one qualitative response. No broad usability, exhaustive coverage, optimality, bike calibration or reliability validation follows from it.

## Proposed findings — not an approved implementation cycle

The patch proposal and its remedies are deferred pending product direction, not awaiting approval. Findings remain evidence for Noa's product/design work; the priorities and acceptance checks below are proposals for reconsideration, not a committed backlog or current test plan. No further UI retest or comfort clarification proceeds now. Final priority belongs to Martijn with dot coordinating. These are evidence-backed reports awaiting technical reproduction where indicated; none is a claim that a fix has been implemented or accepted.

### UT-01-1 — Preserve the qualifying TRAX alternative omitted by combined search

Proposed **P1**: a qualifying preferred-mode option is absent from the combined result, affecting the commute comparison. Owner: Ash for technical work; rue for user-facing evidence and retest. Status: omission confirmed by Ash's reproduction, forwarded by dot on 2026-10-17; proposed patch deferred pending product direction, not implemented. This is technical evidence reported by Ash, not a new participant observation or an independent reproduction by rue.

Reproduction/evidence: at `40.7628276,-111.8825088` (300 E / 300 S), proposed Oct 20 / 10:45–11:00 / <=30 minutes / at most 1 change, the raw combined OTP response omits a qualifying Red Line 703 journey returned by TRAX-only search. Ash also reproduced omission at all four intersection corners; corner coordinates are not included in this handoff, so refer to Ash's underlying evidence rather than inventing them. Martijn's exact original click remains unknown.

The verified TRAX-only option leaves 10:23:08 and arrives at ART 10:49:47 Denver, elapsed 26m39s, walking 17m39s, zero vehicle changes. Walk 7m52s to Library; train 10:31–10:40 to Stadium; walk 9m47s to ART. GTFS trip `5929920`, stops `18378` / `18383`, matches. Comparison options reported by Ash: bus 455 totals 22m40s; bus 220 totals 25m59s. These are schedule results for the reproduced origin/scenario, not guarantees, exhaustive alternatives or measurements of comfort.

Confirmed boundary: omission occurs in the combined raw OTP response, not the app's subsequent filtering or its 20-option cap. Dominance/search pruning is plausible, but the exact OTP internal decision is untraced; do not present that hypothesis as established cause. No comfort preference is configured.

Actual: a qualifying TRAX journey is available through TRAX-only search but absent from combined search. Expected: the combined mode lets Martijn compare this qualifying TRAX alternative with the returned buses rather than hiding it. Faster buses do not invalidate the rail journey under the selected constraints.

Proposed bounded remedy from Ash: query combined and TRAX-only, merge/deduplicate returned itineraries, then apply existing constraint and leg checks. This is a retained technical option, deferred pending product direction; it is not awaiting patch approval, a promise of exhaustive coverage or a new comfort-ranking algorithm.

Proposed acceptance checks after authorization: the exact reproduced coordinate/scenario exposes the verified Red Line 703 journey alongside valid bus alternatives; record and check all four corner cases from Ash's evidence. Duplicate itineraries appear once. Existing arrival-window, <=30-minute, route-allowlist, vehicle-change and returned-leg checks still apply; incomplete supplemental searches retain honest uncertainty rather than suggesting complete enumeration. Add a regression reproducing combined omission with a qualifying TRAX-only return, verify live output and obtain independent routing review. Only after later product direction and authorization would rue offer a focused comparison retest through dot; technical checks alone do not establish participant acceptance. Finding remains open until the approved remedy and checks are completed.

### UT-01-2 — Distinguish bus from TRAX when choosing and viewing trips

Proposed **P1**: a participant initially classified a bus trip as TRAX, affecting the interpretation of a preferred-mode commute. Owner after prioritization: Ash; rue supplies focused retest. Status: reported usability issue; technical reproduction pending.

Reproduction: same origin/scenario; inspect the second returned option if reproducible (order/identity may differ), compare selector text, route map and leg details. Record which option and boarding modes are actually returned; do not infer mode from geometry.

Actual: Martijn mistook the second option for TRAX and corrected himself only after further inspection. Expected: determine whether each alternative uses bus, TRAX or both without guessing from the route's shape.

Proposed acceptance checks: alternative summaries identify actual boarding mode(s) and route/line names; the selected itinerary and map have an explicit, consistent mode distinction that does not rely on color alone. Walking remains distinguishable, and mixed itineraries identify both modes. In a focused retest, Martijn can correctly identify the alternatives' modes from the presented information before inspecting detailed legs. These are outcome checks, not a prescribed visual design.

### UT-01-3 — Make alternate-trip availability discoverable

Proposed **P2**: slows comparison, but Martijn eventually found the dropdown. Owner after prioritization: Ash; rue supplies retest. Status: reported usability issue; technical reproduction pending.

Reproduction: same origin/scenario with multiple returned alternatives; after the first result, inspect how the app signals that more trips exist and how to choose one.

Actual: “It took me a while” to discover the trip-options dropdown; no measured duration. Expected: recognize that multiple alternatives are available and choose another without coaching.

Proposed acceptance checks: after a multi-option result, the interface visibly communicates the available alternatives and their selection control; choosing an alternative updates its map and details consistently. With one result it does not imply hidden alternatives. In a focused retest, Martijn discovers and selects another trip unaided; record behavior rather than claiming general discoverability from that one retest.

## Possible later comfort clarification — on hold

Not sent. The earlier patch approval request in Slack thread `1792273761.604929` is superseded by Martijn's request for a longer-term product vision. No comfort question or further UI retest now; retain this wording only as a possible future research prompt, subject to product direction:

> When both bus and TRAX meet your commute limits, how would you like the app to help you choose between them?

Purpose: clarify how Martijn wants the expressed comfort preference supported without assuming ranking, comfort weights or automatic selection. No new task, repeated nudge or implementation authorization is implied.

## Product direction — supersedes the patch proposal

Latest user direction, forwarded by dot:

> Well I would like a longer term vision of what the product will look like rather than bolting on features on this POC. Perhaps a design lead or product owner is what we need.

Noa joins as product/design lead, drafting docs/product-vision.md (task `01a14bdc-5d28-72ab-abb3-1bb9485ad035`). The bounded patch proposal is deferred pending that direction, not awaiting approval. Preserve UT-01 evidence and candidate remedies for product synthesis. No additional UI retest, comfort question or repeated patch request now.

### Insight brief for Noa

**Evidence:** Martijn tested a real candidate building at 300 E / 300 S, so this session concerned a concrete housing decision. He reported immediate click-to-route success, difficulty discovering alternatives and initial bus/TRAX confusion. He explicitly prefers TRAX's comfort. Ash verified a qualifying 26m39s Red Line journey omitted from combined search, alongside 22m40s and 25m59s bus alternatives. All three satisfy the duration threshold at the reproduced origin; speed alone does not explain Martijn's stated preference. The TRAX journey includes 17m39s walking; we do not know how Martijn values that walking. Martijn subsequently asked for a longer-term product vision rather than successive POC additions.

**Interpretation to consider:** A useful housing answer may need to support an informed comparison of feasible commute choices, not only return a passing journey. Mode identity and meaningful alternative visibility matter to this participant's interpretation. Honest descriptions of sampled coverage and incomplete alternatives matter because an omitted option could change how a candidate home appears. These are implications from one session, not validated requirements for every user.

**Hypotheses / unknowns:** Whether the primary journey should begin with a known building or neighborhood discovery; whether Martijn wants to compare several homes; how he trades comfort against time, walking or transfers; whether preferences should influence ordering, filtering or simply comparison; what evidence makes a home worth shortlisting. No comfort weights, longer duration tolerance, reliability requirement, ranking algorithm or final housing choice were established. Keep these as product questions, not assumed features; no new questions are being sent now.

**Design input, not a prescribed solution:** Explore how a person moves from location to credible commute options to a housing decision, with clear modes, visible tradeoffs and uncertainty. Reconsider the retained patch ideas against that end-to-end vision rather than treating three findings as three mandatory UI additions. This evidence is one participant's qualitative account plus Ash's bounded technical reproduction, not broad usability validation or field travel performance.

## Current handoff

Rue updated only docs/feedback.md for the new direction. Noa owns product-vision drafting and team-index/project links; Ash owns status/board reconciliation; dot coordinates product decisions with Martijn. Existing findings remain open and candidate remedies deferred. No patch approval request, UI retest or comfort clarification is currently actionable. Original participant quotes and technical evidence attribution are preserved.
