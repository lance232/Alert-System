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


def generate_test_email_html(alert_type: str, alert_time: str) -> str:
    """Generate HTML matching AlertSystem.py formatPagasaEmail format"""
    
    if alert_type == "HEAVY_RAINFALL":
        advisory_html = """
            <div class="advisory-box">
                <h3>HEAVY RAINFALL WARNING</h3>
                <div class="info-row"><span class="label">Warning Level:</span> ORANGE Rainfall Warning</div>
                <div class="info-row"><span class="label">Affected Area:</span> Cebu City / Nearby Cities</div>
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
                <div class="info-row"><span class="label">Weather System:</span> Tropical Storm - SAMPLE</div>
                <div class="info-row"><span class="label">Current Location:</span> Location per PAGASA</div>
                <div class="info-row"><span class="label">Signal Level (if any):</span> TCWS #1</div>
                <div class="info-row"><span class="label">Areas Affected:</span> Cebu City / Nearby Cities</div>
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
                <p><strong>Source:</strong> PAGASA Visayas PRSD (Philippine Atmospheric, Geophysical and Astronomical Services Administration)</p>
                <p><strong>Alert Time:</strong> {alert_time}</p>
                <p><em>This is an automated crisis alert.</em></p>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def main():
    print("=" * 70)
    print("PH Alert System - Email Test (Format matches AlertSystem.py)")
    print("=" * 70)
    print()
    
    print("Choose which test email to send:")
    print("1. EARTHQUAKE ALERTS (triggers PHIVOLCS workflow)")
    print("2. HEAVY RAINFALL WARNING (ORANGE/RED) (triggers PAGASA workflow)")
    print("3. TROPICAL DEPRESSION / TYPHOON ALERTS (triggers PAGASA workflow)")
    print("4. Send all test emails")
    print("0. Exit")
    print()
    
    choice = input("Enter your choice (0-4): ").strip()
    
    alert_time = datetime.now().isoformat(timespec="seconds")
    
    if choice == "1":
        print("\n📨 Sending EARTHQUAKE ALERT test email...")
        print(f"   Subject: EARTHQUAKE ALERT:")
        # Format matches PHIVOLCS formatEarthquakeEmail from AlertSystem.py
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
                        <span class="label">Date &amp; Time:</span> 2026-03-26T14:30:15+08:00
                    </div>
                    <div class="info-row">
                        <span class="label">Magnitude:</span> 6.2
                    </div>
                    <div class="info-row">
                        <span class="label">Epicenter Location:</span> 15 km E of Cebu City
                    </div>
                    <div class="info-row">
                        <span class="label">Intensity Felt in Cebu:</span> Intensity IV
                    </div>
                    <div class="info-row">
                        <span class="label">Safety Precautions:</span>
                        <ul>
                            <li>Stay calm and be alert for possible aftershocks.</li>
                            <li>Check surroundings for hazards (falling objects, cracks).</li>
                            <li>Follow instructions from authorities.</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p><strong>Source:</strong> PHIVOLCS (Philippine Institute of Volcanology and Seismology)</p>
                    <p><strong>Alert Time:</strong> {alert_time}</p>
                    <p><em>This is an automated crisis alert.</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        send_test_email("EARTHQUAKE ALERT:", html)
        
    elif choice == "2":
        print("\n📨 Sending HEAVY RAINFALL WARNING test email...")
        print(f"   Subject: HEAVY RAINFALL WARNING")
        html = generate_test_email_html("HEAVY_RAINFALL", alert_time)
        send_test_email("HEAVY RAINFALL WARNING", html)

    elif choice == "3":
        print("\n📨 Sending TROPICAL DEPRESSION / TYPHOON ALERTS test email...")
        print(f"   Subject: TROPICAL DEPRESSION / TYPHOON ALERTS")
        html = generate_test_email_html("TROPICAL_CYCLONE", alert_time)
        send_test_email("TROPICAL DEPRESSION / TYPHOON ALERTS", html)
        
    elif choice == "4":
        print("\n📨 Sending all test emails...")
        
        print("\n1️⃣ Sending EARTHQUAKE ALERT...")
        earthquake_html = f"""
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
                        <span class="label">Date &amp; Time:</span> 2026-03-26T14:30:15+08:00
                    </div>
                    <div class="info-row">
                        <span class="label">Magnitude:</span> 6.2
                    </div>
                    <div class="info-row">
                        <span class="label">Epicenter Location:</span> 15 km E of Cebu City
                    </div>
                    <div class="info-row">
                        <span class="label">Intensity Felt in Cebu:</span> Intensity IV
                    </div>
                    <div class="info-row">
                        <span class="label">Safety Precautions:</span>
                        <ul>
                            <li>Stay calm and be alert for possible aftershocks.</li>
                            <li>Check surroundings for hazards (falling objects, cracks).</li>
                            <li>Follow instructions from authorities.</li>
                        </ul>
                    </div>
                </div>
                <div class="footer">
                    <p><strong>Source:</strong> PHIVOLCS (Philippine Institute of Volcanology and Seismology)</p>
                    <p><strong>Alert Time:</strong> {alert_time}</p>
                    <p><em>This is an automated crisis alert.</em></p>
                </div>
            </div>
        </body>
        </html>
        """
        send_test_email("EARTHQUAKE ALERT:", earthquake_html)
        
        print("\n2️⃣ Sending HEAVY RAINFALL WARNING...")
        html2 = generate_test_email_html("HEAVY_RAINFALL", alert_time)
        send_test_email("HEAVY RAINFALL WARNING", html2)

        print("\n3️⃣ Sending TROPICAL DEPRESSION / TYPHOON ALERTS...")
        html3 = generate_test_email_html("TROPICAL_CYCLONE", alert_time)
        send_test_email("TROPICAL DEPRESSION / TYPHOON ALERTS", html3)
        
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
