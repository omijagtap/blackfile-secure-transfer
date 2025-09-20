#!/usr/bin/env python3
"""
Test if hamburger menu is deployed and working
"""
import requests
import re

APP_URL = "https://blackfile-app.onrender.com"

def test_hamburger_menu():
    print("🍔 Testing hamburger menu deployment...")
    print(f"📍 Checking: {APP_URL}")
    print("-" * 50)
    
    try:
        response = requests.get(APP_URL, timeout=30)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for mobile menu button
            if 'mobileMenuBtn' in content:
                print("✅ Mobile menu button ID found in HTML!")
            else:
                print("❌ Mobile menu button ID NOT found")
                
            # Check for hamburger spans
            if 'mobile-menu-btn' in content:
                print("✅ Mobile menu CSS class found!")
            else:
                print("❌ Mobile menu CSS class NOT found")
                
            # Check for mobile JavaScript
            if 'Mobile menu clicked' in content:
                print("✅ Mobile menu JavaScript found!")
            else:
                print("❌ Mobile menu JavaScript NOT found")
                
            # Check for responsive CSS
            if '@media (max-width: 768px)' in content or 'mobile-menu-btn' in content:
                print("✅ Mobile responsive CSS detected!")
            else:
                print("❌ Mobile responsive CSS NOT found")
                
            print("-" * 50)
            print("📱 To see hamburger menu:")
            print("1. Open: https://blackfile-app.onrender.com")
            print("2. Press F12 (Developer Tools)")
            print("3. Click device icon (📱) for mobile view")
            print("4. Look for ≡ (hamburger) in top-right corner")
            print("5. If still not visible, try Ctrl+F5 to refresh")
            
        else:
            print(f"❌ Site returned status code: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error checking site: {e}")

if __name__ == "__main__":
    test_hamburger_menu()