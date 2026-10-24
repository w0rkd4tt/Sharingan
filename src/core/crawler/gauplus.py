import os
import subprocess
from typing import Set

# File: src/core/crawler/gauplus.py

class Gauplus:
    """Wrapper cho công cụ gauplus/gau"""
    
    def __init__(self, target: str, output_dir: str):
        """
        Khởi tạo wrapper gauplus/gau
        
        Args:
            target: Tên miền mục tiêu
            output_dir: Thư mục đầu ra để lưu kết quả
        """
        self.target = target
        self.output_dir = output_dir
        self.output_file = os.path.join(output_dir, "gauplus_output.txt")
    
    def run(self) -> Set[str]:
        """
        Chạy gauplus/gau để tìm URL từ các nguồn khác nhau
        
        Returns:
            Set[str]: Tập hợp các URL tìm thấy
        """
        print(f"[+] Đang chạy gau cho {self.target}...")
        
        # Thử chạy gauplus trước, nếu không có thì chạy gau
        try:
            cmd = f"echo {self.target} | gauplus --o {self.output_file}"
            subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            print(f"[!] Lỗi khi chạy gauplus: {str(e)}")
            print("[!] Thử chạy gau...")
            
            try:
                cmd = f"echo {self.target} | gau --o {self.output_file}"
                subprocess.run(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            except Exception as e:
                print(f"[!] Lỗi khi chạy gau: {str(e)}")
        
        # Đọc kết quả
        urls = set()
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r') as f:
                urls = set(line.strip() for line in f if line.strip())
            
            print(f"[+] gau tìm thấy {len(urls)} URL.")
        else:
            print("[!] gau không tạo ra tệp đầu ra.")
        
        return urls

