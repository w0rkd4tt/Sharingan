
from dotenv import load_dotenv
import requests
import json
import logging
import urllib.parse
import time 
import os
from datetime import datetime
from ..notification.tele_notifyer import TelegramNotifier

class Scanner:
    def __init__(self, burp_api_url, bot_token=None, chat_id=None):
        """
        Initialize Scanner with API URL and optional Telegram notification settings
        """
        self.BURP_API_URL = burp_api_url
        self.notifier = TelegramNotifier(bot_token, chat_id) if bot_token and chat_id else None
        self.headers = {"Content-Type": "application/json"}
        
        # Constants
        self.SLEEP_TIME = 30  # seconds
        self.MAX_PAUSE_TIME = 15 * 60  # 15 minutes
        
        # Configure logging
        logging.basicConfig(level=logging.DEBUG, 
                          format="%(asctime)s - %(levelname)s - %(message)s")

    def create_scan(self, target_urls, scan_configs, username=None, password=None):
        """Create a scan with multiple URLs and configurations"""
        # Prepare scan configurations
        scan_configurations = [
            {"type": "NamedConfiguration", "name": config_name}
            for config_name in scan_configs
        ]

        data = {
            "urls": target_urls,
            "scan_configurations": scan_configurations,
        }

        if username and password:
            data["application_logins"] = [{
                "type": "UsernameAndPasswordLogin",
                "username": username,
                "password": password
            }]

        logging.debug(f"Sending POST request to {self.BURP_API_URL}/scan with data: {data}")
        response = requests.post(
            f"{self.BURP_API_URL}/scan", 
            headers=self.headers, 
            data=json.dumps(data)
        )
        
        if response.status_code == 201:
            location_header = response.headers.get("Location")
            if location_header:
                scan_id = location_header.split("/")[-1]
                logging.info(f"Scan created successfully. Scan ID: {scan_id}")
                return scan_id
        
        logging.error(f"Failed to create scan: {response.status_code}")
        logging.error(response.text)
        return None

    def check_scan_status(self, scan_id, last_issue_count=0):
        """Check scan status and notify new vulnerabilities"""
        url = f"{self.BURP_API_URL}/scan/{scan_id}"
        logging.debug(f"Sending GET request to {url}")
        
        try:
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                response_json = response.json()
                scan_status = response_json.get("scan_status")
                
                if self.notifier and "issue_events" in response_json:
                    current_issues = response_json["issue_events"]
                    current_count = len(current_issues)
                    
                    if current_count > last_issue_count:
                        self._notify_new_issues(
                            current_issues[last_issue_count:current_count]
                        )
                    
                    return scan_status, current_count
                
                return scan_status, last_issue_count
                
            elif response.status_code == 202:
                return "running", last_issue_count
                
            logging.error(f"Failed to fetch scan status: {response.status_code}")
            return None, last_issue_count
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Error while fetching scan status: {e}")
            return None, last_issue_count

    def generate_report(self, scan_id, format="md", output_dir="reports"):
        """Generate a detailed report from scan results"""
        # ...existing code for generate_report...

    def run_scan(self, target_urls, scan_configs, username=None, password=None):
        """Run complete scan process with monitoring and reporting"""
        scan_id = self.create_scan(target_urls, scan_configs, username, password)
        if not scan_id:
            return False

        pause_counter = 0
        last_issue_count = 0

        while True:
            status, last_issue_count = self.check_scan_status(scan_id, last_issue_count)
            
            if status == "completed":
                self._handle_scan_completion(scan_id)
                return True
            elif status == "failed":
                self._notify_scan_failure()
                return False
            elif status == "paused":
                pause_counter += self.SLEEP_TIME
                if pause_counter >= self.MAX_PAUSE_TIME:
                    self._notify_scan_timeout(pause_counter)
                    return False
                self._notify_scan_paused(pause_counter)
            elif status == "running":
                pause_counter = 0
                logging.info("Scan is still running...")
            else:
                logging.warning(f"Unexpected status: {status}")
                pause_counter = 0

            time.sleep(self.SLEEP_TIME)

    def _notify_new_issues(self, new_issues):
        """Handle notification of new issues"""
        for issue in new_issues:
            severity = issue["issue"].get("severity", "").lower()
            if severity in ["high", "medium"]:
                message = self.notifier.format_issue_message(issue["issue"])
                self.notifier.send_message(message)
                logging.info(f"Notified new {severity} severity issue")

    def _handle_scan_completion(self, scan_id):
        """Handle successful scan completion"""
        logging.info("Scan completed successfully.")
        md_report = self.generate_report(scan_id, format="md")
        json_report = self.generate_report(scan_id, format="json")
        
        if self.notifier:
            try:
                self.notifier.notify_vulnerabilities(json_report, md_report)
            except Exception as e:
                logging.error(f"Error sending final notification: {e}")

        if md_report and json_report:
            logging.info(f"Reports generated:\nMarkdown: {md_report}\nJSON: {json_report}")

    def _notify_scan_failure(self):
        """Handle scan failure notification"""
        message = "Scan failed."
        if self.notifier:
            alert_text = self.notifier.notify_alert(message)
            self.notifier.send_message(alert_text)
        logging.error(message)

    def _notify_scan_timeout(self, pause_duration):
        """Handle scan timeout notification"""
        message = f"Scan has been paused for {pause_duration/60} minutes. Stopping scan."
        if self.notifier:
            alert_text = self.notifier.notify_alert(message)
            self.notifier.send_message(alert_text)
        logging.warning(message)

    def _notify_scan_paused(self, pause_duration):
        """Handle scan pause notification"""
        message = f"Scan is paused (for {pause_duration/60:.1f} minutes)."
        if self.notifier:
            alert_text = self.notifier.notify_alert(message)
            self.notifier.send_message(alert_text)
        logging.info(message)