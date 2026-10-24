#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module các thành phần quét bổ sung cho SharinganV2
"""

import os
import json
import time
import datetime
import requests
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Set, Any, Optional

from src.core.notification.notifier import Notifier


# File: src/core/scanner/fuzzer.py
class Fuzzer:
    """Lớp thực hiện fuzzing các URL có tham số"""
    
    def __init__(self, templates_dir: str, threads: int = 10, verbose: bool = False):
        """
        Khởi tạo fuzzer
        
        Args:
            templates_dir: Thư mục chứa các template fuzzing
            threads: Số luồng chạy song song
            verbose: Bật chế độ thông báo chi tiết
        """
        self.templates_dir = templates_dir
        self.threads = threads
        self.verbose = verbose
        self.templates = self._load_templates()
    
    def _load_templates(self) -> List[Dict]:
        """
        Tải các template fuzzing từ thư mục template
        
        Returns:
            List[Dict]: Danh sách các template
        """
        templates = []
        
        if not os.path.exists(self.templates_dir):
            print(f"[!] Thư mục template không tồn tại: {self.templates_dir}")
            return templates
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.templates_dir, filename), 'r') as f:
                        template = json.load(f)
                        templates.append(template)
                except json.JSONDecodeError:
                    print(f"[!] Lỗi khi phân tích tệp template: {filename}")
        
        return templates
    
    def run_fuzzing(self, parameter_urls: Set[str]) -> List[Dict]:
        """
        Thực hiện fuzzing trên các URL có tham số
        
        Args:
            parameter_urls: Tập hợp các URL có tham số
            
        Returns:
            List[Dict]: Danh sách các lỗ hổng tiềm ẩn
        """
        if not self.templates:
            print("[!] Không tìm thấy template fuzzing nào.")
            return []
        
        print(f"[+] Đang thực hiện fuzzing trên {len(parameter_urls)} URL với {len(self.templates)} templates...")
        vulnerabilities = []
        
        # Sử dụng ThreadPoolExecutor để fuzzing song song
        with ThreadPoolExecutor(max_workers=self.threads) as executor:
            futures = []
            
            for url in parameter_urls:
                for template in self.templates:
                    futures.append(
                        executor.submit(self._fuzz_url_with_template, url, template)
                    )
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    vulnerabilities.append(result)
                    print(f"[!] Phát hiện lỗ hổng tiềm ẩn: {result['vulnerability_type']} tại {result['url']}")
        
        return vulnerabilities
    
    def _fuzz_url_with_template(self, url: str, template: Dict) -> Optional[Dict]:
        """
        Thực hiện fuzzing một URL với một template cụ thể
        
        Args:
            url: URL cần fuzzing
            template: Template fuzzing
            
        Returns:
            Optional[Dict]: Thông tin lỗ hổng nếu phát hiện, None nếu không
        """
        try:
            parsed_url = urlparse(url)
            query_params = parsed_url.query.split('&')
            
            # Thay thế giá trị tham số với payloads từ template
            for param in query_params:
                if '=' in param:
                    param_name, param_value = param.split('=', 1)
                    
                    for payload in template.get('payloads', []):
                        # Tạo URL mới với payload
                        new_url = url.replace(f"{param_name}={param_value}", f"{param_name}={payload}")
                        
                        # Gửi request thử nghiệm
                        response = requests.get(new_url, timeout=5, allow_redirects=False)
                        
                        # Kiểm tra response có dấu hiệu lỗ hổng không
                        for pattern in template.get('patterns', []):
                            if pattern in response.text:
                                return {
                                    'url': new_url,
                                    'vulnerability_type': template.get('name', 'Unknown'),
                                    'evidence': pattern,
                                    'param': param_name,
                                    'payload': payload,
                                    'response_code': response.status_code
                                }
            
            return None
        except Exception as e:
            if self.verbose:
                print(f"[!] Lỗi khi fuzz URL {url}: {str(e)}")
            return None
