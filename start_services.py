#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Start all Sharingan microservices
"""

import os
import sys
import subprocess
import signal
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Service definitions
SERVICES = [
    {
        'name': 'Burp Scanner',
        'module': 'src.microservices.burp_scanner',
        'port': 5003
    },
    {
        'name': 'Crawler',
        'module': 'src.microservices.crawler_service',
        'port': 5001
    },
    {
        'name': 'WhatsApp Notifier',
        'module': 'src.microservices.whatsapp_notifier',
        'port': 5002
    }
]

processes = []

def signal_handler(sig, frame):
    """Handle shutdown signal"""
    print("\n[!] Stopping all services...")
    for p in processes:
        p.terminate()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def start_services():
    """Start all microservices"""
    print("[*] Starting Sharingan Microservices...")
    
    for service in SERVICES:
        print(f"[+] Starting {service['name']} on port {service['port']}...")
        
        # Start service
        process = subprocess.Popen(
            [sys.executable, '-m', service['module']],
            env=os.environ.copy()
        )
        processes.append(process)
    
    print("\n[*] All services started!")
    print("[*] Press Ctrl+C to stop all services\n")
    
    # Wait for processes
    try:
        for p in processes:
            p.wait()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    start_services()