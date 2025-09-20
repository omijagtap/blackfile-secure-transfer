#!/usr/bin/env python3
"""
Keep-alive script for Render.com free tier to prevent cold starts
This sends a simple ping to your app every 14 minutes to keep it warm
"""

import requests
import time
import os
from threading import Thread

# Your app URL - update this with your actual Render URL
APP_URL = "https://blackfile-app.onrender.com"

def ping_app():
    """Ping the app to keep it alive"""
    try:
        response = requests.get(f"{APP_URL}/", timeout=30)
        if response.status_code == 200:
            print(f"✅ Ping successful at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"⚠️ Ping returned {response.status_code}")
    except Exception as e:
        print(f"❌ Ping failed: {e}")

def keep_alive_loop():
    """Run the keep-alive loop"""
    print(f"🚀 Starting keep-alive for {APP_URL}")
    print("⏰ Pinging every 14 minutes to prevent cold starts...")
    
    while True:
        ping_app()
        # Sleep for 14 minutes (840 seconds)
        # Render free tier sleeps after 15 minutes of inactivity
        time.sleep(840)

if __name__ == "__main__":
    # Run keep-alive in background thread
    keep_alive_thread = Thread(target=keep_alive_loop, daemon=True)
    keep_alive_thread.start()
    
    # Keep the script running
    try:
        keep_alive_thread.join()
    except KeyboardInterrupt:
        print("\n🛑 Keep-alive stopped")