import os
import subprocess
from typing import Set

# File: src/core/crawler/hakrawler.py

class Hakrawler:
    """Wrapper cho công cụ hakrawler"""
    
    def __init__(self, target: str, output_dir: str):
        """
        Khởi tạo wrapper hakrawler
        
        Args:
            target: Tên miền mục tiêu
            output_dir: Thư mục đầu ra để lưu kết quả
        """
        self.target = target
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, "hakrawler_output.txt")
    
    def run(self) -> Set[str]:
        """
        Chạy hakrawler để crawl website
        
        Returns:
            Set[str]: Tập hợp các URL tìm thấy
        """
        print(f"[+] Đang chạy hakrawler cho {self.target}...")
        cmd = f"echo https://{self.target} | hakrawler -depth 3 -subs > {self.output_file}"
        
        try:
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f"[!] Lỗi khi chạy hakrawler: {str(e)}")
        
        # Đọc kết quả
        urls = set()
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r') as f:
                urls = set(line.strip() for line in f if line.strip())
            
            print(f"[+] hakrawler tìm thấy {len(urls)} URL.")
        else:
            print("[!] hakrawler không tạo ra tệp đầu ra.")
        
        return urls
