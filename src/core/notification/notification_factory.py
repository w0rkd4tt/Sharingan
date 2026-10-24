#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Factory pattern để tạo notification service phù hợp
"""

import os
from typing import Optional
from .notifier import Notifier
from .whatsapp_notifier import WhatsAppNotifier


class NotificationFactory:
    """Factory class để tạo notification service"""
    
    @staticmethod
    def create_notifier(service_type: str = None) -> Optional[Notifier]:
        """
        Tạo WhatsApp notification service
        
        Args:
            service_type: Không sử dụng - chỉ dùng WhatsApp
            
        Returns:
            WhatsApp Notifier instance hoặc None nếu không có cấu hình
        """
        # Luôn sử dụng WhatsApp
        access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        recipient_number = os.getenv('WHATSAPP_RECIPIENT_NUMBER')
        
        if access_token and phone_number_id and recipient_number:
            return WhatsAppNotifier(access_token, phone_number_id, recipient_number)
        else:
            print("[!] Thiếu cấu hình WhatsApp (WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_RECIPIENT_NUMBER)")
            return None
            
    @staticmethod
    def escape_markdown(notifier: Notifier, text: str) -> str:
        """
        Escape markdown text cho WhatsApp
        
        Args:
            notifier: Notifier instance
            text: Text cần escape
            
        Returns:
            Text đã được escape (WhatsApp không cần escape)
        """
        # WhatsApp không cần escape markdown
        return text