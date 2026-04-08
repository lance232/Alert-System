# Change Specifiers Guide

This guide shows exactly where to change behavior and what to update when requirements change.

## 1) Change Earthquake Magnitude Threshold (Example: 3.5 or 4.5)

Primary code location:
- `PHIVOLCS/parser.py`
- Constant: `MIN_CEBU_ALERT_MAGNITUDE`

Current value:
- `MIN_CEBU_ALERT_MAGNITUDE = 4.0`

How to change:
1. Open `PHIVOLCS/parser.py`.
2. Update `MIN_CEBU_ALERT_MAGNITUDE` to your target.
   - Example for 3.5: `MIN_CEBU_ALERT_MAGNITUDE = 3.5`
   - Example for 4.5: `MIN_CEBU_ALERT_MAGNITUDE = 4.5`
3. Confirm criteria logic still reads `magnitude > MIN_CEBU_ALERT_MAGNITUDE`.

Important note:
- Logic is strict greater-than (`>`), not greater-than-or-equal (`>=`).
- If you want inclusive behavior, change `>` to `>=` in `meetsAlertCriteria()`.

Related references:
- `PHIVOLCS/parser.py` (`MIN_CEBU_ALERT_MAGNITUDE`, `meetsAlertCriteria`)

## 2) Change Queue Size For Pending Quakes

Config location:
- `.env` variable: `MAX_PENDING_QUAKE_EVENTS`

Code reader:
- `AlertSystem.py` reads this with safe parsing.

How to change:
1. In `.env`, set `MAX_PENDING_QUAKE_EVENTS=<number>`.
2. Restart `AlertSystem.py`.

Examples:
- Keep latest 5: `MAX_PENDING_QUAKE_EVENTS=5`
- Keep latest 10: `MAX_PENDING_QUAKE_EVENTS=10`
- Disable queue cap: `MAX_PENDING_QUAKE_EVENTS=0`

## 3) Change Earthquake Age Window

Config location:
- `.env` variable: `MAX_EVENT_AGE_MIN`

Behavior:
- `0` means unlimited age.
- Positive value means only events within last N minutes are considered.

## 4) Change Cold Start Behavior (On Restart)

Config location:
- `.env` variable: `COLD_START_SUPPRESS`

Behavior:
- `1`: suppress old events on first run.
- `0`: allow existing feed events to be evaluated on startup.

Use case:
- For testing alert flow on restart, temporarily set `COLD_START_SUPPRESS=0`.

## 5) Change USGS Confirmation Behavior

Enable/disable:
- `.env`: `USGS_CONFIRMATION_ENABLED` (`1` or `0`)

Match tuning:
- `.env`: `USGS_MATCH_TIME_WINDOW_MIN`
- `.env`: `USGS_MATCH_MAX_DISTANCE_KM`
- `.env`: `USGS_MATCH_MAG_TOLERANCE`

USGS source + matcher code:
- `PHIVOLCS/parser.py`
- Functions: `FetchUSGSEarthquakes`, `findUSGSMatch`, `annotateUSGSConfirmation`

When to edit code vs env:
- Use `.env` for match strictness tuning.
- Edit code only if you need different matching formula or different USGS query parameters.

## 6) Change PAGASA Heavy Rainfall Trigger Rules

Current parser behavior:
- Heavy Rainfall Warning is parsed from HRW section only.
- Explicit no-warning text is ignored.

Code locations:
- `PAGASA/parser.py`
- Functions: `parse_visprsd_cebu_advisories`, `extractSection`, `hasNoHeavyRainfallWarning`

Common change examples:
1. Add more no-warning phrases:
   - Update `negative_patterns` inside `hasNoHeavyRainfallWarning()`.
2. Change section boundary parsing:
   - Update `extractSection()` call patterns in `parse_visprsd_cebu_advisories()`.
3. Change Cebu area matching terms:
   - Update `TARGET_CEBU_AREAS` regex patterns.

## 7) Change Poll Speed / Refresh Controls

Config in `.env`:
- `POLL_INTERVAL_SEC`
- `SMART_REFRESH`
- `STALE_MAX_SEC`
- `NO_NEW_CYCLES_BEFORE_REFRESH`
- `MIN_REFRESH_GAP_SEC`

Rule of thumb:
- Lower interval means faster detection but more requests.
- Keep smart refresh enabled unless debugging.

## 8) State File Handling (Seen/Queue)

State file path:
- `.env`: `STATE_FILE`
- Default: `state_phivolcs_pagasa.json`

What state controls:
- Seen quake IDs
- Pending quake queue
- Seen PAGASA advisories
- Last alerted timestamp

Testing reset (fresh behavior):
- Delete the state file, then restart system.

## 9) Safe Parsing Notes

`AlertSystem.py` uses safe env parsing helpers:
- `envBool()`
- `envInt()`
- `envFloat()`

If invalid values are set in `.env`, defaults are used and startup continues.

## 10) Change Checklist (Quick)

1. Update `.env` first when possible.
2. If code change is required, update the specific function/constant above.
3. Restart Node API (if PHIVOLCS local API changes are relevant).
4. Restart `AlertSystem.py`.
5. Check startup logs for active config.
6. Validate with one controlled test event or reset state file.

## 11) Advanced: Recipient Routing / Per-Alert Recipients

Current behavior:
- All alert types use one recipient list from `.env`:
  - `EMAIL_RECIPIENTS`

Where to update:
- `AlertSystem.py`
- Function: `sendAlertEmail()`

Suggested enhancement pattern:
1. Add new `.env` variables:
   - `EMAIL_RECIPIENTS_EARTHQUAKE`
   - `EMAIL_RECIPIENTS_WEATHER`
   - Keep `EMAIL_RECIPIENTS` as fallback.
2. In `sendAlertEmail()`, choose recipients by payload type:
   - Earthquake payload uses earthquake list.
   - PAGASA payload uses weather list.
3. If type-specific list is empty, fallback to `EMAIL_RECIPIENTS`.

Implementation specifier:
- Update recipient selection block before calling `sendEmail()`.
- Keep existing split logic: `[r.strip() for r in csv.split(",") if r.strip()]`.

## 12) Advanced: Email Subject/Body Customization Matrix

Current subject logic:
- `AlertSystem.py` → `sendAlertEmail()`
- Subject selected by advisory type set:
  - `HEAVY RAINFALL WARNING`
  - `THUNDERSTORM WARNING`
  - `TROPICAL DEPRESSION / TYPHOON ALERTS`
  - `CRISIS WEATHER ALERTS`

Current body templates:
- Earthquake email HTML: `PHIVOLCS/parser.py` → `formatEarthquakeEmail()`
- PAGASA email HTML: `PAGASA/parser.py` → `formatPagasaEmail()`

What to change for common requests:
1. Add severity in earthquake subject:
   - Edit subject assignment inside `sendAlertEmail()`.
   - Example: include magnitude and location.
2. Add/remove fields in earthquake email body:
   - Edit `formatEarthquakeEmail()` in `PHIVOLCS/parser.py`.
3. Add/remove fields in weather email body:
   - Edit `formatPagasaEmail()` in `PAGASA/parser.py`.
4. Change console output format to match email:
   - Earthquake: `formatEarthquakeConsole()` in `PHIVOLCS/parser.py`
   - Weather: `formatPagasaConsole()` in `PAGASA/parser.py`

Low-risk customization approach:
1. Keep existing function names and return types unchanged.
2. Update only string/template blocks.
3. Test with one earthquake path and one weather advisory path.
