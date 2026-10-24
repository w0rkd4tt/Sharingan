#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module tạo các file cấu hình mẫu cho SharinganV2
"""

import os
import json

# File: src/config/config_creator.py
def create_sample_severity_config(config_dir: str = "src/config"):
    """
    Tạo tệp cấu hình mẫu để phân loại mức độ nghiêm trọng của lỗ hổng
    
    Args:
        config_dir: Thư mục đầu ra để lưu tệp cấu hình
    """
    severity_config = {
        "high": [
            "xss",
            "sqli",
            "rce",
            "xxe",
            "ssti",
            "lfi",
            "path traversal"
        ],
        "medium": [
            "ssrf",
            "open redirect",
            "idor",
            "csrf",
            "clickjacking",
            "cors misconfiguration"
        ],
        "low": [
            "information disclosure",
            "brute force",
            "rate limit",
            "http headers missing",
            "cookie flags missing"
        ],
        "info": [
            "other"
        ]
    }
    
    os.makedirs(config_dir, exist_ok=True)
    with open(os.path.join(config_dir, "severity.json"), 'w') as f:
        json.dump(severity_config, f, indent=4)
    
    print(f"[+] Đã tạo tệp cấu hình mức độ nghiêm trọng mẫu trong thư mục '{config_dir}'")
