#!/usr/bin/env python3
"""
Quick test script for Telegram notifications
"""
import os
import sys
from dotenv import load_dotenv

# Load .env
load_dotenv()

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from telegram_notifier import TelegramNotifier

def main():
    print("=" * 50)
    print("Telegram Notifier Test")
    print("=" * 50)
    
    notifier = TelegramNotifier()
    
    print(f"✓ Enabled: {notifier.enabled}")
    print(f"✓ Direct Telegram: {notifier.use_direct_telegram}")
    print(f"✓ Bot Token: {notifier.bot_token[:20]}..." if notifier.bot_token else "✗ No bot token")
    print(f"✓ Chat ID: {notifier.chat_id}" if notifier.chat_id else "✗ No chat ID")
    print(f"✓ Versus URL: {notifier.versus_url}")
    
    print("\n" + "=" * 50)
    print("Sending test alert...")
    print("=" * 50)
    
    success = notifier.send_test_alert()
    
    if success:
        print("\n✅ Test alert sent successfully!")
        print("Check your Telegram app for the message.")
    else:
        print("\n❌ Test alert failed!")
        print("Check the error messages above.")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
