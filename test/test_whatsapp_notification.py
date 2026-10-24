#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Test script cho WhatsApp notification service
Có thể test trực tiếp hoặc qua microservice
"""

import os
import sys
import argparse
import requests
from datetime import datetime

# Thêm path để import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.core.notification.whatsapp_notifier import WhatsAppNotifier
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def test_direct_whatsapp(message: str, file_path: str = None):
    """Test gửi thông báo trực tiếp qua WhatsApp API"""
    print("[*] Testing direct WhatsApp notification...")
    
    # Lấy credentials từ env
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    recipient_number = os.getenv('WHATSAPP_RECIPIENT_NUMBER')
    
    if not all([access_token, phone_number_id, recipient_number]):
        print("[-] Missing WhatsApp credentials in .env file!")
        print("    Required: WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_RECIPIENT_NUMBER")
        return False
        
    try:
        # Khởi tạo WhatsApp notifier
        notifier = WhatsAppNotifier(access_token, phone_number_id, recipient_number)
        
        # Gửi message
        print(f"[+] Sending message to {recipient_number}...")
        success = notifier.send_message(message)
        
        if success:
            print("[✓] Message sent successfully!")
        else:
            print("[-] Failed to send message!")
            return False
            
        # Gửi file nếu có
        if file_path and os.path.exists(file_path):
            print(f"[+] Sending document: {file_path}")
            success = notifier.send_document(file_path, f"Test document sent at {datetime.now()}")
            
            if success:
                print("[✓] Document sent successfully!")
            else:
                print("[-] Failed to send document!")
                return False
                
        return True
        
    except Exception as e:
        print(f"[-] Error: {str(e)}")
        return False


def test_microservice_whatsapp(message: str, file_path: str = None, service_url: str = "http://localhost:5002"):
    """Test gửi thông báo qua notification microservice"""
    print("[*] Testing WhatsApp via microservice...")
    
    try:
        # Kiểm tra service health
        print(f"[+] Checking service health at {service_url}...")
        response = requests.get(f"{service_url}/health", timeout=5)
        
        if response.status_code != 200:
            print("[-] Notification service is not running!")
            print("    Run: cd microservices && docker-compose up notification-service")
            return False
            
        print("[✓] Service is healthy!")
        
        # Gửi message
        print("[+] Sending message via microservice...")
        response = requests.post(
            f"{service_url}/notify/message",
            json={
                "message": message,
                "service": "whatsapp"
            }
        )
        
        if response.status_code == 200:
            print("[✓] Message sent successfully!")
            print(f"    Response: {response.json()}")
        else:
            print(f"[-] Failed to send message: {response.status_code}")
            print(f"    Response: {response.text}")
            return False
            
        # Gửi file nếu có
        if file_path and os.path.exists(file_path):
            print(f"[+] Sending document via microservice: {file_path}")
            response = requests.post(
                f"{service_url}/notify/document",
                json={
                    "file_path": os.path.abspath(file_path),
                    "caption": f"Test document via microservice - {datetime.now()}",
                    "service": "whatsapp"
                }
            )
            
            if response.status_code == 200:
                print("[✓] Document sent successfully!")
                print(f"    Response: {response.json()}")
            else:
                print(f"[-] Failed to send document: {response.status_code}")
                print(f"    Response: {response.text}")
                return False
                
        # Test scan report format
        print("[+] Testing scan report notification...")
        response = requests.post(
            f"{service_url}/notify/scan-report",
            json={
                "target": "test.example.com",
                "summary": {
                    "total_urls": 150,
                    "parameter_urls": 45,
                    "total_issues": 12,
                    "high_issues": 2,
                    "medium_issues": 5,
                    "low_issues": 5
                },
                "service": "whatsapp"
            }
        )
        
        if response.status_code == 200:
            print("[✓] Scan report sent successfully!")
        else:
            print(f"[-] Failed to send scan report: {response.status_code}")
            
        return True
        
    except requests.exceptions.ConnectionError:
        print("[-] Cannot connect to microservice!")
        print("    Make sure the service is running:")
        print("    cd microservices && docker-compose up notification-service")
        return False
    except Exception as e:
        print(f"[-] Error: {str(e)}")
        return False


def create_test_report():
    """Tạo file báo cáo test"""
    test_report = """
# Test Scan Report

## Summary
- Target: test.example.com
- Date: {}
- Status: Completed

## Findings
1. **SQL Injection** (High)
   - URL: https://test.example.com/search?q=test
   - Parameter: q
   
2. **XSS** (Medium)
   - URL: https://test.example.com/comment
   - Parameter: message

## Recommendations
- Update to latest framework version
- Implement input validation
- Use prepared statements
""".format(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    report_path = "/tmp/test_scan_report.md"
    with open(report_path, 'w') as f:
        f.write(test_report)
        
    return report_path


def main():
    parser = argparse.ArgumentParser(
        description='Test WhatsApp notification functionality',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test với message đơn giản
  python test_whatsapp_notification.py -m "Hello from Sharingan!"
  
  # Test với file đính kèm
  python test_whatsapp_notification.py -m "Scan completed" -f report.pdf
  
  # Test qua microservice
  python test_whatsapp_notification.py -m "Test message" --microservice
  
  # Test với custom service URL
  python test_whatsapp_notification.py -m "Test" --microservice --service-url http://localhost:5002
  
  # Test đầy đủ với report
  python test_whatsapp_notification.py -m "Full test" --full-test
        """
    )
    
    parser.add_argument('-m', '--message', 
                       required=True,
                       help='Message to send')
    
    parser.add_argument('-f', '--file', 
                       help='File path to send as attachment')
    
    parser.add_argument('--microservice', 
                       action='store_true',
                       help='Test via microservice instead of direct API')
    
    parser.add_argument('--service-url',
                       default='http://localhost:5002',
                       help='Microservice URL (default: http://localhost:5002)')
    
    parser.add_argument('--full-test',
                       action='store_true',
                       help='Run full test including report generation')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("WhatsApp Notification Test")
    print("=" * 60)
    print(f"Message: {args.message}")
    print(f"Mode: {'Microservice' if args.microservice else 'Direct API'}")
    
    if args.file:
        print(f"Attachment: {args.file}")
    print("=" * 60)
    
    # Full test mode
    if args.full_test:
        print("\n[*] Running full test suite...")
        
        # Tạo test report
        report_path = create_test_report()
        print(f"[+] Created test report: {report_path}")
        
        # Test với report
        args.file = report_path
    
    # Run test
    if args.microservice:
        success = test_microservice_whatsapp(args.message, args.file, args.service_url)
    else:
        success = test_direct_whatsapp(args.message, args.file)
    
    # Cleanup
    if args.full_test and os.path.exists(report_path):
        os.remove(report_path)
        print(f"[+] Cleaned up test report")
    
    print("\n" + "=" * 60)
    if success:
        print("[✓] All tests passed!")
    else:
        print("[-] Some tests failed!")
    print("=" * 60)
    
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())