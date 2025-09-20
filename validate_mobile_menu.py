#!/usr/bin/env python3
"""
Simple Mobile Menu Validation for BlackFile
Tests if mobile menu elements and JavaScript are properly loaded
"""

import requests
import re

def validate_mobile_menu():
    print("🔍 Validating BlackFile Mobile Menu...")
    print("=" * 50)
    
    url = "https://blackfile-app.onrender.com"
    
    try:
        response = requests.get(url, timeout=30)
        html = response.text
        
        print(f"✅ Site accessible: {response.status_code}")
        print(f"📄 Page size: {len(html)} characters")
        
        # Check for mobile menu elements
        checks = [
            ("Mobile menu button HTML", "mobileMenuBtn" in html),
            ("Mobile menu CSS class", "mobile-menu-btn" in html),
            ("Navigation menu", "nav-menu" in html),
            ("Modern CSS loading", "modern-style.css" in html),
            ("Mobile JS toggle function", "toggleMobileMenu" in html),
            ("Mobile event listeners", "addEventListener" in html and "mobileMenuBtn" in html),
            ("Logo image", "logo-horizontal.png" in html or "logo.png" in html),
            ("Hamburger spans", html.count("<span></span>") >= 3),
            ("Fallback text button", "mobileMenuText" in html),
            ("Console logging", "console.log" in html and "mobile menu" in html.lower()),
        ]
        
        print("\n🔍 Mobile Menu Component Checks:")
        print("-" * 40)
        
        passed = 0
        total = len(checks)
        
        for description, result in checks:
            status = "✅" if result else "❌"
            print(f"{status} {description}")
            if result:
                passed += 1
        
        print(f"\n📊 Results: {passed}/{total} checks passed ({passed/total*100:.1f}%)")
        
        if passed >= 8:  # At least 80% should pass
            print("\n🎉 Mobile menu should be working!")
            print("\n📱 Test Instructions:")
            print("1. Open https://blackfile-app.onrender.com on your phone")
            print("2. Or use desktop browser Developer Tools (F12)")
            print("3. Switch to mobile view (phone icon)")
            print("4. Look for hamburger menu (≡) in top-right")
            print("5. Click/tap it to toggle navigation")
            
            if "MENU" in html:
                print("\n🔄 Fallback: If hamburger doesn't work, look for 'MENU' text button")
        else:
            print("\n⚠️ Mobile menu may not work properly")
            
        # Extract some key JavaScript parts for debugging
        print("\n🔧 JavaScript Debug Info:")
        if "toggleMobileMenu" in html:
            print("✅ Toggle function found")
        if "mobileMenuBtn.addEventListener" in html:
            print("✅ Event listeners attached")
        if "console.log" in html and "mobile menu" in html.lower():
            print("✅ Debug logging enabled")
            
    except Exception as e:
        print(f"❌ Error accessing site: {e}")

if __name__ == "__main__":
    validate_mobile_menu()