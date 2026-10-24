#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simple Crawler Microservice
Focused on URL crawling for web applications
"""

import os
import uuid
import threading
import subprocess
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

# In-memory storage
crawl_tasks = {}


def run_crawler_task(task_id: str, target: str, tools: list):
    """Run crawler tools in background"""
    try:
        crawl_tasks[task_id]['status'] = 'running'
        crawl_tasks[task_id]['started_at'] = datetime.now().isoformat()
        
        all_urls = set()
        
        # Run each crawler tool
        for tool in tools:
            try:
                if tool == 'waybackurls':
                    # Run waybackurls
                    cmd = f"echo {target} | waybackurls"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                    if result.stdout:
                        urls = result.stdout.strip().split('\n')
                        all_urls.update([u for u in urls if u])
                        
                elif tool == 'gau':
                    # Run gau (Get All URLs)
                    cmd = f"echo {target} | gau --subs"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                    if result.stdout:
                        urls = result.stdout.strip().split('\n')
                        all_urls.update([u for u in urls if u])
                        
                elif tool == 'hakrawler':
                    # Run hakrawler
                    cmd = f"echo {target} | hakrawler -subs"
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
                    if result.stdout:
                        urls = result.stdout.strip().split('\n')
                        all_urls.update([u for u in urls if u])
                        
                elif tool == 'paramspider':
                    # Run paramspider
                    cmd = f"paramspider -d {target}"
                    subprocess.run(cmd, shell=True, timeout=60)
                    # Read output file
                    output_file = f"output/{target}.txt"
                    if os.path.exists(output_file):
                        with open(output_file, 'r') as f:
                            urls = f.read().strip().split('\n')
                            all_urls.update([u for u in urls if u])
                        os.remove(output_file)
                        
            except Exception as e:
                print(f"Error running {tool}: {e}")
        
        # Filter URLs with parameters
        parameter_urls = [url for url in all_urls if '?' in url and '=' in url]
        
        # Update task results
        crawl_tasks[task_id]['status'] = 'completed'
        crawl_tasks[task_id]['results'] = {
            'total_urls': len(all_urls),
            'parameter_urls': len(parameter_urls),
            'urls': list(all_urls)[:1000],  # Limit to 1000 URLs
            'param_urls': parameter_urls[:500]  # Limit to 500 param URLs
        }
        
    except Exception as e:
        crawl_tasks[task_id]['status'] = 'failed'
        crawl_tasks[task_id]['error'] = str(e)
    finally:
        crawl_tasks[task_id]['completed_at'] = datetime.now().isoformat()


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'crawler',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/crawl/start', methods=['POST'])
def start_crawl():
    """Start URL crawling"""
    data = request.get_json()
    
    if not data or 'target' not in data:
        return jsonify({'error': 'Missing required field: target'}), 400
    
    target = data['target']
    tools = data.get('tools', ['waybackurls', 'gau'])  # Default tools
    
    # Create task
    task_id = str(uuid.uuid4())
    crawl_tasks[task_id] = {
        'id': task_id,
        'target': target,
        'tools': tools,
        'status': 'queued',
        'created_at': datetime.now().isoformat()
    }
    
    # Start crawling in background
    thread = threading.Thread(
        target=run_crawler_task,
        args=(task_id, target, tools)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'status': 'queued',
        'message': 'Crawl task created'
    })


@app.route('/api/crawl/status/<task_id>', methods=['GET'])
def get_crawl_status(task_id):
    """Get crawl task status"""
    if task_id not in crawl_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = crawl_tasks[task_id]
    
    return jsonify({
        'id': task['id'],
        'target': task['target'],
        'tools': task['tools'],
        'status': task['status'],
        'created_at': task['created_at'],
        'started_at': task.get('started_at'),
        'completed_at': task.get('completed_at'),
        'error': task.get('error')
    })


@app.route('/api/crawl/results/<task_id>', methods=['GET'])
def get_crawl_results(task_id):
    """Get crawl results"""
    if task_id not in crawl_tasks:
        return jsonify({'error': 'Task not found'}), 404
    
    task = crawl_tasks[task_id]
    
    if task['status'] != 'completed':
        return jsonify({'error': 'Crawl not completed yet'}), 400
    
    return jsonify({
        'task_id': task_id,
        'target': task['target'],
        'results': task.get('results', {})
    })


@app.route('/api/crawl/tools', methods=['GET'])
def get_available_tools():
    """Get available crawler tools"""
    return jsonify({
        'tools': [
            {'name': 'waybackurls', 'description': 'Get URLs from Wayback Machine'},
            {'name': 'gau', 'description': 'Get All URLs from multiple sources'},
            {'name': 'hakrawler', 'description': 'Fast web crawler'},
            {'name': 'paramspider', 'description': 'Find URLs with parameters'}
        ]
    })


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    print(f"[*] Starting Crawler Microservice on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True)