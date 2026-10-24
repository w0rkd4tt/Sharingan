#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple WhatsApp Notification Microservice
Send notifications via WhatsApp Business API
"""

import os
import requests
from datetime import datetime
from flask import Flask, request, jsonify

app = Flask(__name__)

# Add CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# WhatsApp configuration from environment
WHATSAPP_ACCESS_TOKEN = os.getenv('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_PHONE_NUMBER_ID = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
WHATSAPP_RECIPIENT_NUMBER = os.getenv('WHATSAPP_RECIPIENT_NUMBER', '')


class WhatsAppNotifier:
    """Simple WhatsApp API client"""
    
    def __init__(self, access_token, phone_number_id, recipient_number):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.recipient_number = recipient_number
        self.api_url = f"https://graph.facebook.com/v18.0/{phone_number_id}"
        
    def send_message(self, message):
        """Send text message"""
        url = f"{self.api_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": self.recipient_number,
            "type": "text",
            "text": {"body": message}
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, str(e)
    
    def send_document(self, media_id, filename, caption=None):
        """Send document with media ID"""
        url = f"{self.api_url}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        data = {
            "messaging_product": "whatsapp",
            "to": self.recipient_number,
            "type": "document",
            "document": {
                "id": media_id,
                "filename": filename
            }
        }
        
        if caption:
            data["document"]["caption"] = caption
            
        try:
            response = requests.post(url, json=data, headers=headers)
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, str(e)


# Initialize notifier
notifier = WhatsAppNotifier(
    WHATSAPP_ACCESS_TOKEN,
    WHATSAPP_PHONE_NUMBER_ID,
    WHATSAPP_RECIPIENT_NUMBER
)


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    configured = all([WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_RECIPIENT_NUMBER])
    
    return jsonify({
        'status': 'healthy',
        'service': 'whatsapp-notification',
        'configured': configured,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/notify/message', methods=['POST'])
def send_notification():
    """Send WhatsApp message"""
    data = request.get_json()
    
    if not data or 'message' not in data:
        return jsonify({'error': 'Missing required field: message'}), 400
    
    message = data['message']
    
    # Check configuration
    if not all([WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_RECIPIENT_NUMBER]):
        return jsonify({'error': 'WhatsApp not configured'}), 500
    
    # Send message
    success, result = notifier.send_message(message)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Notification sent',
            'result': result
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 500


@app.route('/api/notify/scan-report', methods=['POST'])
def send_scan_report():
    """Send scan report notification"""
    data = request.get_json()
    
    if not data or 'target' not in data:
        return jsonify({'error': 'Missing required field: target'}), 400
    
    target = data['target']
    summary = data.get('summary', {})
    
    # Format message
    message = f"""🔍 Scan Report - {target}

📊 Summary:
• Total URLs: {summary.get('total_urls', 0)}
• Parameter URLs: {summary.get('parameter_urls', 0)}
• Issues Found: {summary.get('issues_found', 0)}

🔴 High: {summary.get('high_issues', 0)}
🟠 Medium: {summary.get('medium_issues', 0)}
🟡 Low: {summary.get('low_issues', 0)}

⏱️ Completed: {datetime.now().strftime('%Y-%m-%d %H:%M')}"""
    
    # Send notification
    success, result = notifier.send_message(message)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Scan report sent'
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 500


@app.route('/api/notify/alert', methods=['POST'])
def send_alert():
    """Send alert notification"""
    data = request.get_json()
    
    if not data or 'title' not in data:
        return jsonify({'error': 'Missing required field: title'}), 400
    
    title = data['title']
    description = data.get('description', '')
    severity = data.get('severity', 'info')
    
    # Severity emojis
    severity_emojis = {
        'critical': '🚨',
        'high': '🔴',
        'medium': '🟠',
        'low': '🟡',
        'info': 'ℹ️'
    }
    
    emoji = severity_emojis.get(severity, 'ℹ️')
    
    # Format message
    message = f"""{emoji} {title}

{description}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""
    
    # Send notification
    success, result = notifier.send_message(message)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Alert sent'
        })
    else:
        return jsonify({
            'success': False,
            'error': result
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    print(f"[*] Starting WhatsApp Notification Service on port {port}")
    print(f"[*] Recipient: {WHATSAPP_RECIPIENT_NUMBER}")
    app.run(host='0.0.0.0', port=port, debug=True)