#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WhatsApp Personal Notifier - Sử dụng cho tài khoản cá nhân
Sử dụng pywhatkit hoặc selenium để gửi tin nhắn
"""

import os
import time
from typing import Optional
from .notifier import Notifier

# Method 1: Using pywhatkit (đơn giản nhất)
try:
    import pywhatkit as kit
    PYWHATKIT_AVAILABLE = True
except ImportError:
    PYWHATKIT_AVAILABLE = False

# Method 2: Using selenium với WhatsApp Web
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


class WhatsAppPersonalNotifier(Notifier):
    """Lớp xử lý gửi thông báo WhatsApp cho tài khoản cá nhân"""
    
    def __init__(self, phone_number: str, method: str = "pywhatkit"):
        """
        Khởi tạo bộ thông báo WhatsApp cá nhân
        
        Args:
            phone_number: Số điện thoại người nhận (format: +84xxxxxxxxx)
            method: Phương thức gửi ("pywhatkit" hoặc "selenium")
        """
        self.phone_number = phone_number
        self.method = method
        
        # Validate phone number format
        if not phone_number.startswith("+"):
            raise ValueError("Phone number must start with country code (e.g., +84)")
            
        # Check available methods
        if method == "pywhatkit" and not PYWHATKIT_AVAILABLE:
            print("[!] pywhatkit not installed. Install with: pip install pywhatkit")
            print("[!] Switching to selenium method...")
            self.method = "selenium"
            
        if method == "selenium" and not SELENIUM_AVAILABLE:
            print("[!] selenium not installed. Install with: pip install selenium")
            raise ImportError("No WhatsApp sending method available")
            
        if self.method == "selenium":
            self.driver = None
            
    def _init_selenium_driver(self):
        """Khởi tạo Selenium WebDriver"""
        if self.driver is None:
            # Sử dụng Chrome driver
            options = webdriver.ChromeOptions()
            options.add_argument("--user-data-dir=./whatsapp_session")  # Lưu session
            self.driver = webdriver.Chrome(options=options)
            
            # Mở WhatsApp Web
            self.driver.get("https://web.whatsapp.com")
            
            print("[*] Please scan QR code if needed...")
            print("[*] Press Enter when WhatsApp Web is ready...")
            input()
            
    def send_message(self, message: str) -> bool:
        """
        Gửi tin nhắn đến WhatsApp
        
        Args:
            message: Nội dung tin nhắn cần gửi
            
        Returns:
            bool: True nếu gửi thành công, False nếu có lỗi
        """
        try:
            if self.method == "pywhatkit":
                return self._send_with_pywhatkit(message)
            elif self.method == "selenium":
                return self._send_with_selenium(message)
            else:
                print(f"[!] Unknown method: {self.method}")
                return False
                
        except Exception as e:
            print(f"[!] Lỗi khi gửi thông báo WhatsApp: {str(e)}")
            return False
            
    def _send_with_pywhatkit(self, message: str) -> bool:
        """Gửi tin nhắn sử dụng pywhatkit"""
        try:
            # Gửi tin nhắn ngay lập tức (wait_time=10 seconds)
            kit.sendwhatmsg_instantly(
                phone_no=self.phone_number,
                message=message,
                wait_time=10,  # Đợi 10 giây để WhatsApp Web load
                tab_close=True  # Đóng tab sau khi gửi
            )
            print(f"[✓] Message sent to {self.phone_number}")
            return True
            
        except Exception as e:
            print(f"[!] pywhatkit error: {str(e)}")
            return False
            
    def _send_with_selenium(self, message: str) -> bool:
        """Gửi tin nhắn sử dụng Selenium"""
        try:
            # Khởi tạo driver nếu chưa có
            self._init_selenium_driver()
            
            # Tạo URL để mở chat với số điện thoại
            url = f"https://web.whatsapp.com/send?phone={self.phone_number}&text={message}"
            self.driver.get(url)
            
            # Đợi nút Send xuất hiện
            send_button = WebDriverWait(self.driver, 30).until(
                EC.element_to_be_clickable((By.XPATH, '//button[@data-testid="compose-btn-send"]'))
            )
            
            # Click send
            send_button.click()
            
            print(f"[✓] Message sent to {self.phone_number}")
            time.sleep(2)  # Đợi message được gửi
            
            return True
            
        except Exception as e:
            print(f"[!] Selenium error: {str(e)}")
            return False
            
    def send_document(self, file_path: str, caption: Optional[str] = None) -> bool:
        """
        Gửi tài liệu đến WhatsApp (chỉ hỗ trợ với Selenium)
        
        Args:
            file_path: Đường dẫn đến tệp cần gửi
            caption: Chú thích cho tệp (tùy chọn)
            
        Returns:
            bool: True nếu gửi thành công, False nếu có lỗi
        """
        if self.method == "pywhatkit":
            print("[!] pywhatkit does not support file sending. Use selenium method.")
            return False
            
        try:
            # Khởi tạo driver nếu chưa có
            self._init_selenium_driver()
            
            # Mở chat với số điện thoại
            url = f"https://web.whatsapp.com/send?phone={self.phone_number}"
            self.driver.get(url)
            
            # Đợi chat load
            WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="conversation-compose-box-input"]'))
            )
            
            # Click vào nút attachment
            attach_btn = self.driver.find_element(By.XPATH, '//div[@data-testid="attach-menu-plus"]')
            attach_btn.click()
            
            # Click Document option
            doc_input = self.driver.find_element(By.XPATH, '//input[@accept="*"]')
            doc_input.send_keys(os.path.abspath(file_path))
            
            # Đợi file upload
            time.sleep(3)
            
            # Thêm caption nếu có
            if caption:
                caption_input = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//div[@data-testid="media-caption-input"]'))
                )
                caption_input.send_keys(caption)
            
            # Send
            send_btn = self.driver.find_element(By.XPATH, '//span[@data-testid="send"]')
            send_btn.click()
            
            print(f"[✓] Document sent to {self.phone_number}")
            return True
            
        except Exception as e:
            print(f"[!] Error sending document: {str(e)}")
            return False
            
    def close(self):
        """Đóng browser nếu dùng Selenium"""
        if self.method == "selenium" and self.driver:
            self.driver.quit()
            self.driver = None


class WhatsAppGroupNotifier(WhatsAppPersonalNotifier):
    """Gửi tin nhắn đến WhatsApp Group"""
    
    def __init__(self, group_name: str, method: str = "selenium"):
        """
        Khởi tạo notifier cho WhatsApp Group
        
        Args:
            group_name: Tên của group
            method: Chỉ hỗ trợ selenium cho group
        """
        self.group_name = group_name
        self.method = "selenium"  # Groups chỉ work với selenium
        self.driver = None
        
        if not SELENIUM_AVAILABLE:
            raise ImportError("Selenium required for group messaging")
            
    def send_message(self, message: str) -> bool:
        """Gửi tin nhắn đến group"""
        try:
            # Khởi tạo driver
            self._init_selenium_driver()
            
            # Tìm group
            search_box = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="chat-list-search"]'))
            )
            search_box.click()
            search_box.send_keys(self.group_name)
            time.sleep(2)
            
            # Click vào group đầu tiên
            group = self.driver.find_element(By.XPATH, f'//span[@title="{self.group_name}"]')
            group.click()
            
            # Gửi message
            msg_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//div[@data-testid="conversation-compose-box-input"]'))
            )
            msg_box.send_keys(message)
            msg_box.send_keys(Keys.ENTER)
            
            print(f"[✓] Message sent to group: {self.group_name}")
            return True
            
        except Exception as e:
            print(f"[!] Error sending to group: {str(e)}")
            return False