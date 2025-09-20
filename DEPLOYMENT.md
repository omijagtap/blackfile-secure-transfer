# 🚀 RENDER.COM DEPLOYMENT GUIDE

## Step-by-Step Instructions

### 1. GitHub Setup
- Go to github.com
- Create new repository: `blackfile`
- Make it PUBLIC
- Don't add README

### 2. Push Code
```bash
git remote add origin https://github.com/YOUR_USERNAME/blackfile.git
git branch -M main
git push -u origin main
```

### 3. Render.com Setup
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New +" → "Web Service"
4. Connect GitHub → Select "blackfile" repo
5. Use these settings:

**Render Configuration:**
- Name: `blackfile-app`
- Environment: `Python 3`
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`
- Plan: **Free**

**Environment Variables (Add these in Render):**
```
APP_SECRET = your-super-secret-key-change-this
DEBUG = False
```

### 4. Deploy!
- Click "Create Web Service"
- Wait 3-5 minutes
- Get your live URL!

## Your App Will Be Live At:
`https://blackfile-app-xyz.onrender.com`

## Optional: Email Configuration
Add these to environment variables if you want email OTP:
```
SMTP_HOST = smtp.gmail.com
SMTP_PORT = 587
SMTP_USER = your-email@gmail.com
SMTP_PASS = your-app-password
FROM_EMAIL = noreply@yourapp.com
```

## Security Notes:
- Change APP_SECRET before deploying
- Never commit .env files with real secrets
- Use strong passwords for email accounts