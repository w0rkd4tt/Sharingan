#!/usr/bin/env python3
"""Test available Burp scan configurations"""

import requests

# Test different configuration names
configs_to_test = [
    "Crawl and Audit - Crawl strategy - most complete",
    "Crawl and Audit - Crawl strategy - faster",
    "Crawl and Audit - Crawl strategy - fastest", 
    "Crawl and Audit - Audit checks - all except JavaScript analysis",
    "Crawl and Audit - Audit checks - all except time-based detection methods",
    "Audit checks - all except JavaScript analysis",
    "Audit checks - all except time-based detection methods",
    "Audit checks - critical issues only",
    "Audit checks - passive",
    "Audit checks - light active",
    "Audit checks - medium active",
    "Audit checks - active",
    "Crawl strategy - most complete",
    "Crawl strategy - faster", 
    "Crawl strategy - fastest",
    "Never stop crawl due to application errors",
    "Never stop audit due to application errors"
]

print("[*] Testing Burp scan configurations...")
print("-" * 60)

for config_name in configs_to_test:
    data = {
        "urls": ["http://example.com"],
        "scan_configurations": [{
            "name": config_name,
            "type": "NamedConfiguration"
        }]
    }
    
    response = requests.post(
        "http://127.0.0.1:1337/v0.1/scan",
        json=data,
        headers={"Content-Type": "application/json"}
    )
    
    status = "✓" if response.status_code == 201 else "✗"
    print(f"{status} {config_name}")