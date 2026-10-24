#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simplified Burp Scanner Microservice
Focused on Burp Suite scan management only
"""

import os
import uuid
import threading
from datetime import datetime
from flask import Flask, request, jsonify

from .burp_api import BurpAPI

app = Flask(__name__)

# Add CORS headers manually
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# In-memory storage for scan tasks
scan_tasks = {}

# Burp API instance
burp_api = BurpAPI(os.getenv('BURP_API_URL', 'http://127.0.0.1:1337/v0.1'))


def run_scan_task(task_id: str, urls: list, scan_configs: list = None):
    """Background task to run Burp scan"""
    try:
        # Update task status
        scan_tasks[task_id]['status'] = 'running'
        scan_tasks[task_id]['started_at'] = datetime.now().isoformat()
        
        # Start scan
        scan_id = burp_api.start_scan(urls, scan_configs)
        
        if not scan_id:
            scan_tasks[task_id]['status'] = 'failed'
            scan_tasks[task_id]['error'] = 'Failed to start Burp scan'
            return
        
        scan_tasks[task_id]['burp_scan_id'] = scan_id
        
        # Monitor scan progress
        def progress_callback(status):
            metrics = status.get('scan_metrics', {})
            scan_tasks[task_id]['progress'] = metrics.get('crawl_and_audit_progress', -1)
            scan_tasks[task_id]['issues_found'] = metrics.get('issue_events', 0)
            scan_tasks[task_id]['last_update'] = datetime.now().isoformat()
        
        # Wait for scan completion
        final_status = burp_api.wait_for_scan(scan_id, timeout=3600, callback=progress_callback)
        
        # Get final metrics
        metrics = burp_api.get_scan_metrics(scan_id)
        
        # Update task with results
        scan_tasks[task_id]['status'] = 'completed'
        scan_tasks[task_id]['results'] = metrics
        scan_tasks[task_id]['completed_at'] = datetime.now().isoformat()
        
    except Exception as e:
        scan_tasks[task_id]['status'] = 'failed'
        scan_tasks[task_id]['error'] = str(e)
    finally:
        scan_tasks[task_id]['completed_at'] = datetime.now().isoformat()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    # Check Burp connection
    definitions = burp_api.get_issue_definitions()
    burp_connected = len(definitions) > 0
    
    return jsonify({
        'status': 'healthy',
        'service': 'burp-scanner',
        'burp_connected': burp_connected,
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/scan/start', methods=['POST'])
def start_scan():
    """Start a new scan"""
    data = request.get_json()
    
    if not data or 'urls' not in data:
        return jsonify({'error': 'Missing required field: urls'}), 400
    
    urls = data['urls']
    if not isinstance(urls, list) or len(urls) == 0:
        return jsonify({'error': 'URLs must be a non-empty list'}), 400
    
    # Get optional scan configurations
    scan_configs = data.get('scan_configs', None)
    
    # Create task
    task_id = str(uuid.uuid4())
    scan_tasks[task_id] = {
        'id': task_id,
        'urls': urls,
        'status': 'queued',
        'created_at': datetime.now().isoformat(),
        'progress': -1,
        'issues_found': 0
    }
    
    # Start scan in background
    thread = threading.Thread(
        target=run_scan_task,
        args=(task_id, urls, scan_configs)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'status': 'queued',
        'message': 'Scan task created successfully'
    })


@app.route('/api/scan/status/<task_id>', methods=['GET'])
def get_scan_status(task_id):
    """Get scan task status"""
    if task_id not in scan_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = scan_tasks[task_id]
    
    # Get live status from Burp if scan is running
    if task['status'] == 'running' and 'burp_scan_id' in task:
        metrics = burp_api.get_scan_metrics(task['burp_scan_id'])
        if metrics:
            task['progress'] = metrics.get('progress', -1)
            task['issues_found'] = metrics.get('issues_found', 0)
    
    return jsonify(task)


@app.route('/api/scan/list', methods=['GET'])
def list_scans():
    """List all scan tasks"""
    # Get query parameters
    status = request.args.get('status')
    limit = int(request.args.get('limit', 100))
    
    # Filter tasks
    tasks = list(scan_tasks.values())
    
    if status:
        tasks = [t for t in tasks if t['status'] == status]
    
    # Sort by created_at (newest first)
    tasks.sort(key=lambda x: x['created_at'], reverse=True)
    
    # Limit results
    tasks = tasks[:limit]
    
    return jsonify({
        'total': len(scan_tasks),
        'filtered': len(tasks),
        'tasks': tasks
    })


@app.route('/api/scan/results/<task_id>', methods=['GET'])
def get_scan_results(task_id):
    """Get detailed scan results"""
    if task_id not in scan_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = scan_tasks[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Scan not completed yet'}), 400
    
    return jsonify({
        'task_id': task_id,
        'urls': task['urls'],
        'status': task['status'],
        'results': task.get('results', {}),
        'created_at': task['created_at'],
        'completed_at': task.get('completed_at')
    })


@app.route('/api/issues/definitions', methods=['GET'])
def get_issue_definitions():
    """Get Burp issue type definitions"""
    definitions = burp_api.get_issue_definitions()
    
    return jsonify({
        'total': len(definitions),
        'definitions': definitions
    })


@app.route('/api/scan/quick', methods=['POST'])
def quick_scan():
    """Quick scan endpoint - start scan and return immediately"""
    data = request.get_json()
    
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing required field: url'}), 400
    
    url = data['url']
    
    # Start scan directly (no task tracking)
    scan_id = burp_api.start_scan([url])
    
    if scan_id:
        return jsonify({
            'scan_id': scan_id,
            'url': url,
            'message': 'Scan started in Burp Suite'
        })
    else:
        return jsonify({'error': 'Failed to start scan'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5003))
    print(f"[*] Starting Burp Scanner Microservice on port {port}")
    print(f"[*] Burp API URL: {burp_api.base_url}")
    app.run(host='0.0.0.0', port=port, debug=True)