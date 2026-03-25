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

from PHIVOLCS import process_earthquakes, formatEarthquakeEmail, formatEarthquakeConsole
from PAGASA import process_advisories, formatPagasaEmail, formatPagasaConsole

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

PollIntervalSec = int(os.getenv("POLL_INTERVAL_SEC", "30"))

PhivolcsAPIurl = os.getenv("PHIVOLCS_API_URL", "http://localhost:3001/api/earthquakes")

smartRefresh = os.getenv("SMART_REFRESH", "1") == "1"
StaleMaxSec = int(os.getenv("STALE_MAX_SEC", "60"))
NoNewCyclesBeforeRefresh = int(os.getenv("NO_NEW_CYCLES_BEFORE_REFRESH", "1"))
MinRefreshGapSec = int(os.getenv("MIN_REFRESH_GAP_SEC", "25"))

ColdStartSupress = os.getenv("COLD_START_SUPPRESS", "1") == "1"      
MaxEventAgeMin = int(os.getenv("MAX_EVENT_AGE_MIN", "0"))

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "")
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "1") == "1"
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "PH Alert System")

PAGASA_endpoints = [
    "https://bagong.pagasa.dost.gov.ph/regional-forecast/visprsd",
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
                   advisories: Optional[List[Dict[str, Any]]] = None) -> None:
    if not earthquake and not advisories:
        return
    
    alert_time = nowIso()
    recipients = [r.strip() for r in EMAIL_RECIPIENTS.split(",") if r.strip()]
    if not recipients:
        print("  [Email] No recipients configured in EMAIL_RECIPIENTS")
        return
    
    if earthquake:
        subject = "EARTHQUAKE ALERT:"
        html = formatEarthquakeEmail(earthquake, alert_time)
        sendEmail(subject, html, recipients)
    
    if advisories:
        advisory_types = {str(ad.get("type", "")).strip() for ad in advisories}
        if advisory_types == {"Heavy Rainfall Warning"}:
            subject = "HEAVY RAINFALL WARNING"
        elif advisory_types == {"Tropical Cyclone Alert"}:
            subject = "TROPICAL DEPRESSION / TYPHOON ALERTS"
        else:
            subject = "CRISIS WEATHER ALERTS"
        html = formatPagasaEmail(advisories, alert_time)
        sendEmail(subject, html, recipients)


def main():
    session = makeSession()
    state = loadState()
    
    seen_quakes = set(state.get("seen_quake_ids", []))
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
    print("PHIVOLCS + PAGASA Alert System with Email Integration")
    print("=" * 70)
    print(f"Poll Interval      : {PollIntervalSec}s")
    print(f"PHIVOLCS API       : {PhivolcsAPIurl}")
    print(f"Smart Refresh      : {'Enabled' if smartRefresh else 'Disabled'}")
    print(f"Cold Start Suppress: {'Yes' if ColdStartSupress else 'No'}")
    print(f"Max Event Age      : {MaxEventAgeMin} minutes" if MaxEventAgeMin > 0 else "Max Event Age      : Unlimited")
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
                latest_earthquake,
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
            
            new_advisories, hrw_status, seen_pagasa = process_advisories(
                session,
                PAGASA_endpoints,
                seen_pagasa
            )
            
            if latest_earthquake or new_advisories:
                lines = [f"=== PH Alerts – New items @ {timestamp} ===\n"]
                if latest_earthquake:
                    lines.append(formatEarthquakeConsole(latest_earthquake))
                    lines.append("")
                if new_advisories:
                    lines.append(formatPagasaConsole(new_advisories))
                    lines.append("")
                lines.append("Sources: PHIVOLCS (via local API); PAGASA Visayas PRSD page.")
                
                label_parts = []
                if latest_earthquake:
                    label_parts.append("Quake")
                if new_advisories:
                    label_parts.append("PAGASA Advisory")
                label = " & ".join(label_parts)
                
                print(f"[{timestamp}] NEW items found → {label}")
                print("\n".join(lines))
                
                print(f"[{timestamp}] Sending email alerts...")
                sendAlertEmail(earthquake=latest_earthquake, advisories=new_advisories)
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
