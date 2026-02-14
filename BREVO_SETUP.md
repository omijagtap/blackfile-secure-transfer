# 🚀 BREVO SMTP SETUP - SIMPLE & WORKS ON RENDER

## ✅ What Changed:
- Switched from SendGrid to **Brevo SMTP**
- Brevo allows SMTP on free tier (300 emails/day)
- Works perfectly on Render free tier!

---

## 📋 STEP 1: Get Brevo API Key (3 minutes)

### A) Sign Up for Brevo
1. Go to: **https://app.brevo.com/account/register**
2. Fill in:
   - Email: `omijagtap304@gmail.com`
   - Password: (create a password)
3. Click **"Sign Up"**
4. **Verify your email** (check inbox)

### B) Get SMTP API Key
1. After login, go to: **https://app.brevo.com/settings/keys/api**
2. Click **"Generate a new API key"**
3. Name: `BlackFile SMTP`
4. **COPY THE API KEY** (starts with `xkeysib-`)
5. Save it somewhere safe!

### C) Verify Sender Email (Optional but Recommended)
1. Go to: **https://app.brevo.com/senders**
2. Add `omijagtap304@gmail.com` as sender
3. Verify the email

---

## 📋 STEP 2: Add to Render

Go to: **Render Dashboard → blackfile-app → Environment → "Add from .env"**

**COPY & PASTE THIS** (replace with your actual API key):

```
BREVO_API_KEY=YOUR_BREVO_API_KEY_HERE
```

**Example** (your key will look like this):
```
BREVO_API_KEY=xkeysib-abc123xyz789youractualkey
```

Then:
1. Click **"Add Variables"**
2. Click **"Save Changes"**
3. Wait 2-3 minutes for deployment

---

## ✅ DONE!

That's it! Your emails will now work on Render! 🎉

---

## 🎯 Why Brevo Works:

| Feature | Brevo SMTP |
|---------|------------|
| Free Tier | ✅ 300 emails/day |
| Works on Render | ✅ Yes! |
| Setup Time | ⚡ 3 minutes |
| Requires Credit Card | ❌ No |

---

## 🐛 Troubleshooting:

### Still seeing "EMAIL MOCK" in logs?
- Make sure you added `BREVO_API_KEY` to Render
- Make sure you clicked "Save Changes"
- Wait for Render to redeploy

### Authentication failed?
- Double-check your API key is correct
- Make sure you copied the full key (starts with `xkeysib-`)

---

**Last Updated**: 2026-02-14 (Switched to Brevo SMTP)
