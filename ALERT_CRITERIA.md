# Crisis Alert Criteria

The system sends alerts using the following crisis trigger rules and templates.

## 1. Earthquake Alerts

### When to send
- Earthquake event is **Cebu-specific** (location/details mention Cebu, or Cebu felt-intensity data exists).
- Earthquake magnitude is **greater than 4.0**.
- Depth and other earthquake parameters are **not used** for alert triggering.

### Template fields
- Date & Time
- Magnitude
- Epicenter Location
- Intensity Felt in Cebu: Intensity __
- Safety Precautions

## 2. Heavy Rainfall Warning

### When to send
- PAGASA issues **any Heavy Rainfall Warning level** (e.g., Yellow, Orange, Red, or unspecified on page).
- Affected area includes **Cebu City** or nearby cities:
  - Mandaue
  - Lapu-Lapu
  - Talisay
  - Consolacion
  - Liloan
  - Minglanilla

### Template fields
- Warning Level: PAGASA-provided level (all levels accepted)
- Affected Area: Cebu City / Nearby Cities
- Issued By: PAGASA
- Safety Precautions

## 3. Thunderstorm Warning

### When to send
- PAGASA page contains **Thunderstorm Warning** or **Thunderstorm Advisory**.
- Affected area includes **Cebu City** or nearby cities.

### Template fields
- Warning Level (if present)
- Affected Area: Cebu City / Nearby Cities
- Issued By: PAGASA
- Safety Precautions

## 4. Tropical Depression / Typhoon Alerts

### When to send
- Cebu City or nearby cities are within forecast track.
- Signal is raised, or heavy rains are expected in Cebu.

### Template fields
- Weather System: Tropical Depression / Tropical Storm / Typhoon - Name
- Current Location: Location per PAGASA
- Signal Level (if any): TCWS #
- Areas Affected: Cebu City / Nearby Cities
- Date & Time: as of Date, Time
- Safety Precautions

## Implementation Notes

- Earthquake criteria and template are implemented in `PHIVOLCS/parser.py`.
- Earthquake delivery uses a pending queue so missed Cebu earthquakes after temporary failures are retried.
- Pending earthquake queue is trimmed to the **latest 5 qualifying events** before sending (configurable via `MAX_PENDING_QUAKE_EVENTS`, default `5`).
- Earthquake IDs are marked seen only after successful email delivery to avoid missed reports.
- PAGASA heavy rainfall and tropical cyclone criteria/templates are implemented in `PAGASA/parser.py`.
- Email subject selection is handled in `AlertSystem.py`.

## Planned Enhancement: Secondary Confirmation Source

- Candidate reference: `https://github.com/mltpascual/BantayPilipinas`.
- External source: USGS Earthquake Hazards Program (GeoJSON feed).
- Provider: U.S. Geological Survey (USGS).
- Endpoint: `https://earthquake.usgs.gov/fdsnws/event/1/query`.
- Format: `GeoJSON`.
- Parameters for PH-region filtering:
  - `format=geojson`
  - `minlatitude=4.5`
  - `maxlatitude=21.5`
  - `minlongitude=116`
  - `maxlongitude=127`
  - `limit=30`
  - `orderby=time`
- Refresh cadence: approximately every 2 minutes.
- Key returned fields to use for confirmation: magnitude, depth, place/location text, tsunami flag, significance score, and event time.
- Documentation: USGS Earthquake Catalog API (`https://earthquake.usgs.gov/fdsnws/event/1/`).
- License: Public domain (U.S. Government work).
- Proposed use in this project: optional **secondary confirmation** only, not primary trigger replacement.
- Suggested behavior:
  - Keep PHIVOLCS as primary source for local alerting.
  - If USGS also reports a matching event (time + location proximity + similar magnitude), add a "confirmed by USGS" note to logs/email.
  - Do not block PHIVOLCS alert dispatch if USGS is temporarily unavailable.
