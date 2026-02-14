"""
Quick Email Test Script for BlackFile
Run this to verify your Gmail App Password is working correctly
"""

import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
FROM_EMAIL = os.environ.get("FROM_EMAIL", SMTP_USER)

def test_email():
    print("=" * 60)
    print("BlackFile Email Configuration Test")
    print("=" * 60)
    
    # Check if all variables are set
    print(f"\n📋 Configuration Check:")
    print(f"   SMTP_HOST: {SMTP_HOST or '❌ NOT SET'}")
    print(f"   SMTP_PORT: {SMTP_PORT}")
    print(f"   SMTP_USER: {SMTP_USER or '❌ NOT SET'}")
    print(f"   SMTP_PASS: {'✅ SET (' + str(len(SMTP_PASS)) + ' chars)' if SMTP_PASS else '❌ NOT SET'}")
    print(f"   FROM_EMAIL: {FROM_EMAIL or '❌ NOT SET'}")
    
    if not all([SMTP_HOST, SMTP_USER, SMTP_PASS]):
        print("\n❌ ERROR: Missing required email configuration!")
        print("   Please update your .env file with Gmail App Password")
        return False
    
    # Check for placeholder values
    if "PASTE_YOUR" in SMTP_PASS or "your-app-password" in SMTP_PASS:
        print("\n❌ ERROR: SMTP_PASS still contains placeholder value!")
        print("   Please replace with your actual Gmail App Password")
        return False
    
    print("\n📧 Attempting to send test email...")
    
    try:
        # Create test message
        msg = MIMEText("This is a test email from BlackFile. If you received this, your email configuration is working correctly! ✅", "plain")
        msg["Subject"] = "BlackFile Email Test - Success!"
        msg["From"] = FROM_EMAIL
        msg["To"] = SMTP_USER  # Send to yourself
        
        # Connect and send
        print(f"   Connecting to {SMTP_HOST}:{SMTP_PORT}...")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            print("   Starting TLS encryption...")
            server.starttls()
            print("   Logging in...")
            server.login(SMTP_USER, SMTP_PASS)
            print("   Sending email...")
            server.send_message(msg)
        
        print("\n✅ SUCCESS! Test email sent successfully!")
        print(f"   Check your inbox: {SMTP_USER}")
        print("\n🎉 Your email configuration is working correctly!")
        return True
        
    except smtplib.SMTPAuthenticationError as e:
        print(f"\n❌ AUTHENTICATION FAILED!")
        print(f"   Error: {e}")
        print("\n💡 Possible solutions:")
        print("   1. Verify your Gmail App Password is correct (16 characters, no spaces)")
        print("   2. Make sure 2-Step Verification is enabled on your Google Account")
        print("   3. Generate a new App Password at: https://myaccount.google.com/apppasswords")
        return False
        
    except smtplib.SMTPException as e:
        print(f"\n❌ SMTP ERROR!")
        print(f"   Error: {e}")
        return False
        
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR!")
        print(f"   Error: {e}")
        return False

if __name__ == "__main__":
    test_email()
    print("\n" + "=" * 60)
