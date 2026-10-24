#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script cho WhatsApp Personal notification
Dùng cho tài khoản WhatsApp cá nhân
"""

import os
import sys
import argparse
from datetime import datetime

# Thêm path để import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.notification.whatsapp_personal_notifier import WhatsAppPersonalNotifier, WhatsAppGroupNotifier


def test_personal_whatsapp(phone_number: str, message: str, method: str = "pywhatkit"):
    """Test gửi tin nhắn WhatsApp cá nhân"""
    print(f"\n[*] Testing WhatsApp Personal with {method}...")
    print(f"[*] Target: {phone_number}")
    print(f"[*] Message: {message}")
    
    try:
        # Khởi tạo notifier
        notifier = WhatsAppPersonalNotifier(phone_number, method=method)
        
        # Gửi message
        print(f"\n[+] Sending message...")
        success = notifier.send_message(message)
        
        if success:
            print("[✓] Message sent successfully!")
        else:
            print("[-] Failed to send message!")
            
        # Cleanup
        if hasattr(notifier, 'close'):
            notifier.close()
            
        return success
        
    except Exception as e:
        print(f"[-] Error: {str(e)}")
        return False


def test_group_whatsapp(group_name: str, message: str):
    """Test gửi tin nhắn đến WhatsApp Group"""
    print(f"\n[*] Testing WhatsApp Group...")
    print(f"[*] Group: {group_name}")
    print(f"[*] Message: {message}")
    
    try:
        # Khởi tạo group notifier
        notifier = WhatsAppGroupNotifier(group_name)
        
        # Gửi message
        print(f"\n[+] Sending message to group...")
        success = notifier.send_message(message)
        
        if success:
            print("[✓] Message sent to group successfully!")
        else:
            print("[-] Failed to send message to group!")
            
        # Cleanup
        notifier.close()
        
        return success
        
    except Exception as e:
        print(f"[-] Error: {str(e)}")
        return False


def setup_instructions():
    """Hiển thị hướng dẫn setup"""
    print("""
========================================
SETUP INSTRUCTIONS
========================================

1. Cài đặt dependencies:
   
   # Cho phương thức pywhatkit (đơn giản):
   pip install pywhatkit
   
   # Cho phương thức selenium (nâng cao):
   pip install selenium
   pip install webdriver-manager
   
2. Chuẩn bị:
   
   Với pywhatkit:
   - Đảm bảo WhatsApp Web đã login trên browser mặc định
   - Tool sẽ tự động mở browser và gửi tin
   
   Với selenium:
   - Lần đầu chạy cần scan QR code
   - Session sẽ được lưu cho lần sau

3. Format số điện thoại:
   - Phải có country code: +84912345678
   - Không có khoảng trắng hay dấu gạch

4. Lưu ý:
   - pywhatkit: Đơn giản nhưng mở browser mỗi lần
   - selenium: Phức tạp hơn nhưng linh hoạt
   - Group chỉ hoạt động với selenium
   
========================================
    """)


def main():
    parser = argparse.ArgumentParser(
        description='Test WhatsApp Personal notification',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Hiển thị hướng dẫn setup
  python test_whatsapp_personal.py --setup
  
  # Test với pywhatkit (đơn giản)
  python test_whatsapp_personal.py -p +84912345678 -m "Hello from Sharingan!"
  
  # Test với selenium (nâng cao)
  python test_whatsapp_personal.py -p +84912345678 -m "Test message" --selenium
  
  # Test gửi đến group
  python test_whatsapp_personal.py -g "Security Team" -m "Scan completed!"
  
  # Test với timestamp
  python test_whatsapp_personal.py -p +84912345678 -m "Test message" --add-timestamp
        """
    )
    
    parser.add_argument('--setup',
                       action='store_true',
                       help='Show setup instructions')
    
    parser.add_argument('-p', '--phone',
                       help='Phone number with country code (e.g., +84912345678)')
    
    parser.add_argument('-g', '--group',
                       help='Group name to send message')
    
    parser.add_argument('-m', '--message',
                       help='Message to send')
    
    parser.add_argument('--selenium',
                       action='store_true',
                       help='Use selenium method instead of pywhatkit')
    
    parser.add_argument('--add-timestamp',
                       action='store_true',
                       help='Add timestamp to message')
    
    args = parser.parse_args()
    
    # Show setup instructions
    if args.setup:
        setup_instructions()
        return 0
        
    # Validate input
    if not args.message:
        parser.error("Message is required (-m)")
        
    if not args.phone and not args.group:
        parser.error("Either phone number (-p) or group name (-g) is required")
        
    if args.phone and args.group:
        parser.error("Cannot use both phone and group at the same time")
        
    # Add timestamp if requested
    message = args.message
    if args.add_timestamp:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"{message}\n\n[Sent at {timestamp}]"
    
    print("=" * 60)
    print("WhatsApp Personal Notification Test")
    print("=" * 60)
    
    # Run appropriate test
    if args.phone:
        method = "selenium" if args.selenium else "pywhatkit"
        success = test_personal_whatsapp(args.phone, message, method)
    else:
        success = test_group_whatsapp(args.group, message)
    
    print("\n" + "=" * 60)
    if success:
        print("[✓] Test completed successfully!")
    else:
        print("[-] Test failed!")
        print("\nTips:")
        print("- Run with --setup for detailed instructions")
        print("- Make sure WhatsApp Web is logged in")
        print("- Check phone number format (+84...)")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())