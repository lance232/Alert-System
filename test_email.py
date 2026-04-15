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
EMAIL_FROM_NAME = os.getenv("EMAIL_FROM_NAME", "NCR Alert System")

SUBJECT_EARTHQUAKE = "Test Email: Earthquake Alert"
SUBJECT_WEATHER = "Test Email: Weather Crisis"


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


def generate_test_email_html(alert_type: str, alert_time: str) -> str:
    """Generate weather HTML template matching AlertSystem.py formatPagasaEmail format."""
    
    if alert_type == "HEAVY_RAINFALL":
        advisory_html = """
            <div class="advisory-box">
                <h3>HEAVY RAINFALL WARNING</h3>
                <div class="info-row"><span class="label">Warning Level:</span> Per latest PAGASA advisory</div>
                <div class="info-row"><span class="label">Affected Area:</span> Per latest PAGASA advisory</div>
                <div class="info-row"><span class="label">Issued By:</span> PAGASA</div>
                <div class="info-row"><span class="label">Date &amp; Time:</span> {alert_time}</div>
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
    
    elif alert_type == "TROPICAL_CYCLONE":
        advisory_html = """
            <div class="advisory-box">
                <h3>TROPICAL DEPRESSION / TYPHOON ALERTS</h3>
                <div class="info-row"><span class="label">Weather System:</span> Per latest PAGASA advisory</div>
                <div class="info-row"><span class="label">Current Location:</span> Per latest PAGASA advisory</div>
                <div class="info-row"><span class="label">Signal Level (if any):</span> Per latest PAGASA advisory</div>
                <div class="info-row"><span class="label">Areas Affected:</span> Per latest PAGASA advisory</div>
                <div class="info-row"><span class="label">Date &amp; Time:</span> as of {alert_time}</div>
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
    elif alert_type == "THUNDERSTORM":
        advisory_html = """
            <div class="advisory-box">
                <h3>THUNDERSTORM WARNING</h3>
                <div class="info-row"><span class="label">Warning Level:</span> Per latest PAGASA advisory</div>
                <div class="info-row"><span class="label">Affected Area:</span> Per latest PAGASA advisory</div>
                <div class="info-row"><span class="label">Issued By:</span> PAGASA</div>
                <div class="info-row"><span class="label">Date &amp; Time:</span> {alert_time}</div>
                <div class="info-row">
                    <span class="label">Safety Precautions:</span>
                    <ul>
                        <li>Stay indoors and avoid open high ground points.</li>
                        <li>Unplug electronics during lightning activity.</li>
                        <li>Monitor local advisories for changes.</li>
                    </ul>
                </div>
            </div>
            """
    else:
        advisory_html = ""
    
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
                <p><strong>Alert Time:</strong> {alert_time}</p>
                <p><em>This is an automated crisis alert.</em></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def generate_earthquake_test_email_html(alert_time: str) -> str:
    """Generate earthquake HTML template matching PHIVOLCS email format."""

    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #d32f2f; color: white; padding: 15px; border-radius: 5px; }}
            .content {{ background-color: #f5f5f5; padding: 20px; margin-top: 10px; border-radius: 5px; }}
            .info-row {{ margin: 10px 0; padding: 8px; background-color: white; border-left: 4px solid #d32f2f; }}
            .label {{ font-weight: bold; color: #d32f2f; }}
            ul {{ margin-top: 8px; }}
            li {{ margin-bottom: 6px; }}
            .footer {{ margin-top: 20px; font-size: 0.9em; color: #666; border-top: 1px solid #ddd; padding-top: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>EARTHQUAKE ALERTS</h2>
            </div>
            <div class="content">
                <div class="info-row">
                    <span class="label">Date &amp; Time:</span> Per latest PHIVOLCS advisory
                </div>
                <div class="info-row">
                    <span class="label">Magnitude:</span> Per latest PHIVOLCS advisory
                </div>
                <div class="info-row">
                    <span class="label">Epicenter Location:</span> Per latest PHIVOLCS advisory
                </div>
                <div class="info-row">
                    <span class="label">Intensity Felt in Cebu:</span> Per latest PHIVOLCS advisory
                </div>
                <div class="info-row">
                    <span class="label">Safety Precautions:</span>
                    <ul>
                        <li>Duck, Cover, and Hold during the shaking.</li>
                        <li>Stay calm and be alert for possible aftershocks.</li>
                        <li>Check surroundings for hazards (falling objects, cracks).</li>
                        <li>Follow instructions from authorities.</li>
                    </ul>
                </div>
            </div>
            <div class="footer">
                <p><strong>Source:</strong> <a href="https://earthquake.phivolcs.dost.gov.ph/">PHIVOLCS Earthquake Information</a></p>
                <p><strong>Alert Time:</strong> {alert_time}</p>
                <p><em>This is an automated crisis alert.</em></p>
            </div>
        </div>
    </body>
    </html>
    """


def main():
    print("=" * 70)
    print("NCR Alert System - Email Test (Format matches AlertSystem.py)")
    print("=" * 70)
    print()
    
    print("Choose which test email to send:")
    print("1. EARTHQUAKE ALERTS (triggers PHIVOLCS workflow)")
    print("2. HEAVY RAINFALL WARNING (triggers PAGASA workflow)")
    print("3. TROPICAL DEPRESSION / TYPHOON ALERTS (triggers PAGASA workflow)")
    print("4. THUNDERSTORM WARNING (triggers PAGASA workflow)")
    print("5. Send all test emails")
    print("0. Exit")
    print()
    
    choice = input("Enter your choice (0-5): ").strip()
    
    alert_time = datetime.now().isoformat(timespec="seconds")
    
    if choice == "1":
        print("\n📨 Sending EARTHQUAKE ALERT test email...")
        print(f"   Subject: {SUBJECT_EARTHQUAKE}")
        html = generate_earthquake_test_email_html(alert_time)
        send_test_email(SUBJECT_EARTHQUAKE, html)
        
    elif choice == "2":
        print("\n📨 Sending HEAVY RAINFALL WARNING test email...")
        print(f"   Subject: {SUBJECT_WEATHER}")
        html = generate_test_email_html("HEAVY_RAINFALL", alert_time)
        send_test_email(SUBJECT_WEATHER, html)

    elif choice == "3":
        print("\n📨 Sending TROPICAL DEPRESSION / TYPHOON ALERTS test email...")
        print(f"   Subject: {SUBJECT_WEATHER}")
        html = generate_test_email_html("TROPICAL_CYCLONE", alert_time)
        send_test_email(SUBJECT_WEATHER, html)
        
    elif choice == "4":
        print("\n📨 Sending THUNDERSTORM WARNING test email...")
        print(f"   Subject: {SUBJECT_WEATHER}")
        html = generate_test_email_html("THUNDERSTORM", alert_time)
        send_test_email(SUBJECT_WEATHER, html)

    elif choice == "5":
        print("\n📨 Sending all test emails...")
        
        print("\n1️⃣ Sending EARTHQUAKE ALERT...")
        earthquake_html = generate_earthquake_test_email_html(alert_time)
        send_test_email(SUBJECT_EARTHQUAKE, earthquake_html)
        
        print("\n2️⃣ Sending HEAVY RAINFALL WARNING...")
        html2 = generate_test_email_html("HEAVY_RAINFALL", alert_time)
        send_test_email(SUBJECT_WEATHER, html2)

        print("\n3️⃣ Sending TROPICAL DEPRESSION / TYPHOON ALERTS...")
        html3 = generate_test_email_html("TROPICAL_CYCLONE", alert_time)
        send_test_email(SUBJECT_WEATHER, html3)

        print("\n4️⃣ Sending THUNDERSTORM WARNING...")
        html4 = generate_test_email_html("THUNDERSTORM", alert_time)
        send_test_email(SUBJECT_WEATHER, html4)
        
    elif choice == "0":
        print("Exiting...")
        return
    else:
        print("❌ Invalid choice!")
        return
    
    print("\n" + "=" * 70)
    print("Test complete! Check your inbox and Power Automate flows.")
    print("=" * 70)


if __name__ == "__main__":
    main()