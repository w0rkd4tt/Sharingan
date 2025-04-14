import requests
import json
import logging
from typing import Dict, Any
import os

# Configure logging
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(levelname)s - %(message)s',
#     handlers=[
#         logging.FileHandler('telegram_notifier.log'),
#         logging.StreamHandler()
#     ]
# )
logger = logging.getLogger(__name__)

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        """Initialize Telegram notifier with bot token and chat ID"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        logger.debug(f"Initialized TelegramNotifier with API URL: {self.api_url}")



    def format_issue_message(self, issue: Dict[str, Any]) -> str:
        """Format an issue into a Markdown message with length limits"""
        logger.debug(f"Formatting issue: {issue.get('name', 'N/A')}")
        
        def escape_markdown(text: str) -> str:
            """Escape special characters for Markdown"""
            special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
            for char in special_chars:
                text = text.replace(char, f"\\{char}")
            return text

        def truncate_text(text: str, max_length: int) -> str:
            """Truncate text and add ellipsis if too long"""
            if len(text) <= max_length:
                return text
            return text[:max_length-3] + "..."
        
        # Construct full URL from origin and path
        origin = issue.get('origin', '')
        path = issue.get('path', '')
        full_url = f"{origin}{path}" if origin and path else "N/A"
        
        # Basic issue information (reserve 1000 chars for this)
        message = "*💣💣 New Security Issue Found 💣💣*\n\n"
        message += f"*Issue ID*: `{issue.get('id', 'N/A')}`\n"
        message += f"*Name*: `{escape_markdown(issue.get('name', 'N/A'))}`\n"
        message += f"*Severity*: `{issue.get('severity', 'N/A')}`\n"
        message += f"*Confidence*: `{issue.get('confidence', 'N/A')}`\n"
        message += f"*URL*: `{escape_markdown(full_url)}`\n"
        
        # Add description if available (allocate 60% of remaining space)
        if "description" in issue:
            desc = issue["description"]
            # Remove HTML tags
            desc = desc.replace("<b>", "").replace("</b>", "")
            desc = desc.replace("<br>", "\n")
            desc = desc.replace("<ul>", "\n").replace("</ul>", "")
            desc = desc.replace("<li>", "• ").replace("</li>", "\n")
            desc = truncate_text(desc, 500)
            message += f"\n*Description*:\n{escape_markdown(desc)}\n"
            

        logger.debug(f"Final message length: {len(message)}")
        return message

        

    def send_message(self, message: str) -> bool:
        """Send a message to Telegram channel"""
        try:
            logger.debug(f"Sending message to chat ID: {self.chat_id}")
            logger.debug(f"Message length: {len(message)}")
            
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown",
                "disable_web_page_preview": True
            }
            
            logger.debug("Making POST request to Telegram API")
            response = requests.post(self.api_url, json=payload)
            logger.debug(f"Response status code: {response.status_code}")
            logger.debug(f"Response content: {response.text}")
            
            if response.status_code == 200:
                logger.info("Message sent successfully")
                return True
            else:
                logger.error(f"Failed to send message: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending message: {str(e)}", exc_info=True)
            return False



    def notify_alert(self, text: str) -> str:
        """Format an alert into a Markdown message"""
        logger.debug(f"Formatting alert: {text}")
        
        message = f"*🚨🚨New Alert🚨🚨*\n\n"
        message += f"*Message*: `{text}`\n"
        return message


def notify_vulnerabilities(scan_report_path: str, scan_report_path_md: str, bot_token: str, chat_id: str):
    """Read scan report and send notifications for high and medium severity issues"""
    logger.info(f"Starting vulnerability notification process for {scan_report_path}")
    
    # Initialize notifier
    notifier = TelegramNotifier(bot_token, chat_id)
    
    try:
        # Read and parse the scan report
        logger.debug(f"Reading scan report from {scan_report_path}")
        with open(scan_report_path, 'r') as f:
            report_data = json.load(f)
        
        # # Get issues from the report
        # issues = report_data.get("vulnerabilities", {})
        
        # # Only process high and medium severity issues
        # for severity in ["high", "medium"]:
        #     severity_issues = issues.get(severity, [])
        #     logger.info(f"Processing {len(severity_issues)} {severity} severity issues")
            
        #     for issue_data in severity_issues:
        #         if "issue" in issue_data:
        #             logger.debug(f"Processing issue: {issue_data['issue'].get('name', 'N/A')}")
        #             message = notifier.format_issue_message(issue_data["issue"])
        #             notifier.send_message(message)
        
        # Send the MD report file if it exists

        if os.path.exists(scan_report_path_md):
            logger.info(f"Sending MD report file: {scan_report_path_md}")
            with open(scan_report_path_md, 'rb') as md_file:
                files = {
                    'document': md_file
                }
                payload = {
                    'chat_id': chat_id,
                    'caption': '📄 Full Scan Report'
                }
                response = requests.post(
                    f"https://api.telegram.org/bot{bot_token}/sendDocument",
                    data=payload,
                    files=files
                )
                if response.status_code == 200:
                    logger.info("MD report file sent successfully")
                else:
                    logger.error(f"Failed to send MD report: {response.text}")
                    
    except Exception as e:
        logger.error(f"Error processing scan report: {str(e)}", exc_info=True)

# if __name__ == "__main__":
#     logger.info("Starting Telegram notification script")
    
#     # Configuration 
#     BOT_TOKEN = "7599958363:AAF0d5Z8TUKQTzSU9tzRwkTYHBeC5e_x0MM"
#     CHAT_ID = "1106225659"
#     SCAN_REPORT = "reports/scan_report_36_2025_04_12-03_07_32.json"
    
#     # Send notifications and report
#     notify_vulnerabilities(SCAN_REPORT, BOT_TOKEN, CHAT_ID)
    
#     logger.info("Finished processing notifications")

