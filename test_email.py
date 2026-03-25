#!/usr/bin/env python3
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SMTP_HOST = os.getenv("SMTP_HOST", "smtp-mail.outlook.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_APP_PASSWORD = os.getenv("EMAIL_APP_PASSWORD", "")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "")
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "PH Alert System")


def send_test_email(subject: str, html_content: str) -> bool:
    recipients = [r.strip() for r in EMAIL_RECIPIENTS.split(",") if r.strip()]
    
    if not EMAIL_ADDRESS or not EMAIL_APP_PASSWORD:
        print("❌ ERROR: EMAIL_ADDRESS or EMAIL_APP_PASSWORD not set in .env file")
        return False
    
    if not recipients:
        print("❌ ERROR: EMAIL_RECIPIENTS not set in .env file")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_ADDRESS}>"
        msg['To'] = ", ".join(recipients)
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        print(f"📧 Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            print(f"🔐 Logging in as {EMAIL_ADDRESS}...")
            server.login(EMAIL_ADDRESS, EMAIL_APP_PASSWORD)
            print(f"📤 Sending email...")
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {len(recipients)} recipient(s)!")
        print(f"   Subject: {subject}")
        print(f"   Recipients: {', '.join(recipients)}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ Authentication failed! Check your EMAIL_ADDRESS and EMAIL_APP_PASSWORD")
        return False
    except smtplib.SMTPException as e:
        print(f"❌ SMTP Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def main():
    print("=" * 60)
    print("PH Alert System - Email Test for Power Automate Triggers")
    print("=" * 60)
    print()
    
    print("Choose which test email to send:")
    print("1. EARTHQUAKE ALERTS (triggers PHIVOLCS workflow)")
    print("2. HEAVY RAINFALL WARNING (ORANGE/RED) (triggers PAGASA workflow)")
    print("3. TROPICAL DEPRESSION / TYPHOON ALERTS")
    print("4. Send all test emails")
    print("0. Exit")
    print()
    
    choice = input("Enter your choice (0-4): ").strip()
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if choice == "1":
        print("\n📨 Sending EARTHQUAKE ALERTS test email...")
        html = f"""
        <html>
        <body>
            <h2>🚨 TEST: Earthquake Alert</h2>
            <p><strong>This is a test email to verify Power Automate trigger.</strong></p>
            <hr>
            <p><strong>Test Details:</strong></p>
            <ul>
                <li>Subject: EARTHQUAKE ALERT:</li>
                <li>Time: {timestamp}</li>
                <li>Intensity Felt in Cebu: Intensity IV</li>
                <li>Purpose: Trigger PHIVOLCS workflow in Power Automate</li>
            </ul>
            <p>If you receive this email, the trigger should activate and forward to your team.</p>
        </body>
        </html>
        """
        send_test_email("EARTHQUAKE ALERT:", html)
        
    elif choice == "2":
        print("\n📨 Sending HEAVY RAINFALL WARNING test email...")
        html = f"""
        <html>
        <body>
            <h2>⚠️ TEST: Heavy Rainfall Warning</h2>
            <p><strong>This is a test email to verify Power Automate trigger.</strong></p>
            <hr>
            <p><strong>Test Details:</strong></p>
            <ul>
                <li>Subject: HEAVY RAINFALL WARNING</li>
                <li>Time: {timestamp}</li>
                <li>Warning Level: ORANGE Rainfall Warning</li>
                <li>Affected Area: Cebu City / Nearby Cities</li>
                <li>Purpose: Trigger PAGASA workflow in Power Automate</li>
            </ul>
            <p>If you receive this email, the trigger should activate and forward to your team.</p>
        </body>
        </html>
        """
        send_test_email("HEAVY RAINFALL WARNING", html)

    elif choice == "3":
        print("\n📨 Sending TROPICAL DEPRESSION / TYPHOON ALERTS test email...")
        html = f"""
        <html>
        <body>
            <h2>🌀 TEST: Tropical Cyclone Alert</h2>
            <p><strong>This is a test email to verify Power Automate trigger.</strong></p>
            <hr>
            <p><strong>Test Details:</strong></p>
            <ul>
                <li>Subject: TROPICAL DEPRESSION / TYPHOON ALERTS</li>
                <li>Time: {timestamp}</li>
                <li>Weather System: Tropical Storm - SAMPLE</li>
                <li>Signal Level (if any): TCWS #1</li>
                <li>Areas Affected: Cebu City / Nearby Cities</li>
                <li>Purpose: Trigger cyclone workflow in Power Automate</li>
            </ul>
        </body>
        </html>
        """
        send_test_email("TROPICAL DEPRESSION / TYPHOON ALERTS", html)
        
    elif choice == "4":
        print("\n📨 Sending all test emails...")
        
        print("\n1️⃣ Sending EARTHQUAKE ALERT...")
        html1 = f"""
        <html>
        <body>
            <h2>🚨 TEST: Earthquake Alert</h2>
            <p><strong>This is a test email to verify Power Automate trigger.</strong></p>
            <hr>
            <p><strong>Test Details:</strong></p>
            <ul>
                <li>Subject: EARTHQUAKE ALERT:</li>
                <li>Time: {timestamp}</li>
                <li>Purpose: Trigger PHIVOLCS workflow in Power Automate</li>
            </ul>
        </body>
        </html>
        """
        send_test_email("EARTHQUAKE ALERT:", html1)
        
        print("\n2️⃣ Sending HEAVY RAINFALL WARNING...")
        html2 = f"""
        <html>
        <body>
            <h2>⚠️ TEST: Heavy Rainfall Warning</h2>
            <p><strong>This is a test email to verify Power Automate trigger.</strong></p>
            <hr>
            <p><strong>Test Details:</strong></p>
            <ul>
                <li>Subject: HEAVY RAINFALL WARNING</li>
                <li>Time: {timestamp}</li>
                <li>Purpose: Trigger PAGASA workflow in Power Automate</li>
            </ul>
        </body>
        </html>
        """
        send_test_email("HEAVY RAINFALL WARNING", html2)

        print("\n3️⃣ Sending TROPICAL DEPRESSION / TYPHOON ALERTS...")
        html3 = f"""
        <html>
        <body>
            <h2>🌀 TEST: Tropical Cyclone Alert</h2>
            <ul>
                <li>Subject: TROPICAL DEPRESSION / TYPHOON ALERTS</li>
                <li>Time: {timestamp}</li>
                <li>Weather System: Tropical Storm - SAMPLE</li>
                <li>Signal Level: TCWS #1</li>
                <li>Areas Affected: Cebu City / Nearby Cities</li>
            </ul>
        </body>
        </html>
        """
        send_test_email("TROPICAL DEPRESSION / TYPHOON ALERTS", html3)
        
    elif choice == "0":
        print("Exiting...")
        return
    else:
        print("❌ Invalid choice!")
        return
    
    print("\n" + "=" * 60)
    print("Test complete! Check your email and Power Automate flow.")
    print("=" * 60)


if __name__ == "__main__":
    main()
