#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Module quản lý thông báo cho SharinganV2
"""

from abc import ABC, abstractmethod
from typing import Optional


# File:   find . -type d -name "__pycache__" -exec rm -r {} +
class Notifier(ABC):
    """Interface cơ bản cho các bộ thông báo"""
    
    @abstractmethod
    def send_message(self, message: str) -> bool:
        """
        Gửi tin nhắn thông báo
        
        Args:
            message: Nội dung tin nhắn
            
        Returns:
            bool: True nếu gửi thành công, False nếu có lỗi
        """
        pass
    
    @abstractmethod
    def send_document(self, file_path: str, caption: Optional[str] = None) -> bool:
        """
        Gửi tài liệu kèm theo thông báo
        
        Args:
            file_path: Đường dẫn đến tệp cần gửi
            caption: Chú thích cho tệp (tùy chọn)
            
        Returns:
            bool: True nếu gửi thành công, False nếu có lỗi
        """
        pass
