# Alert-System
Automated alert notification system that monitors external hazard data (e.g., PAGASA and PHIVOLCS) and delivers real-time alerts via Outlook and Microsoft Teams

For quick maintenance updates (thresholds, queue, USGS matching, PAGASA rules), see `CHANGE_SPECIFIERS.md`.

## Recent Earthquake Alert Updates

- Cebu-only earthquake alerts now trigger at **magnitude > 4.0**.
- On each cycle, queued unsent earthquake events are trimmed to the **latest 5 qualifying events** to avoid old-event flood after restart.
- Queue size is configurable through `MAX_PENDING_QUAKE_EVENTS` in `.env` (default: `5`).

## Secondary Data Confirmation (Planned)

- Candidate reference repository: https://github.com/mltpascual/BantayPilipinas
- Source details from that implementation:
	- Provider: U.S. Geological Survey (USGS)
	- Endpoint: https://earthquake.usgs.gov/fdsnws/event/1/query
	- Format: GeoJSON
	- PH bounds: latitude 4.5 to 21.5, longitude 116 to 127
	- Query parameters: format=geojson, minlatitude=4.5, maxlatitude=21.5, minlongitude=116, maxlongitude=127, limit=30, orderby=time
	- Refresh cadence: ~2 minutes
	- License: Public domain (U.S. Government work)
- Planned approach:
	- Keep PHIVOLCS as the primary trigger source.
	- Use USGS as optional confirmation metadata for matched events.
	- Keep alert sending non-blocking if USGS data is unavailable.
