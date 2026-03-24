import re
import time
import requests
from html import escape
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime


def parseDT(text: str) -> Optional[datetime]:
    if not text:
        return None
    try:
        from dateutil import parser as dtparse
        return dtparse.parse(text, fuzzy=True)
    except Exception:
        return None


def fetch_pagasa_visprsd(
    session: requests.Session,
    endpoints: List[str] = None
) -> str:
    if endpoints is None:
        endpoints = [
            "https://bagong.pagasa.dost.gov.ph/regional-forecast/visprsd",
            "https://www.pagasa.dost.gov.ph/regional-forecast/visprsd",
        ]
    
    lastError = None
    for url in endpoints:
        try:
            Read = session.get(url, timeout=(10, 30))
            Read.raise_for_status()
            return Read.text
        except Exception as Exempted:
            lastError = Exempted
            time.sleep(2)
    
    raise RuntimeError(f"PAGASA fetch failed on all endpoints: {lastError}")


def parse_visprsd_cebu_advisories(html: str) -> List[Dict[str, Any]]:
    soup = BeautifulSoup(html, "lxml")
    Blocks: List[str] = []

    for Element in soup.find_all(string=re.compile(r"Thunderstorm Advisory No\.\s*\d+", re.I)):
        parent = Element.parent
        Text = re.sub(r"\s+", " ", parent.get_text(" ", strip=True)) if parent else str(Element).strip()
        if len(Text) < 60 and parent and parent.parent:
            Text = re.sub(r"\s+", " ", parent.parent.get_text(" ", strip=True))
        Blocks.append(Text)
   
    for Element in soup.find_all(string=re.compile(r"Heavy Rainfall Warning", re.I)):
        parent = Element.parent
        Text = re.sub(r"\s+", " ", parent.get_text(" ", strip=True)) if parent else str(Element).strip()
        if len(Text) < 60 and parent and parent.parent:
            Text = re.sub(r"\s+", " ", parent.parent.get_text(" ", strip=True))
        Blocks.append(Text)

    Unique, Seen = [], set()
    for Block in Blocks:
        Key = re.sub(r"\s+", " ", Block)
        if Key not in Seen:
            Seen.add(Key)
            Unique.append(Block)

    out: List[Dict[str, Any]] = []
    
    for Block in Unique:
        if not re.search(r"\bCebu\b|#Cebu\b", Block, flags=re.I):
            continue

        number = "?"
        Minimum = re.search(r"Thunderstorm Advisory No\.\s*([0-9]+)", Block, flags=re.I)
        if Minimum:
            number = Minimum.group(1)

        issuedISO = None
        Missed = re.search(
            r"Issued\s+at\s+(.+?)(?=$|\.| within| Moderate| Light| The above| Heavy| Orange| Yellow)",
            Block,
            flags=re.I
        )
        if Missed:
            Text = Missed.group(1).strip()
            try:
                issuedISO = parseDT(Text).isoformat()
            except Exception:
                issuedISO = Text

        places: List[str] = []
        cebuPlace = re.search(r"#Cebu\s*\(([^)]*)\)", Block, flags=re.I)
        if cebuPlace:
            raw = cebuPlace.group(1)
            parts = [part.strip() for part in raw.split(",")]
            for part in parts:
                part = re.sub(r"([a-z])([A-Z])", r"\1 \2", part)
                part = part.replace("CityOf", "City of ")
                places.append(part)
        
        if not places:
            places = ["Cebu (unspecified LGUs)"]

        out.append({
            "source": "PAGASA",
            "type": "Thunderstorm Advisory" if Minimum else "Rainfall Advisory",
            "number": number,
            "issued": issuedISO,
            "mentions_cebu": True,
            "cebu_places": places,
            "raw": Block
        })

    return out


def ExtractHRWStatus(html: str) -> str:
    soup = BeautifulSoup(html, "lxml")
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
        places = ", ".join(advisory.get("cebu_places", [])) or "Cebu (unspecified LGUs)"
        raw = advisory.get("raw", "")[:500]
        advisory_type = safe_html(advisory.get("type", "Advisory"))
        advisory_number = safe_html(advisory.get("number", "?"))
        issued = safe_html(advisory.get("issued", "n/a"))
        safe_places = safe_html(places)
        safe_raw = safe_html(raw)
        advisory_html += f"""
        <div class="advisory-box">
            <h3>{advisory_type} #{advisory_number}</h3>
            <div class="info-row">
                <span class="label">Issued:</span> {issued}
            </div>
            <div class="info-row">
                <span class="label">Affected Areas (Cebu):</span> {safe_places}
            </div>
            <div class="info-row">
                <span class="label">Details:</span><br>
                <div style="margin-top: 5px; padding: 10px; background-color: #fff3cd; border-radius: 3px;">
                    {safe_raw}
                </div>
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
            .footer {{ margin-top: 20px; font-size: 0.9em; color: #666; border-top: 1px solid #ddd; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>⚠️ WEATHER ADVISORY - PAGASA (Cebu)</h2>
            </div>
            <div class="content">
                {advisory_html}
            </div>
            <div class="footer">
                <p><strong>Source:</strong> PAGASA Visayas PRSD (Philippine Atmospheric, Geophysical and Astronomical Services Administration)</p>
                <p><strong>Alert Time:</strong> {safe_alert_time}</p>
                <p><em>This is an automated alert from the NCR Atleos Alert System.</em></p>
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
            places = ", ".join(advisory.get("cebu_places", [])) or "Cebu (unspecified LGUs)"
            raw = advisory.get("raw", "")
            lines.append(
                f"{advisory['type']} #{advisory.get('number', '?')}\n"
                f"  Issued   : {advisory.get('issued', 'n/a')}\n"
                f"  Cebu     : {places}\n"
                f"  Raw      : {raw[:500]}{'...' if len(raw) > 500 else ''}\n"
            )
    return "\n".join(lines)


def process_advisories(
    session: requests.Session,
    endpoints: List[str],
    seen_pagasa_ids: set
) -> Tuple[List[Dict[str, Any]], str, set]:
    try:
        vis_html = fetch_pagasa_visprsd(session, endpoints)
        advisories = parse_visprsd_cebu_advisories(vis_html)
        
        new_advisories: List[Dict[str, Any]] = []
        for advisory in advisories:
            issued_part = advisory.get("issued") or ""
            advisory_key = f"VSPRSD-TA-{advisory['number']}-{issued_part}"
            if advisory_key in seen_pagasa_ids:
                continue
            new_advisories.append(advisory)
            seen_pagasa_ids.add(advisory_key)
        
        hrw_status = ExtractHRWStatus(vis_html)
        
        return new_advisories, hrw_status, seen_pagasa_ids
        
    except Exception:
        return [], "HRW: (status unavailable this cycle)", seen_pagasa_ids
