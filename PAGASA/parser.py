import re
import time
import requests
from html import escape
from bs4 import BeautifulSoup, FeatureNotFound
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


TARGET_CEBU_AREAS = [
    ("Cebu City", [r"\bcebu\s*city\b", r"\b#cebu\b", r"\bcebu\b"]),
    ("Mandaue", [r"\bmandaue\b"]),
    ("Lapu-Lapu", [r"\blapu\s*[- ]?lapu\b"]),
    ("Talisay", [r"\btalisay\b"]),
    ("Consolacion", [r"\bconsolacion\b"]),
    ("Liloan", [r"\bliloan\b"]),
    ("Minglanilla", [r"\bminglanilla\b"]),
]

CEBU_CITY_PATTERNS = [
    r"\bcebu\s*city\b",
    r"(?<!\w)#\s*cebu\b",
]


def parseDT(text: str) -> Optional[datetime]:
    if not text:
        return None
    try:
        from dateutil import parser as dtparse
        return dtparse.parse(text, fuzzy=True)
    except Exception:
        return None


def normalizeText(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def buildSoup(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except FeatureNotFound:
        # Fallback for environments where lxml is not installed.
        return BeautifulSoup(html, "html.parser")


def extractSnippet(text: str, pattern: str, window: int = 220) -> str:
    match = re.search(pattern, text, flags=re.I)
    if not match:
        return text[: max(0, min(len(text), window * 2))]
    start = max(0, match.start() - window)
    end = min(len(text), match.end() + window)
    return text[start:end].strip()


def extractSection(text: str, start_pattern: str, end_pattern: str) -> str:
    start_match = re.search(start_pattern, text, flags=re.I)
    if not start_match:
        return ""

    start = start_match.start()
    tail = text[start:]
    end_match = re.search(end_pattern, tail, flags=re.I)
    if not end_match:
        return tail.strip()
    return tail[:end_match.start()].strip()


def hasNoHeavyRainfallWarning(text: str) -> bool:
    negative_patterns = [
        r"\bthere\s+is\s+no\s+heavy\s+rainfall\s+warning\s+issued\b",
        r"\bno\s+heavy\s+rainfall\s+warning\b",
        r"\bheavy\s+rainfall\s+warning\s*[:\-]?\s*none\b",
    ]
    return any(re.search(pattern, text, flags=re.I) for pattern in negative_patterns)


def extractIssuedTimestamp(text: str) -> Optional[str]:
    candidates = [
        r"issued\s+at\s+(.{8,80}?)(?=\s+(?:thunderstorm|heavy\s+rainfall|special\s+forecast|tropical|within\s+\d+\s+hours|$)|[.;])",
        r"as\s+of\s+(.{8,80}?)(?=\s+(?:thunderstorm|heavy\s+rainfall|special\s+forecast|tropical|within\s+\d+\s+hours|$)|[.;])",
    ]
    for pattern in candidates:
        match = re.search(pattern, text, flags=re.I)
        if not match:
            continue
        captured = match.group(1).strip(" :-")
        parsed = parseDT(captured)
        if parsed:
            return parsed.isoformat()
        return captured
    return None


def extractAffectedCebuAreas(text: str) -> List[str]:
    found: List[str] = []
    for canonical, patterns in TARGET_CEBU_AREAS:
        for pattern in patterns:
            if re.search(pattern, text, flags=re.I):
                found.append(canonical)
                break

    unique = []
    seen = set()
    for area in found:
        if area in seen:
            continue
        seen.add(area)
        unique.append(area)
    return unique


def isCebuCityMentioned(text: str) -> bool:
    return any(re.search(pattern, text, flags=re.I) for pattern in CEBU_CITY_PATTERNS)


def extractSignalLevel(text: str) -> str:
    patterns = [
        r"\bTCWS\s*#?\s*(\d)\b",
        r"\bSignal\s*(?:No\.?\s*)?#?\s*(\d)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return f"TCWS #{match.group(1)}"
    return "None"


def extractWeatherSystem(text: str) -> str:
    match = re.search(
        r"\b(Tropical\s+Depression|Tropical\s+Storm|Typhoon)\s+([A-Z][A-Z0-9\-]+)?",
        text,
        flags=re.I,
    )
    if not match:
        return "Tropical Cyclone (name unavailable)"
    system_type = match.group(1).title()
    system_name = (match.group(2) or "").strip().upper()
    return f"{system_type} - {system_name}" if system_name else system_type


def extractCurrentLocation(text: str) -> str:
    patterns = [
        r"(?:located|estimated)\s+at\s+([^.;]{8,120})",
        r"center\s+of\s+the\s+eye\s+was\s+estimated\s+based\s+on\s+all\s+available\s+data\s+at\s+([^.;]{8,120})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return match.group(1).strip()
    return "Location per PAGASA"


def hasHeavyRainExpectation(text: str) -> bool:
    return bool(re.search(r"heavy\s+rains?\s+(?:expected|possible|likely)", text, flags=re.I))


def extractWarningLevel(text: str) -> str:
    match = re.search(r"\b(YELLOW|ORANGE|RED)\b", text, flags=re.I)
    if match:
        return match.group(1).upper()
    return "UNSPECIFIED"


def extractThunderstormOutlook(text: str) -> str:
    match = re.search(
        r"\bThunderstorm\s+is\s+(VERY\s+LIKELY|LIKELY|LESS\s+LIKELY)\s+to\s+develop\b",
        text,
        flags=re.I,
    )
    if match:
        return re.sub(r"\s+", " ", match.group(1).upper()).strip()
    return "UNSPECIFIED"


def extractThunderstormBulletin(text: str) -> Optional[Dict[str, Any]]:
    # Parse concrete thunderstorm bulletin entries (e.g., "Thunderstorm Watch #VISPRSD")
    # to avoid false positives from tab labels/navigation text.
    bulletin_pattern = re.compile(
        r"\bThunderstorm\s+(Information|Advisory|Watch|Warning)\s*#?\s*VISPRSD\b.*?"
        r"(?=\bThunderstorm\s+(?:Information|Advisory|Watch|Warning)\s*#?\s*VISPRSD\b|\bSpecial\s+Forecasts?\b|$)",
        flags=re.I,
    )

    priority = {
        "Warning": 4,
        "Advisory": 3,
        "Watch": 2,
        "Information": 1,
    }

    candidates: List[Tuple[int, float, int, Dict[str, Any]]] = []

    for idx, match in enumerate(bulletin_pattern.finditer(text)):
        bulletin_text = normalizeText(match.group(0))
        if not isCebuCityMentioned(bulletin_text):
            continue
        affected_areas = ["Cebu City"]

        outlook = extractThunderstormOutlook(bulletin_text)
        if outlook == "LESS LIKELY":
            continue

        subtype = match.group(1).title()
        issued = extractIssuedTimestamp(bulletin_text)
        issued_dt = parseDT(issued or "")
        issued_score = issued_dt.timestamp() if issued_dt else 0.0

        payload = {
            "subtype": subtype,
            "outlook": outlook,
            "affected_areas": affected_areas,
            "issued": issued,
            "raw": bulletin_text,
        }

        candidates.append((priority.get(subtype, 0), issued_score, -idx, payload))

    if not candidates:
        return None

    candidates.sort(reverse=True)
    return candidates[0][3]


def fetch_pagasa_visprsd(
    session: requests.Session,
    endpoints: List[str] = None
) -> str:
    if endpoints is None:
        endpoints = [
            "https://www.pagasa.dost.gov.ph/regional-forecast/visprsd",
        ]
    
    errors: List[str] = []
    for url in endpoints:
        try:
            Read = session.get(url, timeout=(10, 30))
            Read.raise_for_status()
            return Read.text
        except Exception as Exempted:
            errors.append(f"{url} -> {type(Exempted).__name__}: {Exempted}")
            time.sleep(2)
    
    raise RuntimeError("PAGASA fetch failed on all endpoints: " + " | ".join(errors))


def fetch_pagasa_tc_bulletin(
    session: requests.Session,
    endpoints: List[str] = None
) -> str:
    if endpoints is None:
        endpoints = [
            "https://www.pagasa.dost.gov.ph/tropical-cyclone/severe-weather-bulletin",
        ]
    
    errors: List[str] = []
    for url in endpoints:
        try:
            Read = session.get(url, timeout=(10, 30))
            Read.raise_for_status()
            return Read.text
        except Exception as Exempted:
            errors.append(f"{url} -> {type(Exempted).__name__}: {Exempted}")
            time.sleep(2)
    
    raise RuntimeError("PAGASA TC bulletin fetch failed on all endpoints: " + " | ".join(errors))


def parse_visprsd_cebu_advisories(html: str) -> List[Dict[str, Any]]:
    soup = buildSoup(html)
    page_text = normalizeText(soup.get_text(" ", strip=True))
    if not page_text:
        return []

    out: List[Dict[str, Any]] = []
    affected_areas = extractAffectedCebuAreas(page_text)

    hrw_section = extractSection(
        page_text,
        r"\bheavy\s+rainfall\s+warning\b",
        r"\b(?:thunderstorm|special\s+forecast|tropical\s+cyclone|weather\s+advisory|$)\b",
    )
    hrw_areas = ["Cebu City"] if hrw_section and isCebuCityMentioned(hrw_section) else []

    if hrw_section and (not hasNoHeavyRainfallWarning(hrw_section)) and hrw_areas:
        warning_level = extractWarningLevel(hrw_section)
        out.append({
            "source": "PAGASA",
            "type": "Heavy Rainfall Warning",
            "warning_level": warning_level,
            "affected_areas": hrw_areas,
            "issued": extractIssuedTimestamp(hrw_section) or extractIssuedTimestamp(page_text),
            "raw": hrw_section,
        })

    thunderstorm_bulletin = extractThunderstormBulletin(page_text)
    if thunderstorm_bulletin:
        thunderstorm_label = str(thunderstorm_bulletin.get("subtype", "Warning")).upper()
        out.append({
            "source": "PAGASA",
            "type": "Thunderstorm Warning",
            "warning_level": thunderstorm_label,
            "thunderstorm_outlook": thunderstorm_bulletin.get("outlook", "UNSPECIFIED"),
            "affected_areas": thunderstorm_bulletin.get("affected_areas", []),
            "issued": thunderstorm_bulletin.get("issued") or extractIssuedTimestamp(page_text),
            "raw": thunderstorm_bulletin.get("raw") or extractSnippet(page_text, r"\bthunderstorm\b"),
        })

    # Tropical cyclone alerts are sourced from the dedicated TC bulletin parser
    # to avoid false positives from generic PRSD page mentions.

    return out


def parse_tc_bulletin_cebu_alerts(html: str) -> List[Dict[str, Any]]:
    """Parse tropical cyclone bulletin for Cebu-area alerts"""
    soup = buildSoup(html)
    page_text = normalizeText(soup.get_text(" ", strip=True))
    if not page_text:
        return []

    out: List[Dict[str, Any]] = []
    
    # Check if there's an active TC
    if re.search(r"no\s+active\s+tropical\s+cyclone", page_text, flags=re.I):
        return []
    
    affected_areas = extractAffectedCebuAreas(page_text)
    
    # Look for TC mentions
    has_tropical_system = bool(
        re.search(r"\b(Tropical\s+Depression|Tropical\s+Storm|Typhoon)\b", page_text, flags=re.I)
    )
    
    if has_tropical_system and affected_areas:
        signal_level = extractSignalLevel(page_text)
        # Hardening: require explicit raised signal level for Cebu-area alerts.
        if signal_level != "None":
            out.append({
                "source": "PAGASA",
                "type": "Tropical Cyclone Alert",
                "weather_system": extractWeatherSystem(page_text),
                "current_location": extractCurrentLocation(page_text),
                "signal_level": signal_level,
                "affected_areas": affected_areas,
                "issued": extractIssuedTimestamp(page_text),
                "raw": extractSnippet(page_text, r"\b(Tropical\s+Depression|Tropical\s+Storm|Typhoon)\b"),
            })
    
    return out


def ExtractHRWStatus(html: str) -> str:
    soup = buildSoup(html)
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))

    noAdvisory = re.search(
        r"As of today, there is no Heavy Rainfall Warning Issued\.?",
        text,
        flags=re.I
    )
    if noAdvisory:
        return noAdvisory.group(0)

    Advisory = re.search(
        r"(Heavy Rainfall Warning.*?)(?=Thunderstorm|Special Forecast|As of today|$)",
        text,
        flags=re.I
    )
    if Advisory:
        snippet = Advisory.group(1).strip()
        return "HRW: " + (snippet[:140] + "..." if len(snippet) > 140 else snippet)

    return "HRW: (no status text found on PRSD page)"


def formatPagasaEmail(advisories: List[Dict[str, Any]], alert_time: str) -> str:
    def safe_html(value: Any) -> str:
        return escape(str(value), quote=True).replace("\n", "<br>")

    advisory_html = ""
    for advisory in advisories:
        alert_type = advisory.get("type", "Advisory")
        safe_places = safe_html(", ".join(advisory.get("affected_areas", [])) or "Cebu City / Nearby Cities")
        issued = safe_html(advisory.get("issued") or alert_time)

        if alert_type == "Heavy Rainfall Warning":
            level = safe_html(advisory.get("warning_level", "ORANGE"))
            advisory_html += f"""
            <div class="advisory-box">
                <h3>HEAVY RAINFALL WARNING</h3>
                <div class="info-row"><span class="label">Warning Level:</span> {level} Rainfall Warning</div>
                <div class="info-row"><span class="label">Affected Area:</span> {safe_places}</div>
                <div class="info-row"><span class="label">Issued By:</span> PAGASA</div>
                <div class="info-row"><span class="label">Date &amp; Time:</span> {issued}</div>
                <div class="info-row">
                    <span class="label">Safety Precautions:</span>
                    <ul>
                        <li>Avoid unnecessary travel.</li>
                        <li>Be cautious of possible flooding in low-lying areas.</li>
                        <li>Monitor local government advisories.</li>
                    </ul>
                </div>
            </div>
            """
        elif alert_type == "Thunderstorm Warning":
            level = safe_html(advisory.get("warning_level", "UNSPECIFIED"))
            outlook = safe_html(advisory.get("thunderstorm_outlook", "UNSPECIFIED"))
            advisory_html += f"""
            <div class="advisory-box">
                <h3>THUNDERSTORM WARNING</h3>
                <div class="info-row"><span class="label">Warning Level:</span> {level}</div>
                <div class="info-row"><span class="label">Thunderstorm Outlook:</span> {outlook}</div>
                <div class="info-row"><span class="label">Affected Area:</span> {safe_places}</div>
                <div class="info-row"><span class="label">Issued By:</span> PAGASA</div>
                <div class="info-row"><span class="label">Date &amp; Time:</span> {issued}</div>
                <div class="info-row">
                    <span class="label">Safety Precautions:</span>
                    <ul>
                        <li>Stay indoors and avoid open areas during active thunderstorms.</li>
                        <li>Unplug sensitive electronics when lightning risk is high.</li>
                        <li>Monitor local government and PAGASA advisories.</li>
                    </ul>
                </div>
            </div>
            """
        elif alert_type == "Tropical Cyclone Alert":
            weather_system = safe_html(advisory.get("weather_system", "Tropical Cyclone"))
            current_location = safe_html(advisory.get("current_location", "Location per PAGASA"))
            signal_level = safe_html(advisory.get("signal_level", "None"))
            advisory_html += f"""
            <div class="advisory-box">
                <h3>TROPICAL DEPRESSION / TYPHOON ALERTS</h3>
                <div class="info-row"><span class="label">Weather System:</span> {weather_system}</div>
                <div class="info-row"><span class="label">Current Location:</span> {current_location}</div>
                <div class="info-row"><span class="label">Signal Level (if any):</span> {signal_level}</div>
                <div class="info-row"><span class="label">Areas Affected:</span> {safe_places}</div>
                <div class="info-row"><span class="label">Date &amp; Time:</span> as of {issued}</div>
                <div class="info-row">
                    <span class="label">Safety Precautions:</span>
                    <ul>
                        <li>Secure loose objects and prepare emergency essentials.</li>
                        <li>Avoid unnecessary travel.</li>
                        <li>Follow advisories from PAGASA and local authorities.</li>
                    </ul>
                </div>
            </div>
            """

    safe_alert_time = safe_html(alert_time)
    
    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #ff9800; color: white; padding: 15px; border-radius: 5px; }}
            .content {{ background-color: #f5f5f5; padding: 20px; margin-top: 10px; border-radius: 5px; }}
            .advisory-box {{ background-color: white; padding: 15px; margin: 15px 0; border-radius: 5px; border-left: 4px solid #ff9800; }}
            .info-row {{ margin: 10px 0; }}
            .label {{ font-weight: bold; color: #ff9800; }}
            ul {{ margin-top: 8px; }}
            li {{ margin-bottom: 6px; }}
            .footer {{ margin-top: 20px; font-size: 0.9em; color: #666; border-top: 1px solid #ddd; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>CRISIS WEATHER ALERTS</h2>
            </div>
            <div class="content">
                {advisory_html}
            </div>
            <div class="footer">
                <p><strong>Source:</strong>
                    <a href="https://www.pagasa.dost.gov.ph/regional-forecast/visprsd">PAGASA Visayas PRSD</a>
                    and
                    <a href="https://www.pagasa.dost.gov.ph/tropical-cyclone/severe-weather-bulletin">PAGASA Severe Weather Bulletin</a>
                </p>
                <p><strong>Alert Time:</strong> {safe_alert_time}</p>
                <p><em>This is an automated crisis alert.</em></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def formatPagasaConsole(new_advisories: List[Dict[str, Any]]) -> str:
    lines = []
    lines.append("PAGASA – Cebu Advisories (Visayas PRSD)")
    lines.append("-" * 52)
    if not new_advisories:
        lines.append("No new advisory.")
    else:
        for advisory in new_advisories:
            places = ", ".join(advisory.get("affected_areas", [])) or "Cebu City / Nearby Cities"
            advisory_type = advisory.get("type", "Advisory")
            issued = advisory.get("issued", "n/a")
            if advisory_type == "Heavy Rainfall Warning":
                lines.append(
                    f"Heavy Rainfall Warning ({advisory.get('warning_level', 'ORANGE')})\n"
                    f"  Issued   : {issued}\n"
                    f"  Areas    : {places}\n"
                )
            elif advisory_type == "Thunderstorm Warning":
                lines.append(
                    f"Thunderstorm Warning ({advisory.get('warning_level', 'UNSPECIFIED')})\n"
                    f"  Outlook  : {advisory.get('thunderstorm_outlook', 'UNSPECIFIED')}\n"
                    f"  Issued   : {issued}\n"
                    f"  Areas    : {places}\n"
                )
            elif advisory_type == "Tropical Cyclone Alert":
                lines.append(
                    f"Tropical Cyclone Alert\n"
                    f"  System   : {advisory.get('weather_system', 'Tropical Cyclone')}\n"
                    f"  Location : {advisory.get('current_location', 'Location per PAGASA')}\n"
                    f"  Signal   : {advisory.get('signal_level', 'None')}\n"
                    f"  Areas    : {places}\n"
                    f"  Issued   : {issued}\n"
                )
    return "\n".join(lines)


def process_advisories(
    session: requests.Session,
    endpoints: List[str],
    seen_pagasa_ids: set,
    tc_endpoints: List[str] = None
) -> Tuple[List[Dict[str, Any]], str, set]:
    def short_error(err: Exception, max_len: int = 220) -> str:
        text = f"{type(err).__name__}: {err}"
        return text if len(text) <= max_len else text[: max_len - 3] + "..."

    try:
        # Fetch PRSD page for Heavy Rainfall Warnings
        vis_html = fetch_pagasa_visprsd(session, endpoints)
        advisories = parse_visprsd_cebu_advisories(vis_html)
        hrw_status = ExtractHRWStatus(vis_html)
        
        # Fetch TC bulletin page for Tropical Cyclone Alerts
        if tc_endpoints is None:
            tc_endpoints = [
                "https://www.pagasa.dost.gov.ph/tropical-cyclone/severe-weather-bulletin",
            ]
        
        try:
            tc_html = fetch_pagasa_tc_bulletin(session, tc_endpoints)
            tc_advisories = parse_tc_bulletin_cebu_alerts(tc_html)
            advisories.extend(tc_advisories)
        except Exception as tc_error:
            # TC bulletin is secondary for this flow; log diagnostic but continue with PRSD results.
            print(f"[PAGASA] TC bulletin fetch skipped this cycle: {short_error(tc_error)}")
        
        new_advisories: List[Dict[str, Any]] = []
        for advisory in advisories:
            issued_part = advisory.get("issued") or ""
            advisory_key = "|".join([
                str(advisory.get("type", "Advisory")),
                str(advisory.get("warning_level", "")),
                str(advisory.get("weather_system", "")),
                str(advisory.get("signal_level", "")),
                str(issued_part),
                ",".join(advisory.get("affected_areas", [])),
            ])
            if advisory_key in seen_pagasa_ids:
                continue
            new_advisories.append(advisory)
            seen_pagasa_ids.add(advisory_key)
        
        return new_advisories, hrw_status, seen_pagasa_ids
        
    except Exception as err:
        diagnostic = short_error(err)
        print(f"[PAGASA] process_advisories failed: {diagnostic}")
        return [], f"HRW: (status unavailable this cycle: {diagnostic})", seen_pagasa_ids
