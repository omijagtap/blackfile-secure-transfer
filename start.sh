#!/bin/bash
# Startup script for GitHub Codespaces

echo "🚀 Starting BlackFile Secure Transfer..."
echo ""

# Create .env file with credentials
cat > .env << 'EOF'
APP_SECRET=blackfile-secret-key-2024
FLASK_ENV=development

# Gmail SMTP Configuration
GMAIL_USER=omijagtap304@gmail.com
GMAIL_APP_PASSWORD=wxvcwzvnipmobhkk

# Security Settings
OTP_MAX_TRIES=3
LOCK_MIN=10
MAX_FILE_SIZE=10485760
EOF

echo "✅ Environment configured"
echo ""

# Run Flask app
echo "🌐 Starting Flask server..."
python app.py
