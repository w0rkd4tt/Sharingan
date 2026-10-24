#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module quản lý quá trình quét và tìm kiếm lỗ hổng
"""

import os
import time
import json
import datetime
import requests
from urllib.parse import urlparse
from typing import Dict, List, Set, Optional, Any

from src.core.notification.notifier import Notifier
from src.core.scanner.burp_api import BurpAPI
from src.core.scanner.report_generator import ReportGenerator
from src.core.crawler.paramspider import ParamSpider
from src.core.crawler.waybackurls import Waybackurls
from src.core.crawler.hakrawler import Hakrawler
from src.core.crawler.katana import Katana
from src.core.crawler.url_filter import URLFilter


class Scanner:
    """Lớp quản lý quá trình quét và tìm kiếm lỗ hổng"""
    
    def __init__(self, target: str, output_dir: str,
                 burp_api_url: str, burp_api_key: str,
                 threads: int = 10, verbose: bool = False,
                 notifier: Optional[Notifier] = None,
                 scan_config: str = "default"):
        """
        Khởi tạo lớp quản lý quá trình quét
        
        Args:
            target: Tên miền mục tiêu
            output_dir: Thư mục đầu ra để lưu kết quả
            burp_api_url: URL của Burp REST API
            burp_api_key: API key cho Burp REST API
            threads: Số luồng chạy song song
            verbose: Bật chế độ thông báo chi tiết
            notifier: Đối tượng thông báo
            scan_config: Tên cấu hình scan cần sử dụng
        """
        self.target = target
        self.output_dir = output_dir
        self.threads = threads
        self.verbose = verbose
        self.notifier = notifier
        self.scan_config = scan_config
        
        # Tạo thư mục đầu ra nếu chưa tồn tại
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "raw"), exist_ok=True)
        os.makedirs(os.path.join(self.output_dir, "scan_results"), exist_ok=True)
        
        # Khởi tạo các thành phần
        self.paramspider = ParamSpider(target, os.path.join(self.output_dir, "raw"))
        self.waybackurls = Waybackurls(target, os.path.join(self.output_dir, "raw"))
        self.hakrawler = Hakrawler(target, os.path.join(self.output_dir, "raw"))
        self.katana = Katana(target, os.path.join(self.output_dir, "raw"))
        
        self.burp_api = BurpAPI()
        
        # Khởi tạo trình tạo báo cáo
        self.report_generator = ReportGenerator(target, output_dir, notifier)
        
        # Kết quả
        self.all_urls = set()
        self.parameter_urls = set()
        self.start_time = time.time()
        self.scan_results = []
        
        # Thêm khởi tạo URLFilter
        self.url_filter = URLFilter(target)
        
        # Gửi thông báo bắt đầu nếu có bộ thông báo
        if self.notifier:
            from src.core.notification.notification_factory import NotificationFactory
            target_escaped = NotificationFactory.escape_markdown(self.notifier, self.target)
            self.notifier.send_message(f"🚀 Bắt đầu quá trình recon cho {target_escaped}")
    
    def send_notification(self, message: str) -> None:
        """
        Gửi thông báo nếu có bộ thông báo
        
        Args:
            message: Nội dung thông báo
        """
        if self.notifier:
            self.notifier.send_message(message)
    
    def send_issue_notification(self, issues: List[Dict]) -> None:
        """
        Gửi thông báo WhatsApp về các issues tìm thấy
        
        Args:
            issues: Danh sách issues
        """
        if not self.notifier or not issues:
            return
        
        # Phân loại issues theo severity
        severity_counts = {}
        for issue in issues:
            severity = None
            if isinstance(issue, dict):
                severity = issue.get('severity', '').lower()
                if not severity:
                    severity = issue.get('risk', '').lower()
                if not severity:
                    severity = issue.get('confidence', 'unknown').lower()
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Tạo thông báo
        message = f"""🚨 Phát hiện {len(issues)} lỗ hổng mới!

📊 Phân loại theo severity:"""
        
        for severity, count in sorted(severity_counts.items(), reverse=True):
            if severity == 'critical':
                emoji = '🔴'
            elif severity == 'high':
                emoji = '🟠'
            elif severity == 'info':
                emoji = '🔵'
            else:
                emoji = '⚪'
            
            message += f"\n{emoji} {severity.upper()}: {count} lỗ hổng"
        
        # Thêm một số issues mẫu
        message += "\n\n📋 Một số lỗ hổng tiêu biểu:"
        
        for i, issue in enumerate(issues[:5]):  # Show first 5 issues
            if isinstance(issue, dict):
                name = issue.get('name', issue.get('type', 'Unknown'))
                url = issue.get('url', issue.get('path', 'N/A'))
                severity = issue.get('severity', issue.get('risk', 'unknown'))
                
                message += f"\n\n{i+1}. {name}"
                message += f"\n   Severity: {severity}"
                message += f"\n   URL: {url[:100]}..."  # Truncate long URLs
        
        if len(issues) > 5:
            message += f"\n\n... và {len(issues) - 5} lỗ hổng khác"
        
        message += f"\n\n⏰ Thời gian: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        message += f"\n📁 Chi tiết trong file báo cáo"
        
        # Gửi thông báo
        try:
            self.notifier.send_message(message)
            print("[+] Đã gửi thông báo WhatsApp về các lỗ hổng tìm thấy")
        except Exception as e:
            print(f"[-] Lỗi khi gửi thông báo WhatsApp: {str(e)}")

    def load_default_scan_config(self) -> Dict:
        """
        Load cấu hình scan mặc định
        
        Returns:
            Dict: Cấu hình scan mặc định
        """
        return {
            "scan_configurations": [
                {
                    "config": "Checking,Testing",
                    "type": "CustomConfiguration"
                }
            ],
            "urls": []
        }

    def generate_scan_report(self, vulnerabilities: List[Dict]) -> str:
        """
        Tạo báo cáo scan dạng markdown
        
        Args:
            vulnerabilities: Danh sách các lỗ hổng tìm thấy
            
        Returns:
            str: Đường dẫn đến file báo cáo
        """
        report_file = os.path.join(self.output_dir, "scan_results", "scan_report.md")
        
        with open(report_file, 'w') as f:
            f.write(f"# Scan Report for {self.target}\n\n")
            f.write(f"Scan Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            if not vulnerabilities:
                f.write("No vulnerabilities found.\n")
                return report_file
                
            f.write("## Vulnerabilities\n\n")
            
            for vuln in vulnerabilities:
                f.write(f"### {vuln.get('name', 'Unknown Vulnerability')}\n\n")
                f.write(f"**Severity:** {vuln.get('severity', 'Unknown')}\n\n")
                f.write(f"**URL:** {vuln.get('url', 'Unknown')}\n\n")
                f.write(f"**Description:**\n{vuln.get('description', 'No description available')}\n\n")
                f.write(f"**Remediation:**\n{vuln.get('remediation', 'No remediation available')}\n\n")
                f.write("---\n\n")
                
        return report_file
    
    def find_parameters(self, urls: Set[str]) -> Set[str]:
        """
        Lọc các URL có tham số
        
        Args:
            urls: Tập hợp các URL
            
        Returns:
            Set[str]: Tập hợp các URL có tham số
        """
        parameter_urls = set()
        
        for url in urls:
            if "?" in url and "=" in url:
                parameter_urls.add(url)
        
        return parameter_urls
    
    def monitor_scan_progress(self, scan_id: str) -> List[Dict]:
        """
        Theo dõi tiến trình scan và thu thập kết quả
        
        Args:
            scan_id: ID của scan
            
        Returns:
            List[Dict]: Danh sách các lỗ hổng tìm thấy
        """
        vulnerabilities = []
        notified_issues = set()  # Track issues đã notify để tránh duplicate
        wait_interval = 10    # 10 seconds
        elapsed_time = 0
        
        # Không giới hạn thời gian - scan đến khi hoàn thành
        while True:
            try:
                # Kiểm tra trạng thái scan
                status = self.burp_api.check_scan_status(scan_id)
                
                # Luôn lấy kết quả scan mới nhất
                current_issues = []
                results = self.burp_api.get_scan_results(scan_id)
                if results:
                    current_issues = results
                
                # Lọc issues theo severity
                filtered_issues = []
                severity_filter = ['high', 'critical', 'info']
                
                for issue in current_issues:
                    severity = None
                    if isinstance(issue, dict):
                        severity = issue.get('severity', '').lower()
                        
                        # Accept "high", "critical" severity or "info" type issues
                        if severity in severity_filter or severity == 'information':
                            # Tạo unique ID cho issue
                            issue_id = f"{issue.get('issue_name', '')}_{issue.get('url', '')}_{issue.get('path', '')}"
                            
                            # Chỉ thêm và notify nếu là issue mới
                            if issue_id not in notified_issues:
                                filtered_issues.append(issue)
                                notified_issues.add(issue_id)
                                vulnerabilities.append(issue)
                
                # Notify về issues mới
                if filtered_issues and self.notifier:
                    print(f"[+] Phát hiện {len(filtered_issues)} issues mới")
                    self.send_issue_notification(filtered_issues)
                
                # In progress mỗi lần check
                if elapsed_time % 60 == 0:  # Mỗi phút
                    print(f"[*] Scan đang chạy... Đã tìm thấy {len(vulnerabilities)} issues (elapsed: {elapsed_time}s)")
                
                # Kiểm tra status để biết khi nào hoàn thành
                if status == "succeeded":
                    print(f"[+] Scan hoàn thành. Tổng cộng tìm thấy {len(vulnerabilities)} lỗ hổng")
                    break
                    
                elif status == "failed":
                    print("[-] Scan thất bại")
                    break
                    
                elif status in ["running", "crawling", "auditing"]:
                    # Scan đang chạy, đợi thêm
                    time.sleep(wait_interval)
                    elapsed_time += wait_interval
                    
                elif status == "paused":
                    # Scan bị tạm dừng, đợi lâu hơn
                    time.sleep(60)  # Wait 1 minute
                    elapsed_time += 60
                    
                else:
                    print(f"[!] Trạng thái scan không xác định: {status}")
                    break
                    
            except Exception as e:
                print(f"[-] Lỗi khi theo dõi scan: {str(e)}")
                # Không break - tiếp tục monitor
                time.sleep(wait_interval)
                elapsed_time += wait_interval
                
        return vulnerabilities
    
    def start_default_scan(self, urls: List[str]) -> Optional[str]:
        """
        Bắt đầu scan với cấu hình mặc định (fallback khi không có Burp API)
        
        Args:
            urls: Danh sách URLs cần scan
            
        Returns:
            Optional[str]: Scan ID nếu thành công
        """
        print("[!] Burp API không khả dụng, sử dụng phương thức scan mặc định")
        # Có thể implement các phương thức scan khác ở đây
        return None
    
    def run(self) -> None:
        """Chạy toàn bộ quá trình quét"""
        self.start_time = time.time()
        print(f"[+] Bắt đầu quá trình recon cho {self.target}...")
        
        try:
            # Chạy ParamSpider
            # self.send_notification(f"🔍 *Đang chạy ParamSpider để tìm URLs có tham số\\.\\.\\.*")
            paramspider_urls = self.paramspider.run()
            # self.send_notification(f"✅ ParamSpider hoàn thành: tìm thấy {len(paramspider_urls)} URLs")
            
            # Chạy Waybackurls
            # self.send_notification(f"🔍 *Đang chạy waybackurls để tìm URLs lịch sử\\.\\.\\.*")
            waybackurls_urls = self.waybackurls.run()
            # self.send_notification(f"✅ waybackurls hoàn thành: tìm thấy {len(waybackurls_urls)} URLs")
            
            # Chạy Hakrawler
            # self.send_notification(f"🔍 *Đang chạy hakrawler để crawl website\\.\\.\\.*")
            hakrawler_urls = self.hakrawler.run()
            # self.send_notification(f"✅ hakrawler hoàn thành: tìm thấy {len(hakrawler_urls)} URLs")
            
            # Chạy Katana
            # self.send_notification(f"🔍 *Đang chạy katana để crawl website\\.\\.\\.*")
            katana_urls = self.katana.run()
            # self.send_notification(f"✅ katana hoàn thành: tìm thấy {len(katana_urls)} URLs")
            
            # Gộp tất cả URL
            self.all_urls = paramspider_urls.union(waybackurls_urls, hakrawler_urls, katana_urls)
            
            # Lọc URL
            # self.send_notification(f"🔍 *Đang lọc URLs\\.\\.\\.*")
            self.all_urls = self.url_filter.run(self.all_urls)
            # self.send_notification(f"✅ Đã lọc xong: {len(self.all_urls)} URLs còn lại")
            
            # Tìm các URL có tham số
            self.parameter_urls = self.find_parameters(self.all_urls)
            # self.send_notification(f"✅ Tìm thấy {len(self.parameter_urls)} URLs có tham số")
            
            # Lưu kết quả vào file
            urls_file = os.path.join(self.output_dir, "all_urls.txt")
            with open(urls_file, 'w') as f:
                for url in sorted(self.all_urls):
                    f.write(f"{url}\n")
            
            param_urls_file = os.path.join(self.output_dir, "parameter_urls.txt")
            with open(param_urls_file, 'w') as f:
                for url in sorted(self.parameter_urls):
                    f.write(f"{url}\n")
            
            # Gửi URLs đến Burp Suite để quét
            if self.all_urls:
                # Lọc URLs hợp lệ trước khi gửi
                valid_urls = []
                for url in self.all_urls:
                    try:
                        # Clean URL first
                        url = url.strip()  # Remove leading/trailing whitespace
                        url = url.replace('\n', '').replace('\r', '')  # Remove newlines
                        url = url.replace(' ', '%20')  # Encode spaces
                        
                        # Skip empty URLs
                        if not url:
                            continue
                            
                        # Parse URL để kiểm tra tính hợp lệ
                        parsed = urlparse(url)
                        
                        # Chỉ chấp nhận http và https
                        if parsed.scheme in ['http', 'https'] and parsed.netloc:
                            # Kiểm tra thêm các trường hợp URL không hợp lệ
                            if not any(invalid in url.lower() for invalid in ['mailto:', 'javascript:', 'ftp:', 'file:', 'data:']):
                                # Loại bỏ URLs có cấu trúc sai
                                if '://' in url and url.count('://') == 1:
                                    # Loại bỏ URLs có placeholder FUZZ (từ fuzzing tools)
                                    if 'FUZZ' not in url:
                                        # Final validation - ensure URL is well-formed
                                        if len(parsed.netloc) > 0 and '.' in parsed.netloc:
                                            valid_urls.append(url)
                    except Exception as e:
                        # Bỏ qua URLs không thể parse
                        if self.verbose:
                            print(f"[-] Skipping invalid URL: {url[:50]}... - {str(e)}")
                        pass
                
                print(f"[+] Đã lọc {len(valid_urls)} URLs hợp lệ từ {len(self.all_urls)} URLs")
                
                # Lọc và chỉ lấy 100 domain đầu tiên
                unique_domains = set()
                domain_urls = []
                
                for url in valid_urls:
                    try:
                        parsed = urlparse(url)
                        domain = parsed.netloc.lower()
                        
                        # Loại bỏ www. prefix để chuẩn hóa domain
                        if domain.startswith('www.'):
                            domain = domain[4:]
                        
                        # Thêm domain vào set để track unique domains
                        if domain and domain not in unique_domains:
                            unique_domains.add(domain)
                            # Lấy URL đầu tiên của mỗi domain
                            domain_urls.append(url)
                            
                            # Dừng khi đạt 100 domains
                            if len(unique_domains) >= 100:
                                break
                    except Exception:
                        pass
                
                print(f"[+] Đã lọc {len(unique_domains)} domains duy nhất")
                print(f"[+] Giới hạn scan cho 100 domains đầu tiên")
                
                # Sử dụng domain_urls thay vì valid_urls
                valid_urls = domain_urls[:100]
                
                # Hiển thị một số domains đầu tiên
                if valid_urls:
                    print(f"[+] Một số domains sẽ được scan:")
                    for i, url in enumerate(valid_urls[:10]):
                        parsed = urlparse(url)
                        print(f"    {i+1}. {parsed.netloc}")
                    if len(valid_urls) > 10:
                        print(f"    ... và {len(valid_urls) - 10} domains khác")
                    
                    # Lưu danh sách domains vào file
                    domains_file = os.path.join(self.output_dir, "scanned_domains.txt")
                    with open(domains_file, 'w') as f:
                        for url in valid_urls:
                            parsed = urlparse(url)
                            f.write(f"{parsed.netloc}\t{url}\n")
                    print(f"[+] Đã lưu danh sách domains vào: {domains_file}")
                
                print(f"[+] Đang gửi {len(valid_urls)} domain URLs để quét...")
                
                # Gửi cấu hình quét đến Burp Suite
                if self.burp_api and valid_urls:
                    # Load scan configuration if needed
                    scan_config_dict = None
                    if self.scan_config and self.scan_config != "default":
                        config_file = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'burp_scan_configs.json')
                        if os.path.exists(config_file):
                            try:
                                with open(config_file, 'r') as f:
                                    all_configs = json.load(f)
                                
                                # Check different config locations
                                if self.scan_config in all_configs:
                                    scan_config_dict = all_configs[self.scan_config]
                                elif 'default' in all_configs and 'scan_configurations' in all_configs['default']:
                                    if self.scan_config in all_configs['default']['scan_configurations']:
                                        scan_config_dict = all_configs['default']['scan_configurations'][self.scan_config]
                            except Exception as e:
                                print(f"[-] Error loading scan config: {str(e)}")
                    
                    scan_id = self.burp_api.start_scan(valid_urls, scan_config_dict)
                else:
                    scan_id = self.start_default_scan(valid_urls)
                    
                if scan_id:
                    print(f"[+] Đã gửi thành công cấu hình quét. Scan ID: {scan_id}")
                    print("[+] Đang theo dõi tiến trình scan...")
                    
                    # Theo dõi tiến trình scan
                    vulnerabilities = self.monitor_scan_progress(scan_id)
                    self.scan_results = vulnerabilities
                    
                    # Tạo báo cáo scan
                    report_file = self.generate_scan_report(vulnerabilities)
                    print(f"[+] Đã lưu báo cáo scan vào file: {report_file}")
                else:
                    print("[-] Không thể gửi cấu hình quét")
            else:
                print("[-] Không có URL nào để quét")
            
            # Tạo báo cáo cuối cùng
            duration = time.time() - self.start_time
            report_file = self.report_generator.generate_markdown_report(
                self.all_urls,
                self.parameter_urls,
                self.scan_results,  # Thêm kết quả scan vào báo cáo
                duration
            )
            
            print(f"[+] Hoàn thành quá trình recon cho {self.target}")
            print(f"[+] Tổng kết:")
            print(f"    - Thời gian thực hiện: {duration:.2f} giây")
            print(f"    - Tổng số URL: {len(self.all_urls)}")
            print(f"    - URL có tham số: {len(self.parameter_urls)}")
            print(f"    - Số lỗ hổng tìm thấy: {len(self.scan_results)}")
            
            # Gửi báo cáo tổng kết qua notification
            if self.notifier:
                summary_message = f"""✅ Hoàn thành quét {self.target}

📊 Tổng kết:
• Thời gian: {duration:.2f} giây
• Tổng URL: {len(self.all_urls)}
• URL có tham số: {len(self.parameter_urls)}
• Lỗ hổng tìm thấy: {len(self.scan_results)}"""
                
                self.send_notification(summary_message)
                
                # Gửi file báo cáo nếu có
                if report_file and os.path.exists(report_file):
                    if hasattr(self.notifier, 'send_document'):
                        self.notifier.send_document(report_file, f"Báo cáo scan {self.target}")
            
        except Exception as e:
            error_message = f"❌ Lỗi: {str(e)}"
            print(f"[-] {error_message}")
            self.send_notification(error_message)