#!/usr/bin/env python3
"""
Test the new simple mobile menu approach
"""
import requests
import time

APP_URL = "https://blackfile-app.onrender.com"

def test_new_mobile_menu():
    print("📱 Testing NEW SIMPLE mobile menu...")
    print(f"📍 URL: {APP_URL}")
    print("=" * 60)
    
    try:
        # Wait a moment for deployment
        print("⏳ Waiting for deployment...")
        time.sleep(10)
        
        response = requests.get(APP_URL, timeout=30)
        
        if response.status_code == 200:
            content = response.text
            
            # Check for new simple approach
            tests = [
                ("Mobile menu button", 'mobileMenuBtn' in content),
                ("Fallback text button", 'mobileMenuText' in content),
                ("Simple CSS approach", 'display: none' in content and '.nav-menu.active' in content),
                ("Touch event support", 'touchstart' in content),
                ("Unified toggle function", 'toggleMobileMenu' in content),
            ]
            
            all_passed = True
            for test_name, result in tests:
                status = "✅ PASS" if result else "❌ FAIL"
                print(f"{status} {test_name}")
                if not result:
                    all_passed = False
            
            print("=" * 60)
            
            if all_passed:
                print("🎉 ALL TESTS PASSED!")
                print("📱 The new mobile menu should work on your phone!")
                print()
                print("🧪 TO TEST ON YOUR PHONE:")
                print("1. Open your phone browser")
                print("2. Go to: https://blackfile-app.onrender.com")
                print("3. Look for hamburger menu (≡) or 'MENU' button")
                print("4. Tap it - navigation should appear!")
                print("5. Check browser console (if possible) for debug messages")
                print()
                print("📋 DEBUG INFO:")
                print("- Console will show: '🍔 MOBILE MENU TOGGLE CALLED'")
                print("- Console will show: '✅ Menu OPENED' or '❌ Menu CLOSED'")
                print("- On small screens, you'll see 'MENU' text instead of ≡")
            else:
                print("⚠️  Some tests failed - checking deployment status...")
                
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Try again in a few minutes - deployment might still be in progress")

if __name__ == "__main__":
    test_new_mobile_menu()