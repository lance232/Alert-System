================================================================================
                    PH ALERT SYSTEM - READ ME FIRST
================================================================================

WHAT THIS DOES:
  - Monitors PHIVOLCS for earthquakes
  - Monitors PAGASA for weather advisories (Cebu)
  - Automatically sends email alerts to your organization


QUICK START (5 Minutes):
================================================================================

STEP 1: Get Gmail App Password
-------------------------------
1. Go to: https://myaccount.google.com/apppasswords
2. Sign in to your Gmail account
3. Enable 2-Factor Authentication if needed
4. Create app password: App = "Mail", Device = "Windows Computer"
5. Copy the 16-character password (example: abcd efgh ijkl mnop)
   → REMOVE ALL SPACES: abcdefghijklmnop


STEP 2: Edit the .env File
-------------------------------
Open the file named:  .env

Change these 3 lines:

  EMAIL_ADDRESS=your-email@gmail.com
  EMAIL_APP_PASSWORD=your-16-char-password-here
  EMAIL_RECIPIENTS=colleague1@outlook.com,colleague2@outlook.com

Example:
  EMAIL_ADDRESS=alerts@gmail.com
  EMAIL_APP_PASSWORD=abcdefghijklmnop
  EMAIL_RECIPIENTS=john@outlook.com,mary@company.com,boss@outlook.com

Save the file!


STEP 3: Install Python Dependencies
-------------------------------
Open PowerShell in this folder and run:

  pip install -r requirements.txt


STEP 4: Run the System
-------------------------------


OPTION A - Manual Way (Two Terminals):
  
  Terminal 1 (Node.js API):
    cd phivolcs-earthquake-api-main
    npm start
  
  Terminal 2 (Python Alert System):
    python AlertSystem.py

  → Keep BOTH terminals open!


================================================================================
                              IMPORTANT INFO
================================================================================

Q: Do I need both servers running?
A: YES! The Node.js API fetches earthquake data, and the Python script 
   monitors both APIs and sends emails. Both must run together.

Q: Which terminal shows the alerts?
A: Terminal 2 (Python) shows all activity and email notifications.

Q: What happens when an alert is detected?
A: - Console shows the alert details
   - Email is sent to all recipients automatically
   - Recipients can check their inbox (including spam folder)

Q: How do I stop the system?
A: Press Ctrl+C in both terminal windows.


================================================================================
                            TROUBLESHOOTING
================================================================================

"Cannot connect to PHIVOLCS API"
  → Node.js server (Terminal 1) is not running. Start it first!

"Authentication failed" (Email)
  → Wrong app password. Use the 16-character Gmail app password, not your
    regular password. Remove ALL spaces from the password.

"No recipients configured"
  → Edit .env file and add email addresses to EMAIL_RECIPIENTS

Node.js not found
  → Install Node.js from: https://nodejs.org/

Python not found
  → Install Python from: https://python.org/


================================================================================
                            TESTING EMAILS
================================================================================

Want to test if emails work? Do this:

1. Stop the Python script (Ctrl+C in Terminal 2)
2. Delete the file: state_phivolcs_pagasa.json
3. In .env file, change: COLD_START_SUPPRESS=0
4. Run Python script again: python AlertSystem.py
5. Check your email (look in spam folder too)
6. Change back: COLD_START_SUPPRESS=1


================================================================================
                          ADDITIONAL DOCUMENTATION
================================================================================

For more details, see these files:

  HOW_TO_RUN.md      - Complete running instructions
  EMAIL_SETUP.md     - Detailed email configuration guide
  QUICK_START.md     - 5-minute setup guide


================================================================================
                              YOU'RE READY!
================================================================================

1. Edit .env with your Gmail credentials
2. Run: START_ALERT_SYSTEM.bat
3. Keep both windows open
4. Monitor for alerts!

Questions? Check HOW_TO_RUN.md for detailed instructions.
================================================================================
