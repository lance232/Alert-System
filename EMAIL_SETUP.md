# Email Integration Setup Guide

## Overview
Your alert system now sends automatic emails via **Gmail SMTP** to Outlook recipients when:
- A new earthquake is detected from PHIVOLCS
- A new weather advisory for Cebu is detected from PAGASA

## Features Added
✅ HTML-formatted email alerts with professional styling  
✅ Gmail SMTP with app password authentication  
✅ Support for multiple recipients (Outlook, Gmail, etc.)  
✅ Separate emails for earthquakes and weather advisories  
✅ Email delivery confirmation in console logs  
✅ Error handling and retry logic  

---

## Setup Steps

### 1. Generate Gmail App Password

Since you're using Gmail to send emails, you need to create an **App Password** (NOT your regular Gmail password).

**Steps:**
1. Go to your Google Account: https://myaccount.google.com/
2. Enable **2-Factor Authentication** (required for app passwords)
   - Go to Security → 2-Step Verification → Turn on
3. Generate an App Password:
   - Go to: https://myaccount.google.com/apppasswords
   - Select "Mail" as the app
   - Select "Windows Computer" as the device
   - Click "Generate"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

**Important:** Save this password securely - you won't be able to see it again!

### 2. Configure Environment Variables

Create a `.env` file in your project directory (copy from `.env.example`):

```bash
# Copy the example file
cp .env.example .env
```

Edit `.env` and fill in your details:

```bash
# Your Gmail address
EMAIL_ADDRESS=yourname@gmail.com

# The 16-character app password from step 1
EMAIL_APP_PASSWORD=abcdefghijklmnop

# Recipients (comma-separated, can be Outlook/Gmail/any email)
EMAIL_RECIPIENTS=user1@outlook.com,user2@company.com,admin@yourorg.com

# Optional: Customize sender name
EMAIL_FROM_NAME=PH Alert System - Your Organization
```

### 3. Install Python Dependencies

Ensure you have the required packages:

```bash
pip install requests beautifulsoup4 python-dateutil lxml
```

### 4. Load Environment Variables

#### Option A: Using python-dotenv (Recommended)

Install dotenv:
```bash
pip install python-dotenv
```

Add to the top of `AlertSystem.py` (after imports):
```python
from dotenv import load_dotenv
load_dotenv()  # Load .env file
```

#### Option B: Set manually in PowerShell

```powershell
$env:EMAIL_ADDRESS="yourname@gmail.com"
$env:EMAIL_APP_PASSWORD="abcdefghijklmnop"
$env:EMAIL_RECIPIENTS="user1@outlook.com,user2@outlook.com"
```

### 5. Run the Alert System

```bash
python AlertSystem.py
```

---

## Email Configuration Reference

| Variable | Description | Example |
|----------|-------------|---------|
| `SMTP_HOST` | Gmail SMTP server | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (TLS) | `587` |
| `EMAIL_ADDRESS` | Your Gmail address | `alerts@gmail.com` |
| `EMAIL_APP_PASSWORD` | Gmail app password | `abcdefghijklmnop` |
| `EMAIL_RECIPIENTS` | Comma-separated recipients | `user1@outlook.com,user2@outlook.com` |
| `EMAIL_FROM_NAME` | Display name | `PH Alert System` |
| `EMAIL_ENABLED` | Enable/disable emails | `1` (enabled) or `0` (disabled) |

---

## Email Format Examples

### Earthquake Alert
```
Subject: 🚨 EARTHQUAKE ALERT: Magnitude 4.5 - 10 km NW of Cebu City

Content:
- Time
- Magnitude
- Depth
- Location
- Coordinates
- Source: PHIVOLCS
```

### Weather Advisory
```
Subject: ⚠️ WEATHER ADVISORY: 1 New Cebu Advisory - PAGASA

Content:
- Advisory type and number
- Issued time
- Affected areas in Cebu
- Full advisory text
- Source: PAGASA Visayas PRSD
```

---

## Troubleshooting

### "Authentication failed" Error
❌ **Problem:** Cannot authenticate with Gmail  
✅ **Solutions:**
- Verify your Gmail address is correct
- Ensure you're using the **app password**, NOT your regular password
- Check that 2-Factor Authentication is enabled on your Google account
- Generate a new app password if the old one isn't working

### Emails Not Sending
❌ **Problem:** No emails received  
✅ **Solutions:**
- Check `EMAIL_ENABLED=1` in your environment
- Verify `EMAIL_RECIPIENTS` has valid addresses
- Check your spam/junk folder
- Look for error messages in the console output

### "Connection timed out"
❌ **Problem:** Cannot connect to Gmail SMTP  
✅ **Solutions:**
- Check your internet connection
- Verify firewall isn't blocking port 587
- Try using port 465 (SSL) instead:
  ```bash
  SMTP_PORT=465
  # Also update code to use SMTP_SSL instead of SMTP
  ```

### Testing Email Without Waiting for Alerts
To test email functionality, you can temporarily:
1. Delete `state_phivolcs_pagasa.json` to reset state
2. Set `COLD_START_SUPPRESS=0` to send alerts on startup
3. Run the script - it will send emails for the latest events

---

## Security Best Practices

1. **Never commit `.env` file to Git**
   - Add `.env` to your `.gitignore` file
   - Share `.env.example` instead

2. **Protect your app password**
   - Don't share it publicly
   - Don't hardcode it in scripts
   - Rotate it periodically

3. **Limit recipient list**
   - Only add necessary email addresses
   - Use distribution lists if sending to many people

4. **Monitor usage**
   - Gmail has sending limits (500 emails/day)
   - For high volume, consider using a dedicated email service

---

## Advanced Configuration

### Using a Different SMTP Server

If you want to use your organization's SMTP instead of Gmail:

```bash
# Example: Office 365
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
EMAIL_ADDRESS=your-org-email@company.com
EMAIL_APP_PASSWORD=your-password-or-app-password
```

### Customizing Email Templates

Edit the functions in `AlertSystem.py`:
- `formatEarthquakeEmail()` - Customize earthquake alert format
- `formatPagasaEmail()` - Customize weather advisory format

### Adding More Recipients Later

Just update the `EMAIL_RECIPIENTS` variable:
```bash
EMAIL_RECIPIENTS=old@email.com,new1@email.com,new2@email.com
```

---

## Console Output

When emails are sent, you'll see confirmation:
```
[2026-03-09T10:30:45+08:00] NEW items found → Quake
=== PH Alerts – New items @ 2026-03-09T10:30:45+08:00 ===

Earthquake (PHIVOLCS)
----------------------------------------------------
...earthquake details...

[2026-03-09T10:30:45+08:00] Sending email alerts...
  [Email] ✓ Sent to 3 recipient(s)
```

---

## Support

If you encounter any issues:
1. Check the console for error messages
2. Verify all environment variables are set correctly
3. Test your Gmail credentials manually
4. Check Gmail's security settings

For Gmail app password issues: https://support.google.com/accounts/answer/185833
