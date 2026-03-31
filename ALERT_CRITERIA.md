# Crisis Alert Criteria

The system sends alerts using the following crisis trigger rules and templates.

## 1. Earthquake Alerts

### When to send
- Earthquake event is **Cebu-specific** (location/details mention Cebu, or Cebu felt-intensity data exists).
- Earthquake magnitude is **2.5 or higher**.
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
- PAGASA heavy rainfall and tropical cyclone criteria/templates are implemented in `PAGASA/parser.py`.
- Email subject selection is handled in `AlertSystem.py`.
