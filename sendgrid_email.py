"""
SendGrid Email Integration for BlackFile
Use this if SMTP is blocked on your hosting platform (like Render free tier)
"""

import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_email_sendgrid(to_email: str, subject: str, html_body: str):
    """
    Send email using SendGrid API (works on Render free tier)
    
    Setup:
    1. Sign up at https://sendgrid.com (Free: 100 emails/day)
    2. Create API Key: Settings → API Keys → Create API Key
    3. Add to Render Environment Variables:
       SENDGRID_API_KEY=your_api_key_here
       FROM_EMAIL=your_verified_sender@example.com
    """
    
    api_key = os.environ.get('SENDGRID_API_KEY')
    from_email = os.environ.get('FROM_EMAIL', 'noreply@blackfile.app')
    
    if not api_key:
        raise Exception("SENDGRID_API_KEY not configured. Please add it to environment variables.")
    
    try:
        message = Mail(
            from_email=from_email,
            to_emails=to_email,
            subject=subject,
            html_content=html_body
        )
        
        sg = SendGridAPIClient(api_key)
        response = sg.send(message)
        
        print(f"[SENDGRID] ✅ Email sent to {to_email} (Status: {response.status_code})")
        return True
        
    except Exception as e:
        print(f"[SENDGRID] ❌ Failed to send email: {e}")
        raise e


# Instructions to integrate into app.py:
# 
# 1. Install SendGrid:
#    Add to requirements.txt: sendgrid
#
# 2. Replace the send_email function call in app.py (line 573):
#    FROM: send_email(email, "Your BlackFile secure link", html)
#    TO:   send_email_sendgrid(email, "Your BlackFile secure link", html)
#
# 3. Add environment variables to Render:
#    SENDGRID_API_KEY=your_sendgrid_api_key
#    FROM_EMAIL=your_verified_sender@yourdomain.com
