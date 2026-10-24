
# File: src/config/env_creator.py

import os
import json

def create_sample_env_file(output_path: str = ".env.example"):
    """
    Tạo file .env mẫu với các cấu hình cần thiết
    
    Args:
        output_path: Đường dẫn đến file .env mẫu
    """
    env_content = """# Cấu hình cho SharinganV2
# Thông tin API Burp Suite
BURP_API_URL=http://localhost:1337/v0.1
BURP_API_KEY=your_burp_api_key_here

# Thông tin WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_whatsapp_phone_number_id_here
WHATSAPP_RECIPIENT_NUMBER=+84xxxxxxxxx

# WhatsApp notification is always used

# Thư mục template
TEMPLATES_DIR=src/template

# Cấu hình tùy chọn khác
ENABLE_FUZZING=false
"""
    
    with open(output_path, 'w') as f:
        f.write(env_content)
    
    print(f"[+] Đã tạo file {output_path} mẫu")
