# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 2: Get Your Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in to your Gmail account
3. Create an app password:
   - App: **Mail**
   - Device: **Windows Computer**
4. **Copy the 16-character password** (example: `abcd efgh ijkl mnop`)

> ⚠️ **Important**: You need 2-Factor Authentication enabled first!  
> Enable it here: https://myaccount.google.com/signinoptions/two-step-verification

### Step 3: Create Your `.env` File

Create a new file named `.env` in your project folder with this content:

```bash
# Gmail Configuration
EMAIL_ADDRESS=your-gmail@gmail.com
EMAIL_APP_PASSWORD=abcdefghijklmnop
EMAIL_RECIPIENTS=colleague1@outlook.com,colleague2@outlook.com,boss@company.com

# Optional Settings
EMAIL_FROM_NAME=NCR Alert System
EMAIL_ENABLED=1
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587

# Alert System Settings
PHIVOLCS_API_URL=http://localhost:3001/api/earthquakes
POLL_INTERVAL_SEC=30
COLD_START_SUPPRESS=1

# Smart refresh settings (advanced - leave as default)
SMART_REFRESH=1
STALE_MAX_SEC=60
NO_NEW_CYCLES_BEFORE_REFRESH=1
MIN_REFRESH_GAP_SEC=25

# Cold start suppression (1=don't send alerts for old events on first run)
COLD_START_SUPPRESS=1

# Maximum event age in minutes (0=no limit, only alert for recent events)
MAX_EVENT_AGE_MIN=0

# Maximum pending quake alerts kept in queue (latest N events)
MAX_PENDING_QUAKE_EVENTS=5

# USGS secondary confirmation settings
USGS_CONFIRMATION_ENABLED=1
USGS_MATCH_TIME_WINDOW_MIN=20
USGS_MATCH_MAX_DISTANCE_KM=180
USGS_MATCH_MAG_TOLERANCE=0.8

# State file location (tracks which alerts have been sent)
STATE_FILE=state_phivolcs_pagasa.json

```

**Replace:**
- `your-gmail@gmail.com` → Your Gmail address
- `abcdefghijklmnop` → Your 16-character app password (remove spaces)
- `colleague1@outlook.com,colleague2@outlook.com` → Your organization's email addresses

### Step 4: Start Your PHIVOLCS API Server

In a separate terminal:
```powershell
cd phivolcs-earthquake-api-main
npm install
npm start
```

The API should run on http://localhost:3001

### Step 5: Run the Alert System

```powershell
python AlertSystem.py
```

You should see:
```
======================================================================
NCR Alert System (PHIVOLCS + PAGASA) with Email Integration
======================================================================
Poll Interval      : 30s
PHIVOLCS API       : http://localhost:3001/api/earthquakes
Smart Refresh      : Enabled
Cold Start Suppress: Yes

Email Configuration:
  Enabled          : Yes
  SMTP Host        : smtp.gmail.com:587
  From Address     : your-gmail@gmail.com
  Recipients       : colleague1@outlook.com, colleague2@outlook.com
  Authentication   : App Password Configured
======================================================================

Starting monitoring...
```

Earthquake alerts are Cebu-only and trigger only at magnitude **greater than 4.0**.
If one cycle fails, unsent Cebu earthquake alerts are queued and retried in the next cycle.
To avoid restart spam from old backlog, the queue keeps only the **latest 5 qualifying events** by default.

---

## ✅ Testing Email Functionality

To test if emails are working without waiting for a real alert:

1. **Delete the state file** (resets what's been seen):
   ```powershell
   Remove-Item state_phivolcs_pagasa.json -ErrorAction SilentlyContinue
   ```

2. **Temporarily disable cold start suppression**:
   In your `.env` file:
   ```bash
   COLD_START_SUPPRESS=0
   ```

3. **Run the script**:
   ```powershell
   python AlertSystem.py
   ```

4. **Check your email** (including spam folder) - you should receive alerts for the latest earthquake/advisory

5. **Re-enable cold start suppression**:
   ```bash
   COLD_START_SUPPRESS=1
   ```

---

## 📧 What Emails Look Like

### 🚨 Earthquake Alert Email
**Subject:** `🚨 EARTHQUAKE ALERT: Magnitude 4.5 - 10 km NW of Cebu City`

Professional HTML email with:
- Earthquake time
- Magnitude
- Depth
- Exact location
- Coordinates
- Source attribution

### ⚠️ Weather Advisory Email
**Subject:** `⚠️ WEATHER ADVISORY: 1 New Cebu Advisory - PAGASA`

Professional HTML email with:
- Advisory type and number
- Issued time
- Affected areas in Cebu
- Full advisory text
- Source attribution

---

## 🔧 Troubleshooting

### "Authentication failed"
- ❌ Using regular password → ✅ Use app password
- ❌ Spaces in app password → ✅ Remove all spaces: `abcdefghijklmnop`
- ❌ 2FA not enabled → ✅ Enable 2-Factor Authentication first

### "No recipients configured"
- Check `EMAIL_RECIPIENTS` in `.env` file
- Must be comma-separated: `email1@outlook.com,email2@company.com`
- No spaces around commas

### Emails not received
- Check spam/junk folder
- Verify Gmail account has sending permissions
- Check console for `[Email] ✓ Sent to X recipient(s)` message

### Cannot connect to PHIVOLCS API
- Ensure Node.js server is running: `npm start` in `phivolcs-earthquake-api-main/`
- Check if http://localhost:3001/api/earthquakes is accessible in browser

---

## 🎯 Production Deployment

When running 24/7:

1. **Run in background** (Windows):
   ```powershell
   Start-Process python -ArgumentList "AlertSystem.py" -WindowStyle Hidden
   ```

2. **Or use Windows Task Scheduler**:
   - Create a new task
   - Trigger: At system startup
   - Action: Start `python.exe` with argument `AlertSystem.py`
   - Set working directory to your project folder

3. **Monitor logs**:
   - Console output shows all activity
   - Consider redirecting to a log file:
     ```powershell
     python AlertSystem.py >> alerts.log 2>&1
     ```

---

## 📝 Environment Variables Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `EMAIL_ADDRESS` | *(required)* | Your Gmail address |
| `EMAIL_APP_PASSWORD` | *(required)* | 16-char Gmail app password |
| `EMAIL_RECIPIENTS` | *(required)* | Comma-separated recipient emails |
| `EMAIL_FROM_NAME` | NCR Alert System | Display name in emails |
| `EMAIL_ENABLED` | 1 | 1=enabled, 0=disabled |
| `SMTP_HOST` | smtp.gmail.com | Gmail SMTP server |
| `SMTP_PORT` | 587 | SMTP port (TLS) |
| `PHIVOLCS_API_URL` | http://localhost:3001/api/earthquakes | PHIVOLCS API endpoint |
| `POLL_INTERVAL_SEC` | 30 | Check interval in seconds |
| `COLD_START_SUPPRESS` | 1 | Suppress alerts on first run |
| `MAX_EVENT_AGE_MIN` | 0 | Only alert for events within X minutes (0=unlimited) |
| `MAX_PENDING_QUAKE_EVENTS` | 5 | Keep only latest N qualifying queued quake events |
| `USGS_CONFIRMATION_ENABLED` | 1 | Enable USGS secondary confirmation metadata |
| `USGS_MATCH_TIME_WINDOW_MIN` | 20 | Max time difference for PHIVOLCS-USGS match |
| `USGS_MATCH_MAX_DISTANCE_KM` | 180 | Max epicenter distance for PHIVOLCS-USGS match |
| `USGS_MATCH_MAG_TOLERANCE` | 0.8 | Max magnitude difference for PHIVOLCS-USGS match |

---

## 💡 Tips

- **Gmail sending limit**: 500 emails/day for regular accounts
- **Add distribution list**: Instead of listing 50 emails, use a group email
- **Customize email templates**: Edit `formatEarthquakeEmail()` and `formatPagasaEmail()` functions
- **Backup state file**: `state_phivolcs_pagasa.json` tracks what's been sent

---

## 📚 Need More Help?

See [EMAIL_SETUP.md](EMAIL_SETUP.md) for detailed configuration guide.
