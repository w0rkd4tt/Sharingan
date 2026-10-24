#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to help refresh WhatsApp access token
"""

import requests
import json

def exchange_token(short_lived_token, app_id, app_secret):
    """
    Exchange short-lived token for long-lived token
    """
    url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        "grant_type": "fb_exchange_token",
        "client_id": app_id,
        "client_secret": app_secret,
        "fb_exchange_token": short_lived_token
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return data.get('access_token')
    else:
        print(f"Error: {response.json()}")
        return None

def main():
    print("=== WhatsApp Token Refresh Tool ===\n")
    
    print("Để lấy token mới:")
    print("1. Truy cập: https://developers.facebook.com/apps/")
    print("2. Chọn app WhatsApp Business")
    print("3. Vào WhatsApp > API Setup > Generate Token")
    print("4. Copy token và App ID, App Secret\n")
    
    print("Nhập thông tin:")
    short_token = input("Short-lived token: ").strip()
    app_id = input("App ID: ").strip()
    app_secret = input("App Secret: ").strip()
    
    if short_token and app_id and app_secret:
        print("\nĐang exchange token...")
        long_token = exchange_token(short_token, app_id, app_secret)
        
        if long_token:
            print(f"\n✅ Long-lived token (60 ngày):")
            print(f"{long_token}")
            print(f"\nCập nhật vào file .env:")
            print(f'WHATSAPP_ACCESS_TOKEN="{long_token}"')
        else:
            print("\n❌ Không thể exchange token")
    else:
        print("\n❌ Thiếu thông tin bắt buộc")

if __name__ == "__main__":
    main()