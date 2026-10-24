# SharinganV2

<p align="center">
  <img src="https://raw.githubusercontent.com/yourusername/sharinganv2/main/assets/sharingan-logo.png" alt="SharinganV2 Logo" width="200"/>
</p>

<p align="center">
  <strong>Advanced Web Reconnaissance Tool for Security Professionals</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#tools-integration">Tools Integration</a> •
  <a href="#contributing">Contributing</a> •
  <a href="#license">License</a>
</p>

## Features

SharinganV2 combines multiple web reconnaissance tools to provide comprehensive security testing capabilities:

- **URL Discovery**: ParamSpider, waybackurls, gauplus, hakrawler, and katana to find hidden endpoints
- **Parameter Detection**: Automatically identifies URL parameters for deeper testing
- **Vulnerability Scanning**: Optional fuzzing templates to detect common security issues
- **Burp Suite Integration**: Sends findings to Burp Suite via REST API for deeper analysis
- **Telegram Notifications**: Real-time alerts and reports via Telegram bot
- **Beautiful Reports**: Generates comprehensive HTML and Markdown reports
- **Modular Architecture**: Easily extendable to add new tools and capabilities

## Installation

### Prerequisites

- Python 3.7+
- The following external tools:
  - [ParamSpider](https://github.com/0xKayala/ParamSpider)
  - [waybackurls](https://github.com/tomnomnom/waybackurls)
  - [gau/gauplus](https://github.com/bp0lr/gauplus)
  - [hakrawler](https://github.com/hakluke/hakrawler)
  - [katana](https://github.com/projectdiscovery/katana)

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/sharinganv2.git
   cd sharinganv2
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create configuration files:
   ```bash
   python sharingan.py --create-env
   python sharingan.py --create-templates
   python sharingan.py --create-config
   ```

5. Update the `.env` file with your configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your favorite editor
   ```

## Usage

### Basic Usage

```bash
python sharingan.py -t example.com -o reports/example
```

### With Fuzzing Enabled

```bash
python sharingan.py -t example.com --fuzzing
```

### With Burp Suite Integration

```bash
python sharingan.py -t example.com --burp-api http://localhost:1337/v0.1 --burp-key YOUR_API_KEY
```

### With Telegram Notifications

```bash
python sharingan.py -t example.com --telegram-token YOUR_BOT_TOKEN --telegram-chat YOUR_CHAT_ID
```

### Advanced Options

```bash
python sharingan.py -t example.com --threads 20 --verbose --fuzzing
```

## Configuration

### Environment Variables

Configure SharinganV2 by creating a `.env` file with the following options:

```
# Burp Suite API
BURP_API_URL=http://localhost:1337/v0.1
BURP_API_KEY=your_burp_api_key_here

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_token_here
TELEGRAM_CHAT_ID=your_chat_id_here

# Templates
TEMPLATES_DIR=src/template

# Options
ENABLE_FUZZING=false
```

### Fuzzing Templates

Custom fuzzing templates can be added to the `src/template` directory. Each template should be a JSON file with the following structure:

```json
{
  "name": "Cross-Site Scripting (XSS)",
  "description": "Kiểm tra lỗ hổng XSS bằng các payload phổ biến",
  "payloads": [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>"
  ],
  "patterns": [
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>"
  ]
}
```

## Tools Integration

SharinganV2 integrates with the following external tools:

- **ParamSpider**: Discovers parameters in URL endpoints
- **waybackurls**: Finds historical URLs from the Wayback Machine
- **gau/gauplus**: Gathers URLs from multiple sources
- **hakrawler**: Fast web crawler for security testing
- **katana**: Advanced crawling and spidering framework

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- All the amazing open-source tools that SharinganV2 builds upon
- The security research community for their continuous innovation