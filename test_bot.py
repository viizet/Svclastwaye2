#!/usr/bin/env python3
"""
Test script to verify bot components work independently
"""

import sys
import os

def test_imports():
    """Test if all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
        print("✅ Telegram imports successful")
    except ImportError as e:
        print(f"❌ Telegram import failed: {e}")
        return False
    
    try:
        import cairosvg
        print("✅ CairoSVG import successful")
    except ImportError as e:
        print(f"❌ CairoSVG import failed: {e}")
        return False
    
    try:
        from PIL import Image
        print("✅ Pillow import successful")
    except ImportError as e:
        print(f"❌ Pillow import failed: {e}")
        return False
    
    try:
        from database import Database
        from utils import SVGValidator, TGSConverter
        from config import Config
        print("✅ Custom modules import successful")
    except ImportError as e:
        print(f"❌ Custom module import failed: {e}")
        return False
    
    return True

def test_database():
    """Test database functionality"""
    print("\nTesting database...")
    
    try:
        from database import Database
        db = Database("test_bot.db")
        
        # Test adding a user
        db.add_user(12345, "testuser", "Test", "User")
        
        # Test checking user count
        count = db.get_user_count()
        print(f"✅ Database operations successful - Users: {count}")
        
        # Clean up test database
        if os.path.exists("test_bot.db"):
            os.remove("test_bot.db")
        
        return True
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False

def test_svg_validator():
    """Test SVG validation"""
    print("\nTesting SVG validation...")
    
    try:
        from utils import SVGValidator
        validator = SVGValidator()
        
        # Create a test SVG
        test_svg = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="512" height="512" xmlns="http://www.w3.org/2000/svg">
  <circle cx="256" cy="256" r="100" fill="red"/>
</svg>'''.encode('utf-8')
        
        is_valid, message = validator.validate_svg(test_svg)
        print(f"✅ SVG validation successful - Valid: {is_valid}, Message: {message}")
        return True
    except Exception as e:
        print(f"❌ SVG validation test failed: {e}")
        return False

def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config import Config
        config = Config()
        print(f"✅ Configuration loaded - Token present: {'Yes' if config.BOT_TOKEN else 'No'}")
        print(f"✅ Admin IDs: {config.ADMIN_IDS}")
        return True
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 SVGToTGS Bot Component Tests\n")
    
    tests = [
        test_imports,
        test_database, 
        test_svg_validator,
        test_config
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                print("❌ Test failed")
        except Exception as e:
            print(f"❌ Test error: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All components working! Bot is ready for deployment.")
        print("\nTo use the bot:")
        print("1. Get a valid bot token from @BotFather on Telegram")
        print("2. Update the token in config.py")
        print("3. Run: python main.py")
    else:
        print("❌ Some components failed. Check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)