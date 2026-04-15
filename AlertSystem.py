#!/usr/bin/env python3
from __future__ import annotations
import os, json, time, traceback
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any

import requests
from dateutil import parser as dtparse
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

from PHIVOLCS import (
    process_earthquakes,
    formatEarthquakeEmail,
    formatEarthquakeConsole,
    meetsAlertCriteria,
    annotateUSGSConfirmation,
)
from PAGASA import process_advisories, formatPagasaEmail, formatPagasaConsole

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def envBool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default

    value = raw.strip().lower()
    if value in {"1", "true", "yes", "y", "on"}:
        return True
    if value in {"0", "false", "no", "n", "off"}:
        return False

    print(f"[Config] Invalid boolean for {name}={raw!r}; using default {default}")
    return default


def envInt(name: str, default: int, minimum: Optional[int] = None) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default

    try:
        value = int(raw)
    except Exception:
        print(f"[Config] Invalid integer for {name}={raw!r}; using default {default}")
        return default

    if minimum is not None and value < minimum:
        print(f"[Config] {name} below minimum ({minimum}); using minimum value")
        return minimum
    return value


def envFloat(name: str, default: float, minimum: Optional[float] = None) -> float:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default

    try:
        value = float(raw)
    except Exception:
        print(f"[Config] Invalid number for {name}={raw!r}; using default {default}")
        return default

    if minimum is not None and value < minimum:
        print(f"[Config] {name} below minimum ({minimum}); using minimum value")
        return minimum
    return value


PollIntervalSec = envInt("POLL_INTERVAL_SEC", 30, minimum=1)

PhivolcsAPIurl = os.getenv("PHIVOLCS_API_URL", "http://localhost:3001/api/earthquakes")

smartRefresh = envBool("SMART_REFRESH", True)
StaleMaxSec = envInt("STALE_MAX_SEC", 60, minimum=0)
NoNewCyclesBeforeRefresh = envInt("NO_NEW_CYCLES_BEFORE_REFRESH", 1, minimum=0)
MinRefreshGapSec = envInt("MIN_REFRESH_GAP_SEC", 25, minimum=0)

ColdStartSupress = envBool("COLD_START_SUPPRESS", True)
MaxEventAgeMin = envInt("MAX_EVENT_AGE_MIN", 0, minimum=0)
MaxPendingQuakeEvents = envInt("MAX_PENDING_QUAKE_EVENTS", 5, minimum=0)
USGSConfirmationEnabled = envBool("USGS_CONFIRMATION_ENABLED", True)
USGSMatchTimeWindowMin = envFloat("USGS_MATCH_TIME_WINDOW_MIN", 20.0, minimum=0.0)
USGSMatchMaxDistanceKm = envFloat("USGS_MATCH_MAX_DISTANCE_KM", 180.0, minimum=0.0)
USGSMatchMagTolerance = envFloat("USGS_MATCH_MAG_TOLERANCE", 0.8, minimum=0.0)

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = envInt("SMTP_PORT", 587, minimum=1)
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "")
EMAIL_ENABLED = envBool("EMAIL_ENABLED", True)
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "NCR Alert System")

PAGASA_endpoints = [
    "https://www.pagasa.dost.gov.ph/regional-forecast/visprsd",
]

stateFile = os.getenv("STATE_FILE", "state_phivolcs_pagasa.json")

def makeSession() -> requests.Session:
    Sessions = requests.Session()
    Sessions.headers.update({
        "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/122.0.0.0 Safari/537.36"),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Cache-Control": "no-cache",
        "Connection": "close",
    })
    retry = Retry(
        total=3, connect=3, read=3, status=3,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=frozenset(["GET"]),
        backoff_factor=0.8,
    )
    Sessions.mount("https://", HTTPAdapter(max_retries=retry))
    return Sessions


def loadState() -> Dict[str, Any]:
    if os.path.exists(stateFile):
        try:
            with open(stateFile, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "seen_quake_ids": [],
        "pending_quake_events": [],
        "seen_pagasa_ids": [],
        "no_new_cycles": 0,
        "last_top_id": "",            
        "last_alerted_dt_iso": None    
    }

def saveState(State: Dict[str, Any]) -> None:
    with open(stateFile, "w", encoding="utf-8") as f:
        json.dump(State, f, indent=2)

def nowIso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")

def parseDT(text: str) -> Optional[datetime]:
    if not text:
        return None
    try:
        return dtparse.parse(text, fuzzy=True)
    except Exception:
        return None


def quakeSortKey(quake: Dict[str, Any]) -> float:
    quake_dt = parseDT(str(quake.get("time", "")))
    if not quake_dt:
        return 0.0
    if quake_dt.tzinfo is None:
        quake_dt = quake_dt.replace(tzinfo=timezone.utc)
    return quake_dt.timestamp()


def serializeQuakeForState(quake: Dict[str, Any]) -> Dict[str, Any]:
    transient_keys = {"_dt", "usgs_confirmed", "usgs_match", "usgs_match_summary"}
    return {key: value for key, value in quake.items() if key not in transient_keys}


def sendEmail(subject: str, html_content: str, recipients: List[str]) -> bool:
    if not EMAIL_ENABLED:
        print("  [Email] Disabled via config")
        return False
    
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        print("  [Email] Missing EMAIL_ADDRESS or EMAIL_APP_PASSWORD")
        return False
    
    if not recipients:
        print("  [Email] No recipients specified")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_ADDRESS}>"
        msg['To'] = ", ".join(recipients)
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            server.send_message(msg)
        
        print(f"  [Email] ✓ Sent to {len(recipients)} recipient(s)")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("  [Email] ✗ Authentication failed. Check EMAIL_ADDRESS and EMAIL_APP_PASSWORD")
        return False
    except smtplib.SMTPException as e:
        print(f"  [Email] ✗ SMTP error: {e}")
        return False
    except Exception as e:
        print(f"  [Email] ✗ Error: {e}")
        traceback.print_exc()
        return False

def sendAlertEmail(earthquake: Optional[Dict[str, Any]] = None,
                   advisories: Optional[List[Dict[str, Any]]] = None) -> Dict[str, bool]:
    result = {"earthquake_sent": False, "advisories_sent": False}
    if not earthquake and not advisories:
        return result
    
    alert_time = nowIso()
    recipients = [r.strip() for r in EMAIL_RECIPIENTS.split(",") if r.strip()]
    if not recipients:
        print("  [Email] No recipients configured in EMAIL_RECIPIENTS")
        return result
    
    if earthquake:
        subject = "EARTHQUAKE ALERT:"
        html = formatEarthquakeEmail(earthquake, alert_time)
        result["earthquake_sent"] = sendEmail(subject, html, recipients)
    
    if advisories:
        advisory_types = {str(ad.get("type", "")).strip() for ad in advisories}
        if advisory_types == {"Heavy Rainfall Warning"}:
            subject = "HEAVY RAINFALL WARNING"
        elif advisory_types == {"Thunderstorm Warning"}:
            subject = "THUNDERSTORM WARNING"
        elif advisory_types == {"Tropical Cyclone Alert"}:
            subject = "TROPICAL DEPRESSION / TYPHOON ALERTS"
        else:
            subject = "CRISIS WEATHER ALERTS"
        html = formatPagasaEmail(advisories, alert_time)
        result["advisories_sent"] = sendEmail(subject, html, recipients)

    return result


def main():
    session = makeSession()
    state = loadState()
    
    seen_quakes = set(state.get("seen_quake_ids", []))
    pending_quake_events: List[Dict[str, Any]] = state.get("pending_quake_events", [])
    seen_pagasa = set(state.get("seen_pagasa_ids", []))
    no_new_cycles = int(state.get("no_new_cycles", 0))
    last_top_id = state.get("last_top_id", "")
    last_alerted_dt_iso = state.get("last_alerted_dt_iso")
    last_alerted_dt: Optional[datetime] = None
    if last_alerted_dt_iso:
        try:
            last_alerted_dt = dtparse.parse(last_alerted_dt_iso)
        except Exception:
            last_alerted_dt = None
        
    cold_start = ColdStartSupress and (last_alerted_dt is None)
    last_refresh_mono = 0.0

    print("=" * 70)
    print("NCR Alert System (PHIVOLCS + PAGASA) with Email Integration")
    print("=" * 70)
    print(f"Poll Interval      : {PollIntervalSec}s")
    print(f"PHIVOLCS API       : {PhivolcsAPIurl}")
    print(f"Smart Refresh      : {'Enabled' if smartRefresh else 'Disabled'}")
    print(f"Cold Start Suppress: {'Yes' if ColdStartSupress else 'No'}")
    print(f"Max Event Age      : {MaxEventAgeMin} minutes" if MaxEventAgeMin > 0 else "Max Event Age      : Unlimited")
    print(f"USGS Confirmation  : {'Enabled' if USGSConfirmationEnabled else 'Disabled'}")
    print(f"\nEmail Configuration:")
    print(f"  Enabled          : {'Yes' if EMAIL_ENABLED else 'No'}")
    print(f"  SMTP Host        : {SMTP_HOST}:{SMTP_PORT}")
    print(f"  From Address     : {EMAIL_ADDRESS if EMAIL_ADDRESS else '(not set)'}")
    print(f"  Recipients       : {EMAIL_RECIPIENTS if EMAIL_RECIPIENTS else '(not set)'}")
    print(f"  Authentication   : {'App Password Configured' if EMAIL_APP_PASSWORD else '(not set)'}")
    print("=" * 70)
    print("\nStarting monitoring...\n")

    while True:
        try:
            timestamp = nowIso()
            
            (
                pending_earthquakes,
                meta,
                seen_quakes,
                last_alerted_dt,
                last_top_id,
                no_new_cycles,
                last_refresh_mono,
                cold_start
            ) = process_earthquakes(
                PhivolcsAPIurl,
                seen_quakes,
                last_alerted_dt,
                last_top_id,
                no_new_cycles,
                last_refresh_mono,
                cold_start,
                MaxEventAgeMin,
                smartRefresh,
                StaleMaxSec,
                NoNewCyclesBeforeRefresh,
                MinRefreshGapSec
            )

            pending_by_id: Dict[str, Dict[str, Any]] = {}
            for quake in pending_quake_events:
                quake_id = str(quake.get("id", "")).strip()
                if not quake_id:
                    continue
                if f"PHIVOLCS-{quake_id}" in seen_quakes:
                    continue
                if not meetsAlertCriteria(quake):
                    continue
                pending_by_id[quake_id] = quake

            for quake in pending_earthquakes:
                quake_id = str(quake.get("id", "")).strip()
                if not quake_id:
                    continue
                if f"PHIVOLCS-{quake_id}" in seen_quakes:
                    continue
                if not meetsAlertCriteria(quake):
                    continue
                pending_by_id[quake_id] = quake

            pending_quake_events = sorted(pending_by_id.values(), key=quakeSortKey)
            if MaxPendingQuakeEvents > 0 and len(pending_quake_events) > MaxPendingQuakeEvents:
                pending_quake_events = pending_quake_events[-MaxPendingQuakeEvents:]

            pending_quake_events = annotateUSGSConfirmation(
                pending_quake_events,
                enabled=USGSConfirmationEnabled,
                time_window_minutes=USGSMatchTimeWindowMin,
                max_distance_km=USGSMatchMaxDistanceKm,
                magnitude_tolerance=USGSMatchMagTolerance,
            )
            
            new_advisories, hrw_status, seen_pagasa = process_advisories(
                session,
                PAGASA_endpoints,
                seen_pagasa
            )
            
            if pending_quake_events or new_advisories:
                label_parts = []
                if pending_quake_events:
                    label_parts.append(f"Quake x{len(pending_quake_events)}")
                if new_advisories:
                    label_parts.append("PAGASA Advisory")
                label = " & ".join(label_parts)
                
                print(f"[{timestamp}] NEW items found → {label}")

                if pending_quake_events:
                    print(f"[{timestamp}] Pending Cebu earthquake alerts: {len(pending_quake_events)}")
                    while pending_quake_events:
                        quake = pending_quake_events[0]
                        quake_id = str(quake.get("id", "")).strip()

                        print(formatEarthquakeConsole(quake))
                        print(f"[{timestamp}] Sending earthquake email alert...")
                        email_result = sendAlertEmail(earthquake=quake)
                        if not email_result.get("earthquake_sent"):
                            print(f"[{timestamp}] Earthquake email failed. Will retry this event in the next cycle.")
                            break

                        if quake_id:
                            seen_quakes.add(f"PHIVOLCS-{quake_id}")

                        quake_dt = parseDT(str(quake.get("time", "")))
                        if quake_dt and (last_alerted_dt is None or quake_dt > last_alerted_dt):
                            last_alerted_dt = quake_dt

                        pending_quake_events.pop(0)

                if new_advisories:
                    print(formatPagasaConsole(new_advisories))
                    print(f"[{timestamp}] Sending PAGASA advisory email alerts...")
                    sendAlertEmail(advisories=new_advisories)
            else:
                cached = meta.get("cached")
                last_updated = meta.get("lastUpdated")
                count = meta.get("count")
                if cached is not None:
                    print(f"[{timestamp}] No new event | {hrw_status} | cached={cached} lastUpdated={last_updated} count={count}")
                else:
                    print(f"[{timestamp}] No new event | {hrw_status}")
            
            saveState({
                "seen_quake_ids": sorted(seen_quakes),
                "pending_quake_events": [serializeQuakeForState(q) for q in pending_quake_events],
                "seen_pagasa_ids": sorted(seen_pagasa),
                "no_new_cycles": int(no_new_cycles),
                "last_top_id": last_top_id,
                "last_alerted_dt_iso": last_alerted_dt.isoformat() if last_alerted_dt else last_alerted_dt_iso,
            })
            
        except Exception as e:
            print(f"[{nowIso()}] Loop error: {e}")
            traceback.print_exc()
        
        time.sleep(PollIntervalSec)


if __name__ == "__main__":
    main()