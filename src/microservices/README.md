# Sharingan Microservices

This directory contains standalone microservices that integrate with the main Sharingan tool.

## Services

### 1. Burp Scanner Service
- **File**: `burp_scanner.py`
- **Port**: 5003
- **Purpose**: Interface with Burp Suite Professional REST API for automated scanning

### 2. Crawler Service  
- **File**: `crawler_service.py`
- **Port**: 5001
- **Purpose**: URL discovery using multiple tools (waybackurls, gau, hakrawler, paramspider)

### 3. WhatsApp Notifier Service
- **File**: `whatsapp_notifier.py`
- **Port**: 5002
- **Purpose**: Send scan reports and alerts via WhatsApp Business API

## Running Services

Each service can be run independently:

```bash
# Burp Scanner
python src/microservices/burp_scanner.py

# Crawler
python src/microservices/crawler_service.py

# WhatsApp Notifier
python src/microservices/whatsapp_notifier.py
```

## Configuration

All services use environment variables from the `.env` file in the project root.