# 📧 RENDER ENVIRONMENT VARIABLES - COPY & PASTE

## ✅ Updated Configuration for Render (Port 465 SSL)

Copy and paste this into Render's "Add from .env" section:

```
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USER=omijagtap304@gmail.com
SMTP_PASS=YOUR_16_CHAR_APP_PASSWORD_HERE
FROM_EMAIL=omijagtap304@gmail.com
```

---

## ⚠️ IMPORTANT: Replace App Password

**Before pasting**, replace `YOUR_16_CHAR_APP_PASSWORD_HERE` with your actual Gmail App Password.

### How to Get Gmail App Password:

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in with: `omijagtap304@gmail.com`
3. Create app password for "BlackFile"
4. Copy the 16-character password (remove spaces)
5. Replace `YOUR_16_CHAR_APP_PASSWORD_HERE` above

---

## 📝 How to Add to Render:

1. **Go to**: https://dashboard.render.com/
2. **Click** your service: `blackfile-app`
3. **Click** "Environment" tab (left sidebar)
4. **Click** "Add from .env" button
5. **Paste** the configuration above (with your real password)
6. **Click** "Add Variables"
7. **Click** "Save Changes" at the bottom
8. **Wait** 2-3 minutes for Render to redeploy

---

## 🔧 What Changed:

- **Port changed from 587 → 465** (SSL instead of TLS)
- **Why?** Render's free tier blocks port 587 but allows port 465
- **Code updated** to automatically try port 465 first, then fallback to 587

---

## ✅ After Deployment:

1. Wait for Render to finish deploying (check Render dashboard)
2. Go to your live website
3. Upload a test file
4. Enter your email
5. Check your inbox - email should arrive! 🎉

---

## 🐛 If Still Not Working:

Check Render logs for email status:
- Dashboard → Your Service → Logs
- Look for lines starting with `[EMAIL]`
- Should see: `✅ Email sent successfully via port 465`

---

**Last Updated**: 2026-02-14 (Fixed for Render network restrictions)
