#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module tương tác với Burp REST API
"""

import json
import time
import requests
import os
import datetime
from typing import Dict, List, Optional, Any


class BurpAPI:
    """Lớp tương tác với Burp REST API"""
    
    def __init__(self, api_url: str = "http://127.0.0.1:1337/v0.1"):
        """
        Khởi tạo lớp tương tác với Burp REST API
        
        Args:
            api_url: URL của Burp REST API
        """
        self.api_url = api_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def load_default_config(self) -> Dict:
        """
        Load cấu hình scan mặc định
        
        Returns:
            Dict: Cấu hình scan mặc định
        """
        return {
            "scan_configurations": [
                {
                    "name": "Crawl and Audit - Crawl strategy - most complete",
                    "type": "NamedConfiguration"
                }
            ],
            "urls": []
        }
    
    def start_scan(self, urls: List[str], scan_config: Optional[Dict] = None) -> Optional[str]:
        """
        Bắt đầu scan với danh sách URL
        
        Args:
            urls: Danh sách URL cần scan
            scan_config: Cấu hình scan từ burp_scan_configs.json
            
        Returns:
            Optional[str]: ID của scan nếu thành công, None nếu thất bại
        """
        try:
            # Validate URLs
            if not urls or len(urls) == 0:
                print("[-] Không có URLs để scan")
                return None
            
            # Clean URLs before sending
            cleaned_urls = []
            for url in urls:
                # Basic cleaning
                url = str(url).strip()
                url = url.replace('\n', '').replace('\r', '')
                url = url.replace('\t', '')
                
                # Skip empty or invalid URLs
                if url and url.startswith(('http://', 'https://')) and len(url) > 10:
                    cleaned_urls.append(url)
            
            if not cleaned_urls:
                print("[-] Không có URLs hợp lệ sau khi làm sạch")
                return None
                
            # Start with URLs
            config = {"urls": cleaned_urls}
            
            # If scan_config provided, use it; otherwise use default Crawl and Audit
            if scan_config and isinstance(scan_config, dict) and "scan_configurations" in scan_config:
                scan_configurations = scan_config["scan_configurations"]
                # Validate scan configurations format
                if isinstance(scan_configurations, list) and len(scan_configurations) > 0:
                    # Check if each config has required fields
                    valid_configs = []
                    for sc in scan_configurations:
                        if isinstance(sc, dict) and "name" in sc:
                            valid_configs.append({
                                "name": sc["name"],
                                "type": sc.get("type", "NamedConfiguration")
                            })
                    
                    if valid_configs:
                        config["scan_configurations"] = valid_configs
            else:
                # Use default Crawl and Audit configuration
                config["scan_configurations"] = [
                    {
                        "name": "Checking",
                        "type": "NamedConfiguration"
                    },{
                        "name": "Testing",
                        "type": "NamedConfiguration"
                    }
                ]
                print("[+] Using default scan configuration: Crawl and Audit - most complete")
                
            # Debug: In cấu hình chi tiết
            print(f"[+] Config: {json.dumps(config, indent=2)}")
            print(f"[+] Number of URLs: {len(config.get('urls', []))}")
            
            # Kiểm tra URLs có vấn đề
            if 'urls' in config:
                print(f"[+] Checking first 10 URLs for validity:")
                for i, url in enumerate(config['urls'][:10]):  # Check first 10 URLs
                    # Basic URL validation
                    is_valid = True
                    issues = []
                    
                    if not url:
                        is_valid = False
                        issues.append("empty")
                    elif not url.startswith(('http://', 'https://')):
                        is_valid = False
                        issues.append("missing protocol")
                    elif ' ' in url:
                        is_valid = False
                        issues.append("contains spaces")
                    elif '\n' in url or '\r' in url:
                        is_valid = False
                        issues.append("contains newlines")
                    
                    status = "✓" if is_valid else "✗"
                    issue_str = f" ({', '.join(issues)})" if issues else ""
                    print(f"    {status} URL {i+1}: {url[:100]}...{issue_str}")
            
            # Gửi request đến Burp REST API
            response = requests.post(
                f"{self.api_url}/scan",
                json=config,
                headers=self.headers
            )
            
            print(f"[+] Response status: {response.status_code}")
            print(f"[+] Response headers: {dict(response.headers)}")
            print(f"[+] Response text: {response.text}")
            
            if response.status_code == 201:
                location_header = response.headers.get("Location")
                if location_header:
                    scan_id = location_header.split("/")[-1]
                    print(f"[+] Scan created successfully. Scan ID: {scan_id}")
                    return scan_id
            else:
                print(f"[-] Lỗi khi gửi request đến Burp REST API: {response.status_code}")
                if response.text:
                    print(f"[-] Chi tiết lỗi: {response.text}")
                return None
                
        except Exception as e:
            print(f"[-] Lỗi khi bắt đầu scan: {str(e)}")
            return None
    
    def check_scan_status(self, scan_id):
        """Check scan status and notify new vulnerabilities"""
        url = f"{self.api_url}/scan/{scan_id}"
        print(f"[+] Sending GET request to {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                response_json = response.json()
                scan_status = response_json.get("scan_status")
                print(f"[+] Scan status: {scan_status}")
                
                if scan_status == "succeeded":
                    print("[+] Scan completed successfully")
                    return "succeeded"
                elif scan_status == "failed":
                    print("[-] Scan failed")
                    return "failed"
                elif scan_status == "running" or scan_status == "crawling" or scan_status == "auditing":
                    print("[+] Scan is still running...")
                    return "running"
                elif scan_status == "paused":
                    print("[*] Scan is paused, waiting 5 minutes before checking again...")
                    return "paused"
                else:
                    print(f"[*] Unknown scan status: {scan_status}")
                    return scan_status
                    
            print(f"[-] Failed to fetch scan status: {response.status_code}")
            return None
                
        except requests.exceptions.RequestException as e:
            print(f"[-] Error while fetching scan status: {e}")
            return None
    
    def get_scan_results(self, scan_id: str) -> Optional[List[Dict]]:
        """
        Lấy kết quả scan (issues) từ scan status
        
        Args:
            scan_id: ID của scan
            
        Returns:
            Optional[List[Dict]]: Danh sách issues nếu thành công, None nếu thất bại
        """
        try:
            # Get scan status which includes issue_events
            response = requests.get(
                f"{self.api_url}/scan/{scan_id}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                data = response.json()
                # Extract issue_events from the response
                issue_events = data.get('issue_events', [])
                return issue_events
            return None
            
        except Exception as e:
            print(f"[-] Lỗi khi lấy kết quả scan: {str(e)}")
            return None
        
    def get_bug(self, scan_id: str) -> Optional[List[Dict]]:
        """
        Lấy báo cáo lỗi từ scan
        
        Args:
            scan_id: ID của scan
            
        Returns:
            Optional[List[Dict]]: Danh sách các lỗi được phát hiện nếu thành công, None nếu thất bại
        """
        try:
            response = requests.get(
                f"{self.api_url}/scan/{scan_id}/bug_report",
                headers=self.headers
            )
            
            if response.status_code == 200:
                #get scan status from response
                scan_status = response.json().get("scan_status")
                if scan_status == "completed":
                    print("[-] Scan completed")
                    return True
                elif scan_status == "failed":
                    print("[-] Scan failed")
                    return False

                bugs = response.json()
                print(f"[+] Found {len(bugs)} bugs in scan {scan_id}")
                for bug in bugs:
                    print(f"[+] Bug: {bug.get('name', 'Unknown')} - Severity: {bug.get('severity', 'Unknown')}")
                return bugs
            else:
                print(f"[-] Failed to get bug report: {response.status_code}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[-] Error while getting bug report: {e}")
            return None
        except json.JSONDecodeError as e:
            print(f"[-] Error parsing bug report response: {e}")
            return None
    
    def stop_scan(self, scan_id: str) -> bool:
        """
        Dừng scan
        
        Args:
            scan_id: ID của scan
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            response = requests.post(
                f"{self.api_url}/scan/{scan_id}/stop",
                headers=self.headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"[-] Lỗi khi dừng scan: {str(e)}")
            return False
    
    def delete_scan(self, scan_id: str) -> bool:
        """
        Xóa scan
        
        Args:
            scan_id: ID của scan
            
        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            response = requests.delete(
                f"{self.api_url}/scan/{scan_id}",
                headers=self.headers
            )
            
            return response.status_code == 200
            
        except Exception as e:
            print(f"[-] Lỗi khi xóa scan: {str(e)}")
            return False
    
    def get_scan_configurations(self) -> Optional[List[Dict]]:
        """
        Lấy danh sách cấu hình scan
        
        Returns:
            Optional[List[Dict]]: Danh sách cấu hình scan nếu thành công, None nếu thất bại
        """
        try:
            response = requests.get(
                f"{self.api_url}/scan_configurations",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"[-] Lỗi khi lấy danh sách cấu hình scan: {str(e)}")
            return None
    
    def get_scan_configuration(self, config_name: str) -> Optional[Dict]:
        """
        Lấy thông tin cấu hình scan
        
        Args:
            config_name: Tên cấu hình scan
            
        Returns:
            Optional[Dict]: Thông tin cấu hình scan nếu thành công, None nếu thất bại
        """
        try:
            response = requests.get(
                f"{self.api_url}/scan_configurations/{config_name}",
                headers=self.headers
            )
            
            if response.status_code == 200:
                return response.json()
            return None
            
        except Exception as e:
            print(f"[-] Lỗi khi lấy thông tin cấu hình scan: {str(e)}")
            return None
        
    def monitor_scan_progress(self, scan_id: str):
        """Monitor scan progress and generate report when completed"""
        print(f"[+] Starting to monitor scan {scan_id}")
        while True:
            status = self.check_scan_status(scan_id)
            
            if status == "succeeded":
                print("[+] Scan completed successfully, generating report...")
                # Lấy danh sách bugs khi scan hoàn thành
                bugs = self.get_bug(scan_id)
                if bugs:
                    # Tạo báo cáo
                    reports = self.generate_scan_report(scan_id)
                    print(f"[+] Generated reports: {reports}")
                return bugs
            elif status == "failed":
                print("[-] Scan failed")
                return None
            elif status == "running":
                print("[+] Scan is still running, waiting...")
                time.sleep(10)  # Đợi 10s trước khi check lại
            elif status == "paused":
                print("[*] Scan is paused, waiting 5 minutes...")
                time.sleep(300)  # Đợi 5 phút trước khi check lại
            else:
                print(f"[-] Unknown scan status: {status}")
                return None
    
    def generate_scan_report(self, scan_id: str, output_dir: str = "scan_reports") -> Dict[str, str]:
        """
        Tạo báo cáo chi tiết về các lỗi được phát hiện dưới dạng markdown và HTML
        
        Args:
            scan_id: ID của scan
            output_dir: Thư mục lưu báo cáo
            
        Returns:
            Dict[str, str]: Dictionary chứa đường dẫn đến các file báo cáo
        """
        try:
            # Tạo thư mục output nếu chưa tồn tại
            os.makedirs(output_dir, exist_ok=True)
            
            # Lấy thông tin scan
            scan_status = self.check_scan_status(scan_id)
            bugs = self.get_bug(scan_id)
            
            if not bugs:
                print("[-] No bugs found in scan")
                return {}
                
            # Tạo timestamp cho tên file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"scan_report_{scan_id}_{timestamp}"
            
            # Tạo báo cáo markdown
            md_report = f"""# Scan Report
## Scan Information
- **Scan ID:** {scan_id}
- **Scan Status:** {scan_status}
- **Scan Date:** {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
- **Total Issues Found:** {len(bugs)}

## Issues Found

"""
            
            # Tạo báo cáo HTML
            html_report = f"""<!DOCTYPE html>
<html>
<head>
    <title>Scan Report - {scan_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; }}
        .issue {{ margin: 20px 0; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
        .high {{ border-left: 5px solid #dc3545; }}
        .medium {{ border-left: 5px solid #ffc107; }}
        .low {{ border-left: 5px solid #28a745; }}
        .info {{ border-left: 5px solid #17a2b8; }}
        .severity {{ font-weight: bold; }}
        .url {{ word-break: break-all; }}
        .description {{ white-space: pre-wrap; }}
    </style>
</head>
<body>
    <h1>Scan Report</h1>
    <h2>Scan Information</h2>
    <ul>
        <li><strong>Scan ID:</strong> {scan_id}</li>
        <li><strong>Scan Status:</strong> {scan_status}</li>
        <li><strong>Scan Date:</strong> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</li>
        <li><strong>Total Issues Found:</strong> {len(bugs)}</li>
    </ul>
    
    <h2>Issues Found</h2>
"""
            
            # Thêm thông tin chi tiết về từng lỗi
            for bug in bugs:
                severity = bug.get('severity', 'Unknown').lower()
                name = bug.get('name', 'Unknown')
                url = bug.get('url', 'Unknown')
                description = bug.get('description', 'No description available')
                remediation = bug.get('remediation', 'No remediation available')
                
                # Thêm vào markdown
                md_report += f"""### {name}
- **Severity:** {severity}
- **URL:** {url}
- **Description:**
{description}
- **Remediation:**
{remediation}

---
"""
                
                # Thêm vào HTML
                html_report += f"""
    <div class="issue {severity}">
        <h3>{name}</h3>
        <p><span class="severity">Severity:</span> {severity}</p>
        <p><span class="severity">URL:</span> <span class="url">{url}</span></p>
        <h4>Description:</h4>
        <div class="description">{description}</div>
        <h4>Remediation:</h4>
        <div class="description">{remediation}</div>
    </div>
"""
            
            # Hoàn thiện HTML
            html_report += """
</body>
</html>
"""
            
            # Lưu các file báo cáo
            md_path = os.path.join(output_dir, f"{base_filename}.md")
            html_path = os.path.join(output_dir, f"{base_filename}.html")
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(md_report)
                
            with open(html_path, 'w', encoding='utf-8') as f:
                f.write(html_report)
                
            print(f"[+] Generated reports:")
            print(f"    - Markdown: {md_path}")
            print(f"    - HTML: {html_path}")
            
            return {
                "markdown": md_path,
                "html": html_path
            }
            
        except Exception as e:
            print(f"[-] Error generating scan report: {e}")
            return {}

def test():
    burp_api = BurpAPI()
    scan_id = burp_api.start_scan([ "https://8x8.vc/"]) #"https://hillstar.nl",
    if scan_id:
        # Đợi scan hoàn thành
        bugs = burp_api.monitor_scan_progress(scan_id)
        if bugs:
            # Tạo báo cáo
            reports = burp_api.generate_scan_report(scan_id)
            print(f"[+] Generated reports: {reports}")
    
if __name__ == "__main__":
    test()