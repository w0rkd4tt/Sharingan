#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SharinganV2 - Công cụ kết hợp nhiều công cụ recon web để tìm kiếm lỗ hổng

Kết hợp: ParamSpider, waybackurls, gauplus, hakrawler, katana
Sau đó sử dụng fuzzing templates và gửi kết quả đến Burp Suite qua Burp REST API
Tích hợp với bot Telegram để gửi thông báo trạng thái, lỗi và báo cáo cuối cùng
"""

import os
import sys
import argparse
from src.core.scanner.scanner import Scanner
from src.config.config_manager import ConfigManager
from src.core.notification.notification_factory import NotificationFactory

def print_banner():
    banner = """
    ███████╗██╗  ██╗ █████╗ ██████╗ ██╗███╗   ██╗ ██████╗  █████╗ ███╗   ██╗
    ██╔════╝██║  ██║██╔══██╗██╔══██╗██║████╗  ██║██╔════╝ ██╔══██╗████╗  ██║
    ███████╗███████║███████║██████╔╝██║██╔██╗ ██║██║  ███╗███████║██╔██╗ ██║
    ╚════██║██╔══██║██╔══██║██╔══██╗██║██║╚██╗██║██║   ██║██╔══██║██║╚██╗██║
    ███████║██║  ██║██║  ██║██║  ██║██║██║ ╚████║╚██████╔╝██║  ██║██║ ╚████║
    ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝
    """
    print(banner)
    print("SharinganV2 - Công cụ kết hợp nhiều công cụ recon web để tìm kiếm lỗ hổng")
    print("=" * 80)
    print("\nCách sử dụng:")
    print("python3 sharingan.py -t example.com --threads 10 --verbose --fuzzing")
    print("\nCác tùy chọn:")
    print("-t, --target: Tên miền mục tiêu")
    print("--templates: Thư mục chứa các template fuzzing (mặc định: 'src/template')")
    print("--threads: Số luồng chạy song song (mặc định: 10)")
    print("--verbose: Bật chế độ thông báo chi tiết")
    print("--fuzzing: Bật tính năng fuzzing template")
    print("--create-templates: Tạo các template fuzzing mẫu")
    print("--create-config: Tạo tệp cấu hình mẫu")
    print("--create-env: Tạo file .env mẫu")
    print("--env-file: Đường dẫn đến file .env chứa cấu hình (mặc định: '.env')")
    print("\nVí dụ:")
    print("1. Quét một tên miền:")
    print("   python3 sharingan.py -t example.com --threads 10 --verbose --fuzzing")
    print("2. Tạo template mẫu:")
    print("   python3 sharingan.py --create-templates")
    print("3. Tạo file cấu hình mẫu:")
    print("   python3 sharingan.py --create-config")
    print("4. Tạo file .env mẫu:")
    print("   python3 sharingan.py --create-env")
    print("\nLưu ý: Cấu hình WhatsApp và Burp Suite có thể được đặt trong file .env")
    print("=" * 80)

def main():
    if len(sys.argv) == 1:
        print_banner()
        return

    parser = argparse.ArgumentParser(description="SharinganV2 - Công cụ kết hợp nhiều công cụ recon web")
    parser.add_argument("-t", "--target", help="Tên miền mục tiêu (ví dụ: example.com)")
    parser.add_argument("--templates", default="src/template", help="Thư mục chứa các template fuzzing (mặc định: 'src/template')")
    parser.add_argument("--threads", type=int, default=10, help="Số luồng chạy song song (mặc định: 10)")
    parser.add_argument("--verbose", action="store_true", help="Bật chế độ thông báo chi tiết")
    parser.add_argument("--create-templates", action="store_true", help="Tạo các template fuzzing mẫu")
    parser.add_argument("--create-config", action="store_true", help="Tạo tệp cấu hình mẫu")
    parser.add_argument("--create-env", action="store_true", help="Tạo file .env mẫu")
    parser.add_argument("--env-file", default=".env", help="Đường dẫn đến file .env chứa cấu hình (mặc định: '.env')")
    parser.add_argument("--fuzzing", action="store_true", help="Bật tính năng fuzzing template")
    
    args = parser.parse_args()
    
    # Tạo đối tượng ConfigManager để quản lý cấu hình
    config_manager = ConfigManager(env_file=args.env_file)
    
    if args.create_templates:
        from src.config.template_creator import create_sample_templates
        create_sample_templates(args.templates)
        return
    
    if args.create_config:
        from src.config.config_creator import create_sample_severity_config
        create_sample_severity_config()
        return
        
    if args.create_env:
        from src.config.env_creator import create_sample_env_file
        create_sample_env_file()
        return
    
    # Kiểm tra target
    if not args.target:
        print("[-] Lỗi: Bạn phải chỉ định tên miền mục tiêu (-t hoặc --target)")
        return

    # Tạo thư mục đầu ra dựa trên target
    output_dir = os.path.join("reports", args.target)
    os.makedirs(output_dir, exist_ok=True)
    
    # Lấy cấu hình từ tham số dòng lệnh và biến môi trường
    burp_api_url = config_manager.get("BURP_API_URL")
    burp_api_key = config_manager.get("BURP_API_KEY")
    enable_fuzzing = args.fuzzing
    
    # Nếu không chỉ định fuzzing từ tham số, kiểm tra biến môi trường
    if not enable_fuzzing and config_manager.get("ENABLE_FUZZING"):
        env_fuzzing = config_manager.get("ENABLE_FUZZING").lower()
        enable_fuzzing = env_fuzzing in ["true", "1", "yes", "y"]
    
    # Khởi tạo bộ thông báo sử dụng factory pattern
    notifier = NotificationFactory.create_notifier()
    
    # Khởi tạo scanner
    scanner = Scanner(
        target=args.target,
        output_dir=output_dir,  # Sử dụng thư mục đầu ra dựa trên target
        burp_api_url=burp_api_url,
        burp_api_key=burp_api_key,
        threads=args.threads,
        verbose=args.verbose,
        notifier=notifier
    )
    
    # Chạy quá trình quét
    scanner.run()

if __name__ == "__main__":
    main()