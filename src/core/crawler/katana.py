import os
import subprocess
from typing import Set

# File: src/core/crawler/katana.py

class Katana:
    """Wrapper cho công cụ katana"""
    
    def __init__(self, target: str, output_dir: str):
        """
        Khởi tạo wrapper katana
        
        Args:
            target: Tên miền mục tiêu
            output_dir: Thư mục đầu ra để lưu kết quả
        """
        self.target = target
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, "katana_output.txt")
    
    def run(self) -> Set[str]:
        """
        Chạy katana để thực hiện crawling nâng cao
        
        Returns:
            Set[str]: Tập hợp các URL tìm thấy
        """
        print(f"[+] Đang chạy katana cho {self.target}...")
        cmd = f"katana -u https://{self.target} -jc -o {self.output_file}"
        
        try:
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f"[!] Lỗi khi chạy katana: {str(e)}")
        
        # Đọc kết quả
        urls = set()
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r') as f:
                urls = set(line.strip() for line in f if line.strip())
            
            print(f"[+] katana tìm thấy {len(urls)} URL.")
        else:
            print("[!] katana không tạo ra tệp đầu ra.")
        
        return urls