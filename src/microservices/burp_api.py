#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simplified Burp Suite REST API Client
Focused on http://127.0.0.1:1337/v0.1/ endpoints only
"""

import json
import time
import requests
from typing import Dict, List, Optional, Any


class BurpAPI:
    """Simplified Burp Suite REST API client for v0.1"""
    
    def __init__(self, base_url: str = "http://127.0.0.1:1337/v0.1"):
        """
        Initialize Burp API client
        
        Args:
            base_url: Base URL for Burp REST API (default: http://127.0.0.1:1337/v0.1)
        """
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json"
        })
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Any:
        """Make HTTP request to Burp API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                timeout=30
            )
            
            # Handle different status codes
            if response.status_code == 201:
                # Created - return location header for scan
                return {"location": response.headers.get('Location', '')}
            elif response.status_code == 200:
                # Success - return JSON if available
                if response.content:
                    return response.json()
                return {}
            elif response.status_code == 204:
                # No content
                return {}
            else:
                # Error
                error_msg = f"API error {response.status_code}: {response.text}"
                print(f"[-] {error_msg}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"[-] Request failed: {str(e)}")
            return None
    
    def get_issue_definitions(self) -> List[Dict[str, Any]]:
        """Get all issue type definitions"""
        result = self._request("GET", "/knowledge_base/issue_definitions")
        return result if isinstance(result, list) else []
    
    def start_scan(self, urls: List[str], scan_configs: Optional[List[Dict]] = None) -> Optional[str]:
        """
        Start a new scan
        
        Args:
            urls: List of URLs to scan
            scan_configs: Optional scan configurations
            
        Returns:
            Scan task ID if successful, None otherwise
        """
        # Default scan configuration
        if not scan_configs:
            scan_configs = [
                {
                    "name": "Audit checks - passive",
                    "type": "NamedConfiguration"
                },
                {
                    "name": "Audit checks - light active", 
                    "type": "NamedConfiguration"
                }
            ]
        
        scan_data = {
            "scan_configurations": scan_configs,
            "urls": urls
        }
        
        result = self._request("POST", "/scan", data=scan_data)
        
        if result and "location" in result:
            # Extract scan ID from location header
            return result["location"].split("/")[-1]
        
        return None
    
    def get_scan_status(self, scan_id: str) -> Optional[Dict[str, Any]]:
        """Get scan status and progress"""
        return self._request("GET", f"/scan/{scan_id}")
    
    def get_scan_issues(self, scan_id: str) -> List[Dict[str, Any]]:
        """Get issues found by scan"""
        status = self.get_scan_status(scan_id)
        if status:
            return status.get("issue_events", [])
        return []
    
    def wait_for_scan(self, scan_id: str, timeout: int = 3600, callback=None) -> Dict[str, Any]:
        """
        Wait for scan to complete
        
        Args:
            scan_id: Scan task ID
            timeout: Maximum wait time in seconds
            callback: Optional progress callback function
            
        Returns:
            Final scan status
        """
        start_time = time.time()
        last_status = {}
        
        while (time.time() - start_time) < timeout:
            status = self.get_scan_status(scan_id)
            
            if not status:
                break
            
            last_status = status
            
            # Call callback if provided
            if callback:
                callback(status)
            
            # Check if scan is complete
            scan_status = status.get("scan_status", "unknown")
            if scan_status in ["succeeded", "failed", "paused", "cancelled"]:
                break
            
            # Wait before next check
            time.sleep(5)
        
        return last_status
    
    def get_scan_metrics(self, scan_id: str) -> Dict[str, Any]:
        """Get scan metrics and summary"""
        status = self.get_scan_status(scan_id)
        
        if not status:
            return {}
        
        metrics = status.get("scan_metrics", {})
        
        return {
            "scan_id": scan_id,
            "status": status.get("scan_status", "unknown"),
            "progress": metrics.get("crawl_and_audit_progress", 0),
            "urls_crawled": metrics.get("crawl_unique_locations_visited", 0),
            "requests_made": metrics.get("crawl_requests_made", 0) + metrics.get("audit_requests_made", 0),
            "issues_found": metrics.get("issue_events", 0),
            "elapsed_time": metrics.get("total_elapsed_time", 0),
            "error_message": metrics.get("crawl_and_audit_caption", ""),
            "issue_events": status.get("issue_events", [])
        }
    
    def create_scan_and_wait(self, urls: List[str], timeout: int = 1800) -> Dict[str, Any]:
        """
        Create scan and wait for completion
        
        Args:
            urls: URLs to scan
            timeout: Maximum wait time
            
        Returns:
            Scan results with metrics
        """
        print(f"[+] Starting scan for {len(urls)} URL(s)...")
        
        # Start scan
        scan_id = self.start_scan(urls)
        if not scan_id:
            return {"error": "Failed to start scan"}
        
        print(f"[+] Scan started with ID: {scan_id}")
        
        # Wait for completion with progress
        def progress_callback(status):
            metrics = status.get("scan_metrics", {})
            progress = metrics.get("crawl_and_audit_progress", -1)
            if progress >= 0:
                print(f"    Progress: {progress}%")
        
        final_status = self.wait_for_scan(scan_id, timeout, progress_callback)
        
        # Get final metrics
        metrics = self.get_scan_metrics(scan_id)
        
        print(f"[+] Scan completed with status: {metrics['status']}")
        print(f"    - URLs crawled: {metrics['urls_crawled']}")
        print(f"    - Total requests: {metrics['requests_made']}")
        print(f"    - Issues found: {metrics['issues_found']}")
        
        return metrics


# Example usage
if __name__ == "__main__":
    # Initialize API
    api = BurpAPI()
    
    # Test connection
    print("[*] Testing Burp Suite connection...")
    definitions = api.get_issue_definitions()
    if definitions:
        print(f"[+] Connected! Found {len(definitions)} issue definitions")
    else:
        print("[-] Failed to connect to Burp Suite")
        exit(1)
    
    # Run a test scan
    test_urls = ["http://testphp.vulnweb.com/"]
    results = api.create_scan_and_wait(test_urls, timeout=300)
    
    # Show results
    if "error" not in results:
        print("\n[*] Scan Results:")
        print(json.dumps(results, indent=2))