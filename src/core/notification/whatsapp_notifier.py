import os
import requests
from typing import Optional
from .notifier import Notifier


class WhatsAppNotifier(Notifier):
    """Lớp xử lý gửi thông báo đến WhatsApp Business API"""
    
    def __init__(self, access_token: str, phone_number_id: str, recipient_number: str):
        """
        Khởi tạo bộ thông báo WhatsApp
        
        Args:
            access_token: Access token từ WhatsApp Business API
            phone_number_id: ID của số điện thoại WhatsApp Business
            recipient_number: Số điện thoại người nhận (format: +84xxxxxxxxx)
        """
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.recipient_number = recipient_number
        self.api_url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
    def send_message(self, message: str) -> bool:
        """
        Gửi tin nhắn đến WhatsApp
        
        Args:
            message: Nội dung tin nhắn cần gửi
            
        Returns:
            bool: True nếu gửi thành công, False nếu có lỗi
        """
        try:
            url = f"{self.api_url}/messages"
            data = {
                "messaging_product": "whatsapp",
                "to": self.recipient_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            response = requests.post(url, json=data, headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            print(f"[!] Lỗi khi gửi thông báo WhatsApp: {str(e)}")
            return False
            
    def send_document(self, file_path: str, caption: Optional[str] = None) -> bool:
        """
        Gửi tài liệu đến WhatsApp
        
        Args:
            file_path: Đường dẫn đến tệp cần gửi
            caption: Chú thích cho tệp (tùy chọn)
            
        Returns:
            bool: True nếu gửi thành công, False nếu có lỗi
        """
        try:
            # Bước 1: Upload file để lấy media ID
            media_id = self._upload_media(file_path)
            if not media_id:
                return False
                
            # Bước 2: Gửi document với media ID
            url = f"{self.api_url}/messages"
            data = {
                "messaging_product": "whatsapp",
                "to": self.recipient_number,
                "type": "document",
                "document": {
                    "id": media_id,
                    "filename": os.path.basename(file_path)
                }
            }
            
            if caption:
                data["document"]["caption"] = caption
                
            response = requests.post(url, json=data, headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            print(f"[!] Lỗi khi gửi tài liệu qua WhatsApp: {str(e)}")
            return False
            
    def _upload_media(self, file_path: str) -> Optional[str]:
        """
        Upload media file lên WhatsApp servers
        
        Args:
            file_path: Đường dẫn đến file cần upload
            
        Returns:
            str: Media ID nếu upload thành công, None nếu thất bại
        """
        try:
            url = f"{self.api_url}/media"
            
            # Map file extensions to MIME types supported by WhatsApp
            mime_types = {
                '.pdf': 'application/pdf',
                '.txt': 'text/plain',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel',
                '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.ppt': 'application/vnd.ms-powerpoint',
                '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.webp': 'image/webp',
                '.mp4': 'video/mp4',
                '.mp3': 'audio/mpeg',
                '.aac': 'audio/aac',
                '.amr': 'audio/amr',
                '.ogg': 'audio/ogg',
                '.opus': 'audio/opus'
            }
            
            # Get file extension and determine MIME type
            file_ext = os.path.splitext(file_path)[1].lower()
            mime_type = mime_types.get(file_ext, 'application/octet-stream')
            
            # Convert .md files to .txt for WhatsApp compatibility
            if file_ext == '.md':
                mime_type = 'text/plain'
            
            with open(file_path, 'rb') as file:
                files = {
                    'file': (os.path.basename(file_path), file, mime_type)
                }
                data = {
                    'messaging_product': 'whatsapp'
                }
                
                response = requests.post(
                    url, 
                    data=data, 
                    files=files,
                    headers={"Authorization": f"Bearer {self.access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json().get('id')
                else:
                    print(f"[!] Upload media thất bại: {response.text}")
                    return None
                    
        except Exception as e:
            print(f"[!] Lỗi khi upload media: {str(e)}")
            return None
            
    def send_template_message(self, template_name: str, language_code: str = "vi", parameters: list = None) -> bool:
        """
        Gửi tin nhắn template (cần được approve bởi WhatsApp)
        
        Args:
            template_name: Tên template đã được approve
            language_code: Mã ngôn ngữ (mặc định: vi)
            parameters: Danh sách các tham số cho template
            
        Returns:
            bool: True nếu gửi thành công, False nếu có lỗi
        """
        try:
            url = f"{self.api_url}/messages"
            data = {
                "messaging_product": "whatsapp",
                "to": self.recipient_number,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    }
                }
            }
            
            if parameters:
                data["template"]["components"] = [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": param} for param in parameters]
                }]
                
            response = requests.post(url, json=data, headers=self.headers)
            return response.status_code == 200
        except Exception as e:
            print(f"[!] Lỗi khi gửi template message: {str(e)}")
            return False