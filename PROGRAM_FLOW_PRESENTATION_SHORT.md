# Program Flow Presentation (Short)

## Slide 1 - What The System Does
- Monitors PHIVOLCS earthquakes and PAGASA advisories.
- Filters for Cebu relevance and alert criteria.
- Sends email alerts and prevents duplicate sends.
- Saves runtime state for restart-safe behavior.

Code anchors:
- [main loop start](AlertSystem.py#L253)
- [state load](AlertSystem.py#L131)
- [state save](AlertSystem.py#L149)

## Slide 2 - Earthquake Decision Flow
1. Fetch and filter earthquakes.
2. Keep only Cebu events above threshold.
3. Merge with pending queue and cap queue size.
4. Optionally annotate with USGS confirmation.

Code anchors:
- [threshold value](PHIVOLCS/parser.py#L23)
- [criteria function](PHIVOLCS/parser.py#L180)
- [earthquake processing](PHIVOLCS/parser.py#L582)
- [queue merge and cap](AlertSystem.py#L318)
- [USGS annotation call](AlertSystem.py#L344)

## Slide 3 - PAGASA Decision Flow
1. Fetch PRSD and TC bulletin pages.
2. Parse Cebu advisories only.
3. Block HRW false positives using no-warning guards.
4. Deduplicate advisory keys before sending.

Code anchors:
- [advisory processor](PAGASA/parser.py#L481)
- [PRSD parser](PAGASA/parser.py#L206)
- [no-warning guard](PAGASA/parser.py#L57)
- [HRW section scoping](PAGASA/parser.py#L44)

## Slide 4 - Output And Retry Behavior
1. If pending quake exists, send quake email first.
2. On quake email failure, keep item in queue for next cycle.
3. If weather advisories exist, send PAGASA advisory email.

Code anchors:
- [send orchestrator](AlertSystem.py#L220)
- [quake send loop](AlertSystem.py#L365)
- [retry on failure](AlertSystem.py#L373)
- [weather send path](AlertSystem.py#L387)

## Slide 5 - Config Knobs You Can Explain
- Threshold and queue:
  - MIN_CEBU_ALERT_MAGNITUDE in PHIVOLCS parser
  - MAX_PENDING_QUAKE_EVENTS in env
- Restart behavior:
  - COLD_START_SUPPRESS
  - state file seen and pending entries
- USGS confirmation tuning:
  - USGS_CONFIRMATION_ENABLED
  - time window, distance, magnitude tolerance

Code anchors:
- [safe env parsing](AlertSystem.py#L30)
- [queue and USGS env reads](AlertSystem.py#L90)
- [state serialization for pending queue](AlertSystem.py#L172)

## Optional 60-second Demo Script
1. Start PHIVOLCS API.
2. Start AlertSystem.py.
3. Show startup config lines.
4. Show one cycle log with either quake or PAGASA path.
5. Show saved state file update.
