#!/usr/bin/env python3
"""
Check if the performance optimizations are live on Render
"""

import requests
import time

APP_URL = "https://blackfile-app.onrender.com"

def check_deployment():
    print("🔍 Checking BlackFile deployment status...")
    print(f"📍 URL: {APP_URL}")
    print("-" * 50)
    
    try:
        # Check if site is accessible
        response = requests.get(APP_URL, timeout=30)
        
        if response.status_code == 200:
            print("✅ Site is LIVE and accessible!")
            
            # Check for performance optimizations in response
            content = response.text
            
            # Check for caching headers (our optimization)
            cache_control = response.headers.get('Cache-Control', '')
            if 'max-age=300' in cache_control:
                print("✅ Caching optimization detected!")
            else:
                print("⏳ Caching optimization not yet deployed")
            
            # Check for modern UI elements
            if 'BlackFile' in content and 'Secure File Transfer' in content:
                print("✅ Modern UI is live!")
            else:
                print("⚠️ Modern UI not detected")
                
            # Check response time
            response_time = response.elapsed.total_seconds()
            print(f"⚡ Response time: {response_time:.2f} seconds")
            
            if response_time < 2:
                print("✅ Fast response time - optimizations working!")
            elif response_time < 5:
                print("⚡ Good response time")
            else:
                print("🐌 Slow response - might be cold start")
                
        else:
            print(f"❌ Site returned {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("⏳ Site is loading (might be cold start)")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("-" * 50)
    print("🎯 Next steps:")
    print("1. Check Render dashboard for deployment status")
    print("2. Visit your site to test the optimizations")
    print(f"3. Go to: {APP_URL}")

if __name__ == "__main__":
    check_deployment()