#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module lọc URL dựa trên extension
"""

import os
from typing import Set, Dict
from urllib.parse import urlparse, parse_qs, urlencode

class URLFilter:
    """Lớp lọc URL dựa trên extension"""
    
    # Danh sách các extension cần loại bỏ
    EXCLUDED_EXTENSIONS = {
        # Font files
        'woff', 'woff2', 'ttf', 'otf', 'eot',
        # Images
        'png', 'jpg', 'jpeg', 'gif', 'svg', 'ico', 'webp',
        # Styles
        'css', 'scss', 'sass',
        # Scripts
        'js', 'js.map',
        # Media
        'mp3', 'mp4', 'webm', 'ogg',
        # Documents
        'pdf', 'doc', 'docx', 'xls', 'xlsx',
        # Archives
        'zip', 'rar', '7z', 'tar', 'gz',
        # Others
        'xml', 'json', 'txt', 'md'
    }
    
    def __init__(self, target: str):
        """
        Khởi tạo bộ lọc URL
        
        Args:
            target: Tên miền mục tiêu
        """
        self.target = target
    
    def _normalize_url(self, url: str) -> str:
        """
        Chuẩn hóa URL bằng cách giữ nguyên tên tham số nhưng xóa giá trị
        
        Args:
            url: URL cần chuẩn hóa
            
        Returns:
            str: URL đã được chuẩn hóa
        """
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        # Tạo dict mới với giá trị rỗng cho mỗi tham số
        normalized_params = {k: [''] for k in query_params.keys()}
        
        # Tạo URL mới với các tham số đã chuẩn hóa
        normalized_query = urlencode(normalized_params, doseq=True)
        
        # Kết hợp các phần của URL
        return parsed._replace(query=normalized_query).geturl()
    
    def filter_urls(self, urls: Set[str]) -> Set[str]:
        """
        Lọc các URL dựa trên extension và tham số
        
        Args:
            urls: Tập hợp các URL cần lọc
            
        Returns:
            Set[str]: Tập hợp các URL đã được lọc
        """
        filtered_urls = set()
        normalized_groups: Dict[str, str] = {}  # normalized_url -> original_url
        
        for url in urls:
            # Bỏ qua các URL không thuộc target
            if self.target not in url:
                continue
                
            # Lấy extension từ URL
            path = urlparse(url).path
            extension = os.path.splitext(path)[1].lower().lstrip('.')
            
            # Nếu không có extension hoặc extension không nằm trong danh sách loại trừ
            if not extension or extension not in self.EXCLUDED_EXTENSIONS:
                # Chuẩn hóa URL để kiểm tra tham số
                normalized_url = self._normalize_url(url)
                
                # Nếu URL đã chuẩn hóa chưa tồn tại trong nhóm, thêm vào
                if normalized_url not in normalized_groups:
                    normalized_groups[normalized_url] = url
                    filtered_urls.add(url)
        
        return filtered_urls
    
    def run(self, urls: Set[str]) -> Set[str]:
        """
        Chạy quá trình lọc URL
        
        Args:
            urls: Tập hợp các URL cần lọc
            
        Returns:
            Set[str]: Tập hợp các URL đã được lọc
        """
        print(f"[*] Đang lọc {len(urls)} URL...")
        filtered_urls = self.filter_urls(urls)
        print(f"[+] Đã lọc xong: {len(filtered_urls)} URL còn lại")
        return filtered_urls 