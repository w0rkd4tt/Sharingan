#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module quản lý cấu hình cho SharinganV2
"""

import os
import json
from dotenv import load_dotenv
from typing import Any, Dict, Optional


class ConfigManager:
    """Lớp quản lý cấu hình cho SharinganV2"""
    
    def __init__(self, env_file: str = ".env", config_dir: str = "src/config"):
        """
        Khởi tạo lớp quản lý cấu hình
        
        Args:
            env_file: Đường dẫn đến file .env
            config_dir: Thư mục chứa các file cấu hình
        """
        self.env_file = env_file
        self.config_dir = config_dir
        self.severity_config = {}
        
        # Tải biến môi trường từ file .env
        if os.path.exists(env_file):
            load_dotenv(env_file)
            
        # Tải cấu hình phân loại mức độ nghiêm trọng nếu có
        severity_config_path = os.path.join(config_dir, "severity.json")
        if os.path.exists(severity_config_path):
            try:
                with open(severity_config_path, 'r') as f:
                    self.severity_config = json.load(f)
            except json.JSONDecodeError:
                print(f"[!] Lỗi khi đọc file cấu hình {severity_config_path}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Lấy giá trị của biến môi trường
        
        Args:
            key: Tên biến môi trường
            default: Giá trị mặc định nếu không tìm thấy
            
        Returns:
            Any: Giá trị của biến môi trường hoặc giá trị mặc định
        """
        return os.getenv(key, default)
    
    def get_severity_config(self) -> Dict:
        """
        Lấy cấu hình phân loại mức độ nghiêm trọng
        
        Returns:
            Dict: Cấu hình phân loại mức độ nghiêm trọng
        """
        return self.severity_config
    
    def get_severity(self, vuln_type: str) -> str:
        """
        Xác định mức độ nghiêm trọng của loại lỗ hổng
        
        Args:
            vuln_type: Loại lỗ hổng
            
        Returns:
            str: Mức độ nghiêm trọng (high, medium, low, info)
        """
        vuln_type_lower = vuln_type.lower()
        
        for severity, vuln_types in self.severity_config.items():
            for vt in vuln_types:
                if vt in vuln_type_lower:
                    return severity
        
        # Mặc định là info nếu không tìm thấy
        return "info"
    
    def save_to_json(self, data: Dict, filename: str) -> bool:
        """
        Lưu dữ liệu vào file JSON
        
        Args:
            data: Dữ liệu cần lưu
            filename: Tên file
            
        Returns:
            bool: True nếu lưu thành công, False nếu có lỗi
        """
        try:
            with open(filename, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"[!] Lỗi khi lưu file {filename}: {str(e)}")
            return False
    
    def load_from_json(self, filename: str) -> Optional[Dict]:
        """
        Tải dữ liệu từ file JSON
        
        Args:
            filename: Tên file
            
        Returns:
            Dict: Dữ liệu từ file hoặc None nếu có lỗi
        """
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            print(f"[!] Lỗi khi đọc file {filename}: {str(e)}")
            return None