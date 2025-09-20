@echo off
echo =================================
echo BlackFile Deployment Setup
echo =================================

echo.
echo Step 1: Setting up Git remote...
echo REPLACE 'YOUR_USERNAME' with your actual GitHub username!
echo.

echo git remote add origin https://github.com/YOUR_USERNAME/blackfile.git
echo git branch -M main  
echo git push -u origin main

echo.
echo =================================
echo After running the above commands:
echo =================================
echo 1. Go to render.com
echo 2. Sign up with GitHub
echo 3. Create new Web Service
echo 4. Select your blackfile repository
echo 5. Use these settings:
echo    - Build Command: pip install -r requirements.txt
echo    - Start Command: gunicorn app:app
echo    - Add Environment Variable: APP_SECRET=your-secret-key
echo.
echo Your app will be live at: https://blackfile-xyz.onrender.com
echo =================================

pause