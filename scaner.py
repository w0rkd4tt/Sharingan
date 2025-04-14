from dotenv import load_dotenv
import requests
import json
import logging
import urllib.parse
import time 
import os
from datetime import datetime  
import lib.tele_notifyer as tele_notifyer

# Cấu hình logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")



def create_scan(target_urls, scan_configs, username=None, password=None):
    """
    Create a scan with multiple URLs and configurations
    Args:
        target_urls: List of URLs to scan
        scan_configs: List of scan configuration names
        username: Optional login username
        password: Optional login password
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    # Prepare scan configurations
    scan_configurations = [
        {
            "type": "NamedConfiguration",
            "name": config_name
        }
        for config_name in scan_configs
    ]

    # Prepare the base request data
    data = {
        "urls": target_urls,
        "scan_configurations": scan_configurations,
        #"resource_pool": "Product"
    }

    # Add authentication if provided
    if username and password:
        data["application_logins"] = [{
            "type": "UsernameAndPasswordLogin",
            "username": username,
            "password": password
        }]

    logging.debug(f"Sending POST request to {BURP_API_URL}/scan with data: {data}")
    response = requests.post(f"{BURP_API_URL}/scan", headers=headers, data=json.dumps(data))
    logging.debug(f"Response status code: {response.status_code}")
    logging.debug(f"Response headers: {response.headers}")
    logging.debug(f"Response text: {response.text}")
    
    if response.status_code == 201:
        location_header = response.headers.get("Location")
        if location_header:
            scan_id = location_header.split("/")[-1]
            print(f"Scan created successfully. Scan ID: {scan_id}")
            return scan_id
        else:
            print("Failed to retrieve scan ID from Location header.")
            return None
    else:
        print(f"Failed to create scan: {response.status_code}")
        print(response.text)
        return None


def check_scan_status(scan_id, notifier=None, last_issue_count=0):
    """
    Check scan status and notify new vulnerabilities immediately
    Args:
        scan_id: The scan ID to check
        notifier: TelegramNotifier instance
        last_issue_count: Count of issues from last check
    """
    headers = {
        "Content-Type": "application/json"
    }
    url = f"{BURP_API_URL}/scan/{scan_id}"
    logging.debug(f"Sending GET request to {url}")
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            response_json = response.json()
            scan_status = response_json.get("scan_status")
            
            # Check for new vulnerabilities
            if notifier and "issue_events" in response_json:
                current_issues = response_json["issue_events"]
                current_count = len(current_issues)
                
                # If there are new issues
                if current_count > last_issue_count:
                    new_issues = current_issues[last_issue_count:current_count]
                    
                    # Notify each new high/medium severity issue
                    for issue in new_issues:
                        severity = issue["issue"].get("severity", "").lower()
                        if severity in ["high", "medium"]:
                            message = notifier.format_issue_message(issue["issue"])
                            notifier.send_message(message)
                            logging.info(f"Notified new {severity} severity issue")
                
                return scan_status, current_count
            
            return scan_status, last_issue_count
            
        elif response.status_code == 202:
            return "running", last_issue_count
        else:
            logging.error(f"Failed to fetch scan status: {response.status_code}")
            return None, last_issue_count
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Error while fetching scan status: {e}")
        return None, last_issue_count

def generate_report(scan_id, format="md", output_dir="reports"):
    """Generate a detailed report from scan results with issues sorted by severity"""
    headers = {
        "Content-Type": "application/json"
    }
    url = f"{BURP_API_URL}/scan/{scan_id}"
    
    try:
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Get scan results
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.error(f"Failed to fetch scan results: {response.status_code}")
            return None
            
        data = response.json()
        timestamp = datetime.now().strftime("%Y_%m_%d-%H_%M_%S")
        
        # Sort issues by severity
        severity_order = {
            "high": 0,
            "medium": 1,
            "low": 2,
            "info": 3
        }
        
        issues = data.get("issue_events", [])
        sorted_issues = sorted(
            issues,
            key=lambda x: (
                severity_order.get(x["issue"].get("severity", "info"), 4),
                x["issue"].get("name", "")
            )
        )
        

        if format.lower() == "json":
            # Generate JSON report
            filename = f"scan_report_{scan_id}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            # Prepare JSON structure
            report_data = {
                "summary": {
                    "scan_id": scan_id,
                    "status": data.get("scan_status"),
                    "timestamp": timestamp
                },
                "metrics": data.get("scan_metrics", {}),
                "vulnerabilities": {
                    "high": [],
                    "medium": [],
                    "low": [],
                    "info": []
                }
            }
            
            # Group issues by severity in JSON
            for issue in sorted_issues:
                severity = issue["issue"].get("severity", "info").lower()
                if severity in report_data["vulnerabilities"]:
                    report_data["vulnerabilities"][severity].append(issue)
            
            # Write JSON file
            with open(filepath, "w") as f:
                json.dump(report_data, f, indent=4)
        else:  # Default to Markdown format
            filename = f"scan_report_{scan_id}_{timestamp}.md"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, "w") as f:
                # Write summary
                f.write("# Scan Report\n\n")
                f.write("## Summary\n\n")
                f.write(f"- **Scan ID**: {scan_id}\n")
                f.write(f"- **Status**: {data.get('scan_status')}\n")
                f.write(f"- **Time**: {timestamp}\n\n")
                
                # Write metrics
                if "scan_metrics" in data:
                    metrics = data["scan_metrics"]
                    f.write("## Scan Metrics\n\n")
                    f.write(f"- **Requests Made**: {metrics.get('crawl_requests_made', 0)}\n")
                    f.write(f"- **Network Errors**: {metrics.get('crawl_network_errors', 0)}\n")
                    f.write(f"- **Unique Locations**: {metrics.get('crawl_unique_locations_visited', 0)}\n")
                    f.write(f"- **Issues Found**: {metrics.get('issue_events', 0)}\n\n")
                
                # Write vulnerabilities grouped by severity
                f.write("## Vulnerabilities Found\n\n")
                
                # Group issues by severity
                severity_groups = {
                    "high": [],
                    "medium": [],
                    "low": [],
                    "info": []
                }
                
                for issue in sorted_issues:
                    severity = issue["issue"].get("severity", "info").lower()
                    if severity in severity_groups:
                        severity_groups[severity].append(issue)
                
                # Write issues for each severity level
                for severity in ["high", "medium", "low", "info"]:
                    if severity_groups[severity]:
                        f.write(f"### {severity.upper()} Severity Issues\n\n")
                        for issue in severity_groups[severity]:
                            issue_data = issue["issue"]
                            f.write(f"#### {issue_data.get('name', 'Unknown Issue')}\n\n")
                            f.write(f"- **Severity**: {severity.upper()}\n")
                            f.write(f"- **URL**: {issue_data.get('path', 'Unknown')}\n")
                            f.write(f"- **Description**: {issue_data.get('description', 'No description available')}\n")
                            if "remediation" in issue_data:
                                f.write(f"- **Remediation**: {issue_data['remediation']}\n")
                            f.write("\n---\n\n")

        logging.info(f"Report generated successfully: {filepath}")
        return filepath
        
    except requests.exceptions.RequestException as e:
        logging.error(f"Error generating report: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error while generating report: {e}")
        return None

if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()
    
    try:
        # Parse target URLs and scan configs from JSON strings
        target_urls_str = os.getenv('TARGET_URLS', '[]')
        scan_configs_str = os.getenv('SCAN_NAME', '["Checking"]')
        
        target_urls = json.loads(target_urls_str)
        scan_configs = json.loads(scan_configs_str)
        
        if not isinstance(target_urls, list):
            raise ValueError("TARGET_URLS must be a JSON array")
        if not isinstance(scan_configs, list):
            raise ValueError("SCAN_NAME must be a JSON array")
        
        username = os.getenv('USERNAME')
        password = os.getenv('PASSWORD')
        BOT_TOKEN = os.getenv('BOT_TOKEN')
        CHAT_ID = os.getenv('CHAT_ID')
        BURP_API_URL = os.getenv('BURP_API_URL') # Default to 127.0.0.1:1337
        if not BOT_TOKEN or not CHAT_ID or not BURP_API_URL:
            raise ValueError("BOT_TOKEN, CHAT_ID, and BURP_API_URL must be set in environment variables")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from environment variables: {e}")
        exit(1)
    



   # Constants for timeout
    SLEEP_TIME = 30  # Sleep time in seconds
    MAX_PAUSE_TIME = 15 * 60  # 15 minutes in seconds
    pause_counter = 0  # Counter to track pause duration

    # Khởi tạo Telegram Notifier
    notifier = tele_notifyer.TelegramNotifier(BOT_TOKEN, CHAT_ID)

    last_issue_count = 0
    
    # Create scan
    scan_id = create_scan(target_urls, scan_configs, username, password)
    if scan_id:
        while True:
            status, last_issue_count = check_scan_status(scan_id, notifier, last_issue_count)
            
            if status == "completed":
                print("Scan completed successfully.")
                # Generate final reports
                md_report = generate_report(scan_id, format="md")
                json_report = generate_report(scan_id, format="json")
                try:
                    # Send final summary
                    tele_notifyer.notify_vulnerabilities(json_report, md_report, BOT_TOKEN, CHAT_ID)
                except Exception as e:
                    logging.error(f"Error sending final notification: {e}")
                if md_report and json_report:
                    print(f"Reports generated:\nMarkdown: {md_report}\nJSON: {json_report}")
                break
            elif status == "failed":
                alert_message = "Scan failed."
                alert_text = notifier.notify_alert(alert_message)
                notifier.send_message(alert_text)
                # print(alert_message)
                break
            elif status == "running":
                print("Scan is still running. Checking again in 30 seconds...")
                pause_counter = 0  # Reset pause counter when running
            elif status == "paused":
                pause_counter += SLEEP_TIME
                if pause_counter >= MAX_PAUSE_TIME:
                    print(f"Scan has been paused for {MAX_PAUSE_TIME/60} minutes. Stopping scan.")
                    alert_message = f"Scan has been paused for {MAX_PAUSE_TIME/60} minutes. Stopping scan."
                    alert_text = notifier.notify_alert(alert_message)
                    notifier.send_message(alert_text)
                    break
                print(f"Scan is paused (for {pause_counter/60:.1f} minutes). Checking again in 30 seconds...")
                alert_message = f"Scan is paused (for {pause_counter/60:.1f} minutes). Checking again in 30 seconds..."
                alert_text = notifier.notify_alert(alert_message)
                notifier.send_message(alert_text)
            else:
                print(f"Unexpected status: {status}. Retrying in 30 seconds...")
                pause_counter = 0  # Reset pause counter for other statuses
            
            time.sleep(SLEEP_TIME)

    # generate_report(25, format="json")