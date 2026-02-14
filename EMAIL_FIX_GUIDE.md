# 🔧 Email Configuration Fix Guide

## Problem Identified
Your `.env` file has a **placeholder Gmail App Password** instead of the actual password. This is why emails aren't being sent.

---

## ✅ Complete Fix (Follow in Order)

### Step 1: Generate Gmail App Password

1. **Visit**: https://myaccount.google.com/apppasswords
2. **Sign in** with: `omijagtap304@gmail.com`
3. **If you see "App passwords"**:
   - Click "Select app" → Choose "Mail" or "Other (Custom name)"
   - Type: "BlackFile Secure Transfer"
   - Click "Generate"
   - **COPY the 16-character password** (e.g., `abcd efgh ijkl mnop`)

4. **If you DON'T see "App passwords"**:
   - You need to enable **2-Step Verification** first
   - Go to: https://myaccount.google.com/security
   - Enable "2-Step Verification"
   - Then return to step 1

---

### Step 2: Update Local `.env` File

1. Open `.env` file in your project
2. Find this line:
   ```
   SMTP_PASS=PASTE_YOUR_16_CHAR_APP_PASSWORD_HERE
   ```
3. Replace with your actual app password (remove all spaces):
   ```
   SMTP_PASS=abcdefghijklmnop
   ```
4. Save the file

---

### Step 3: Test Email Configuration Locally

Run the test script to verify your configuration:

```bash
python test_email.py
```

**Expected Output**:
```
✅ SUCCESS! Test email sent successfully!
Check your inbox: omijagtap304@gmail.com
```

**If you see errors**, the script will tell you exactly what's wrong.

---

### Step 4: Update Render Environment Variables ⚠️ CRITICAL

Your Render deployment is **missing email configuration**. You MUST add these:

1. **Go to Render Dashboard**: https://dashboard.render.com/
2. **Select your service**: `blackfile-app`
3. **Click "Environment"** tab (left sidebar)
4. **Add these environment variables** (click "Add Environment Variable" for each):

   | Key | Value |
   |-----|-------|
   | `SMTP_HOST` | `smtp.gmail.com` |
   | `SMTP_PORT` | `587` |
   | `SMTP_USER` | `omijagtap304@gmail.com` |
   | `SMTP_PASS` | `[Your 16-char App Password - NO SPACES]` |
   | `FROM_EMAIL` | `omijagtap304@gmail.com` |

5. **Click "Save Changes"** at the bottom
6. Render will automatically redeploy (takes 2-3 minutes)

---

### Step 5: Verify on Render

After Render redeploys:

1. Go to your live website
2. Upload a test file
3. Enter your email: `omijagtap304@gmail.com`
4. Click "Send Secure File"
5. **Check your inbox** - you should receive the email with OTP and download link

---

## 🐛 Troubleshooting

### "Authentication Failed" Error
- **Cause**: Wrong App Password or 2-Step Verification not enabled
- **Fix**: 
  1. Verify 2-Step Verification is ON
  2. Generate a NEW App Password
  3. Update `.env` and Render environment variables

### "Connection Timeout" Error
- **Cause**: Firewall or network blocking SMTP port 587
- **Fix**: 
  1. Try using port `465` instead (SSL)
  2. Update `SMTP_PORT=465` in both `.env` and Render

### Email Still Not Sending on Render
- **Cause**: Environment variables not saved or deployment failed
- **Fix**:
  1. Go to Render Dashboard → Environment tab
  2. Verify ALL 5 email variables are present
  3. Click "Manual Deploy" → "Deploy latest commit"

### "File sent successfully" but no email received
- **Cause**: Email might be in Spam folder
- **Fix**: 
  1. Check your Spam/Junk folder
  2. Mark as "Not Spam" if found
  3. Add `omijagtap304@gmail.com` to your contacts

---

## 📝 Quick Checklist

- [ ] Generated Gmail App Password
- [ ] Updated `.env` file with actual password (no spaces)
- [ ] Ran `python test_email.py` successfully
- [ ] Added all 5 environment variables to Render
- [ ] Saved changes on Render (auto-redeploy triggered)
- [ ] Tested file upload on live website
- [ ] Received email successfully

---

## 🎯 Next Steps

Once all steps are complete:

1. **Test locally**: Run your Flask app and send a test file
2. **Test on Render**: Upload a file on your live website
3. **Verify email delivery**: Check inbox for OTP email

---

## 📞 Need Help?

If you're still having issues after following all steps:

1. Run `python test_email.py` and share the output
2. Check Render logs: Dashboard → Logs tab
3. Look for any error messages starting with `[EMAIL]`

---

**Last Updated**: 2026-02-14
