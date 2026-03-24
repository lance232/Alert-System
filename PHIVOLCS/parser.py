import re
import time
import requests
from html import escape
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime, timezone


def parseDT(text: str) -> Optional[datetime]:
    if not text:
        return None
    try:
        from dateutil import parser as dtparse
        return dtparse.parse(text, fuzzy=True)
    except Exception:
        return None


def normNum(Numbers: str, decimals: int = 3) -> str:
    try:
        return f"{float(str(Numbers).strip()):.{decimals}f}"
    except Exception:
        return str(Numbers).strip()


def WithRefreshPath(apiURL: str) -> str:
    Base = apiURL.rstrip("/")
    if re.search(r"/api/earthquakes/?$", Base):
        return Base + "/refresh"
    if Base.endswith("/refresh"):
        return Base
    return Base + "/refresh"


def meetsAlertCriteria(earthquake: Dict[str, Any]) -> bool:
    magnitude_str = str(earthquake.get('magnitude', '0')).strip()
    try:
        magnitude = float(magnitude_str)
        if magnitude <= 4.0:
            return False
    except ValueError:
        return False
    
    location = str(earthquake.get('location', '')).lower()
    visayas_keywords = [
        'cebu', 'bohol', 'negros', 'leyte', 'samar', 'panay',
        'iloilo', 'bacolod', 'tacloban', 'dumaguete', 'tagbilaran',
        'ormoc', 'calbayog', 'catbalogan', 'roxas', 'kalibo',
        'boracay', 'siquijor', 'biliran', 'eastern samar', 'western samar',
        'northern samar', 'southern leyte', 'negros oriental', 'negros occidental',
        'eastern visayas', 'central visayas', 'western visayas', 'visayas'
    ]
    
    if not any(keyword in location for keyword in visayas_keywords):
        return False
    
    depth_str = str(earthquake.get('depth', '')).lower()
    depth_match = re.search(r'(\d+(?:\.\d+)?)', depth_str)
    if depth_match:
        try:
            depth_km = float(depth_match.group(1))
            if depth_km < 1 or depth_km > 10:
                return False
        except ValueError:
            return False
    else:
        return False

    return True


def FetchPhivolcs(
    apiURL: str, 
    timeout: Tuple[float, float] = (10, 30), 
    force_refresh: bool = False
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    url = WithRefreshPath(apiURL) if force_refresh else apiURL
    Read = requests.get(url, timeout=timeout)
    Read.raise_for_status()
    Object = Read.json()
   
    if not Object.get("success", True) and "data" not in Object:
        raise RuntimeError(Object.get("error") or "PHIVOLCS API returned success=false")

    Raw = Object.get("data", []) or []
    events: List[Dict[str, Any]] = []
    
    for Item in Raw:
        dateTime = str(Item.get("dateTime", "")).strip()
        Latitude = str(Item.get("latitude", "")).strip()
        Longitude = str(Item.get("longitude", "")).strip()
        Magnitude = str(Item.get("magnitude", "")).strip()
        Depth = str(Item.get("depth", "")).strip()
        Location = str(Item.get("location", "")).strip()

        eventDate = parseDT(dateTime)
        isoKey = eventDate.isoformat() if eventDate else dateTime
        latitudeKey = normNum(Latitude, 3)
        longitudeKey = normNum(Longitude, 3)
        earthquakeID = f"{isoKey}|{latitudeKey}|{longitudeKey}"

        events.append({
            "source": "PHIVOLCS",
            "id": earthquakeID,
            "time": dateTime or "n/a",
            "latitude": Latitude or "n/a",
            "longitude": Longitude or "n/a",
            "depth": Depth or "n/a",
            "magnitude": Magnitude or "n/a",
            "location": Location or "n/a",
            "_dt": eventDate,
        })

    events.sort(key=lambda x: (x["_dt"] or x["time"]), reverse=True)

    meta = {
        "cached": Object.get("cached"),
        "lastUpdated": Object.get("lastUpdated"),
        "count": Object.get("count"),
    }
    
    return events, meta


def formatEarthquakeEmail(earthquake: Dict[str, Any], alert_time: str) -> str:
    def safe_html(value: Any) -> str:
        return escape(str(value), quote=True).replace("\n", "<br>")

    event_time = safe_html(earthquake.get('time', 'n/a'))
    magnitude = safe_html(earthquake.get('magnitude', 'n/a'))
    depth = safe_html(earthquake.get('depth', 'n/a'))
    location = safe_html(earthquake.get('location', 'n/a'))
    latitude = safe_html(earthquake.get('latitude', 'n/a'))
    longitude = safe_html(earthquake.get('longitude', 'n/a'))
    safe_alert_time = safe_html(alert_time)

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #d32f2f; color: white; padding: 15px; border-radius: 5px; }}
            .content {{ background-color: #f5f5f5; padding: 20px; margin-top: 10px; border-radius: 5px; }}
            .info-row {{ margin: 10px 0; padding: 8px; background-color: white; border-left: 4px solid #d32f2f; }}
            .label {{ font-weight: bold; color: #d32f2f; }}
            .footer {{ margin-top: 20px; font-size: 0.9em; color: #666; border-top: 1px solid #ddd; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>🚨 EARTHQUAKE ALERT - PHIVOLCS</h2>
            </div>
            <div class="content">
                <div class="info-row">
                    <span class="label">Time:</span> {event_time}
                </div>
                <div class="info-row">
                    <span class="label">Magnitude:</span> {magnitude}
                </div>
                <div class="info-row">
                    <span class="label">Depth:</span> {depth}
                </div>
                <div class="info-row">
                    <span class="label">Location:</span> {location}
                </div>
                <div class="info-row">
                    <span class="label">Coordinates:</span> Lat {latitude}, Lon {longitude}
                </div>
            </div>
            <div class="footer">
                <p><strong>Source:</strong> PHIVOLCS (Philippine Institute of Volcanology and Seismology)</p>
                <p><strong>Alert Time:</strong> {safe_alert_time}</p>
                <p><em>This is an automated alert from the NCR Atleos Alert System.</em></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def formatEarthquakeConsole(latest_earthquake: Optional[Dict[str, Any]]) -> str:
    lines = []
    lines.append("Earthquake (PHIVOLCS)")
    lines.append("-" * 52)
    if latest_earthquake:
        lines.append(
            f"ID        : {latest_earthquake['id']}\n"
            f"Time      : {latest_earthquake.get('time', 'n/a')}\n"
            f"Magnitude : {latest_earthquake.get('magnitude', 'n/a')}\n"
            f"Depth     : {latest_earthquake.get('depth', 'n/a')}\n"
            f"Lat, Lon  : {latest_earthquake.get('latitude','n/a')}, {latest_earthquake.get('longitude','n/a')}\n"
            f"Location  : {latest_earthquake.get('location','n/a')}\n"
        )
    else:
        lines.append("No new earthquake.")
    return "\n".join(lines)


def isNew(event: Dict[str, Any], watermark: Optional[datetime]) -> bool:
    if watermark is None:
        return True
    event_dt = event.get("_dt")
    if not event_dt:
        return False
    return event_dt > watermark


def withinMaxAge(event: Dict[str, Any], max_minutes: int) -> bool:
    if max_minutes <= 0:
        return True
    event_dt = event.get("_dt")
    if not event_dt:
        return False
    age_seconds = (datetime.now(timezone.utc) - event_dt.astimezone(timezone.utc)).total_seconds()
    return age_seconds <= max_minutes * 60


def process_earthquakes(
    api_url: str,
    seen_quake_ids: set,
    last_alerted_dt: Optional[datetime],
    last_top_id: str,
    no_new_cycles: int,
    last_refresh_mono: float,
    cold_start: bool,
    max_event_age_min: int,
    smart_refresh: bool,
    stale_max_sec: int,
    no_new_cycles_before_refresh: int,
    min_refresh_gap_sec: int
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any], set, Optional[datetime], str, int, float, bool]:
    try:
        earthquakes, meta = FetchPhivolcs(api_url, timeout=(10, 30), force_refresh=False)
        current_top_id = earthquakes[0]["id"] if earthquakes else last_top_id
        
        if cold_start and earthquakes and earthquakes[0].get("_dt"):
            last_alerted_dt = earthquakes[0]["_dt"]
            cold_start = False
        
        new_earthquakes: List[Dict[str, Any]] = []
        for quake in earthquakes:
            earthquake_key = f"PHIVOLCS-{quake['id']}"
            if earthquake_key in seen_quake_ids:
                continue
            if not isNew(quake, last_alerted_dt):
                continue
            if not withinMaxAge(quake, max_event_age_min):
                continue
            if not meetsAlertCriteria(quake):
                continue
            new_earthquakes.append(quake)
            seen_quake_ids.add(earthquake_key)
        
        latest_earthquake = new_earthquakes[0] if new_earthquakes else None
        if latest_earthquake:
            no_new_cycles = 0
            if latest_earthquake.get("_dt"):
                last_alerted_dt = latest_earthquake["_dt"]
        else:
            no_new_cycles += 1
        
        if smart_refresh and (latest_earthquake is None):
            should_refresh = False
            now_mono = time.monotonic()
            
            last_updated_text = meta.get("lastUpdated")
            if last_updated_text:
                try:
                    from dateutil import parser as dtparse
                    last_updated_dt = dtparse.parse(last_updated_text)
                    age_sec = (datetime.now(timezone.utc) - last_updated_dt).total_seconds()
                    if bool(meta.get("cached")) and age_sec > stale_max_sec:
                        should_refresh = True
                except Exception:
                    pass
            
            if no_new_cycles >= no_new_cycles_before_refresh:
                should_refresh = True
            
            if current_top_id and current_top_id == last_top_id:
                should_refresh = True
            
            if should_refresh and (now_mono - last_refresh_mono < min_refresh_gap_sec):
                should_refresh = False
            
            if should_refresh:
                try:
                    earthquakes, meta = FetchPhivolcs(api_url, timeout=(10, 30), force_refresh=True)
                    last_refresh_mono = time.monotonic()
                    current_top_id = earthquakes[0]["id"] if earthquakes else current_top_id
                    
                    new_earthquakes = []
                    for quake in earthquakes:
                        earthquake_key = f"PHIVOLCS-{quake['id']}"
                        if earthquake_key in seen_quake_ids:
                            continue
                        if not isNew(quake, last_alerted_dt):
                            continue
                        if not withinMaxAge(quake, max_event_age_min):
                            continue
                        if not meetsAlertCriteria(quake):
                            continue
                        new_earthquakes.append(quake)
                        seen_quake_ids.add(earthquake_key)
                    
                    if new_earthquakes:
                        latest_earthquake = new_earthquakes[0]
                        no_new_cycles = 0
                        if latest_earthquake.get("_dt"):
                            last_alerted_dt = latest_earthquake["_dt"]
                except Exception:
                    pass
        
        return (
            latest_earthquake,
            meta,
            seen_quake_ids,
            last_alerted_dt,
            current_top_id,
            no_new_cycles,
            last_refresh_mono,
            cold_start
        )
        
    except Exception:
        return (
            None,
            {"cached": None, "lastUpdated": None, "count": None},
            seen_quake_ids,
            last_alerted_dt,
            last_top_id,
            no_new_cycles,
            last_refresh_mono,
            cold_start
        )
