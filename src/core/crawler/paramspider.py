#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module các wrapper cho các công cụ crawl URL
"""

import os
import subprocess
from typing import Set


# File: src/core/crawler/paramspider.py
class ParamSpider:
    """Wrapper cho công cụ ParamSpider"""
    
    def __init__(self, target: str, output_dir: str):
        """
        Khởi tạo wrapper ParamSpider
        
        Args:
            target: Tên miền mục tiêu
            output_dir: Thư mục đầu ra để lưu kết quả
        """
        self.target = target
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, "paramspider_output.txt")
    
    def run(self) -> Set[str]:
        """
        Chạy ParamSpider để tìm các URL có tham số
        
        Returns:
            Set[str]: Tập hợp các URL tìm thấy
        """
        print(f"[+] Đang chạy ParamSpider cho {self.target}...")
        cmd = [
            "python3", "tools/ParamSpider/paramspider.py",
            "-d", self.target,
            "--exclude", "woff,css,js,png,svg,jpg,jpeg,gif,ttf",
            "-o", self.output_file
        ]
        
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f"[!] Lỗi khi chạy ParamSpider: {str(e)}")
        
        # Đọc kết quả
        urls = set()
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r') as f:
                urls = set(line.strip() for line in f if line.strip())
            
            print(f"[+] ParamSpider tìm thấy {len(urls)} URL có tham số.")
        else:
            print("[!] ParamSpider không tạo ra tệp đầu ra.")
        
        return urls

