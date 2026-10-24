
# File: src/core/scanner/report_generator.py
import os
import datetime
from typing import List, Dict, Set, Optional
from src.core.notification import Notifier

class ReportGenerator:
    """Lớp tạo báo cáo kết quả quét"""
    
    def __init__(self, target: str, output_dir: str, notifier: Optional[Notifier] = None):
        """
        Khởi tạo lớp tạo báo cáo
        
        Args:
            target: Tên miền mục tiêu
            output_dir: Thư mục đầu ra để lưu báo cáo
            notifier: Đối tượng thông báo (tùy chọn)
        """
        self.target = target
        self.output_dir = output_dir
        self.notifier = notifier
    
    def generate_markdown_report(self, all_urls: Set[str], parameter_urls: Set[str],
                               vulnerabilities: List[Dict], duration: float) -> str:
        """
        Tạo báo cáo dạng Markdown
        
        Args:
            all_urls: Tập hợp tất cả URL thu thập được
            parameter_urls: Tập hợp các URL có tham số
            vulnerabilities: Danh sách các lỗ hổng tiềm ẩn
            duration: Thời gian thực hiện quét (giây)
            
        Returns:
            str: Đường dẫn đến tệp báo cáo
        """
        # Phân loại các lỗ hổng theo mức độ nghiêm trọng
        vulnerabilities_by_severity = {
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }
        
        # Phân loại lỗ hổng dựa trên loại
        for vuln in vulnerabilities:
            vuln_type = vuln.get('vulnerability_type', '').lower()
            
            if "xss" in vuln_type or "sqli" in vuln_type or "rce" in vuln_type:
                vulnerabilities_by_severity["high"].append(vuln)
            elif "ssrf" in vuln_type or "open redirect" in vuln_type or "idor" in vuln_type:
                vulnerabilities_by_severity["medium"].append(vuln)
            elif "csrf" in vuln_type or "clickjacking" in vuln_type:
                vulnerabilities_by_severity["low"].append(vuln)
            else:
                vulnerabilities_by_severity["info"].append(vuln)
        
        # Tạo nội dung Markdown
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        target_escaped = ""
        time_escaped = ""
        
        if self.notifier and hasattr(self.notifier, 'escape_markdown'):
            target_escaped = self.notifier.escape_markdown(self.target)
            time_escaped = self.notifier.escape_markdown(current_time)
        else:
            target_escaped = self.target
            time_escaped = current_time
        
        markdown_content = f"""
# 📊 SharinganV2 Reconnaissance Report

## Target: {target_escaped}
*Report generated at: {time_escaped}*

### 📈 Summary
- Total scan time: {duration:.2f} seconds
- Total URLs discovered: {len(all_urls)}
- URLs with parameters: {len(parameter_urls)}
- Potential vulnerabilities: {len(vulnerabilities)}
- High severity issues: {len(vulnerabilities_by_severity["high"])}
- Medium severity issues: {len(vulnerabilities_by_severity["medium"])}

"""
        
        # Thêm phần lỗ hổng mức độ High
        if vulnerabilities_by_severity["high"]:
            markdown_content += "### 🔴 High Severity Issues\n\n"
            
            for i, vuln in enumerate(vulnerabilities_by_severity["high"], 1):
                vuln_type = vuln.get('vulnerability_type', 'Unknown')
                url = vuln.get('url', 'Unknown')
                param = vuln.get('param', 'Unknown')
                payload = vuln.get('payload', 'Unknown')
                
                if self.notifier and hasattr(self.notifier, 'escape_markdown'):
                    vuln_type = self.notifier.escape_markdown(vuln_type)
                    url = self.notifier.escape_markdown(url)
                    param = self.notifier.escape_markdown(param)
                    payload = self.notifier.escape_markdown(payload)
                
                markdown_content += f"""
{i}\\. *{vuln_type}*
- URL: `{url}`
- Parameter: `{param}`
- Payload: `{payload}`

"""
        
        # Thêm phần lỗ hổng mức độ Medium
        if vulnerabilities_by_severity["medium"]:
            markdown_content += "### 🟠 Medium Severity Issues\n\n"
            
            for i, vuln in enumerate(vulnerabilities_by_severity["medium"], 1):
                vuln_type = vuln.get('vulnerability_type', 'Unknown')
                url = vuln.get('url', 'Unknown')
                param = vuln.get('param', 'Unknown')
                payload = vuln.get('payload', 'Unknown')
                
                if self.notifier and hasattr(self.notifier, 'escape_markdown'):
                    vuln_type = self.notifier.escape_markdown(vuln_type)
                    url = self.notifier.escape_markdown(url)
                    param = self.notifier.escape_markdown(param)
                    payload = self.notifier.escape_markdown(payload)
                
                markdown_content += f"""
{i}\\. *{vuln_type}*
- URL: `{url}`
- Parameter: `{param}`
- Payload: `{payload}`

"""
        
        # Kết thúc báo cáo Markdown
        markdown_content += f"""
### 🔍 Scan Details
- Target: `{target_escaped}`
- Start time: {time_escaped}
- Duration: {duration:.2f} seconds
- Parameters tested: {len(parameter_urls)}

*Generated by SharinganV2*
"""
        
        # Lưu báo cáo Markdown
        report_file = os.path.join(self.output_dir, "report.md")
        with open(report_file, 'w') as f:
            f.write(markdown_content)
        
        return report_file
    
    def generate_html_report(self, all_urls: Set[str], parameter_urls: Set[str],
                           vulnerabilities: List[Dict], duration: float) -> str:
        """
        Tạo báo cáo dạng HTML
        
        Args:
            all_urls: Tập hợp tất cả URL thu thập được
            parameter_urls: Tập hợp các URL có tham số
            vulnerabilities: Danh sách các lỗ hổng tiềm ẩn
            duration: Thời gian thực hiện quét (giây)
            
        Returns:
            str: Đường dẫn đến tệp báo cáo
        """
        # Phân loại các lỗ hổng theo mức độ nghiêm trọng
        vulnerabilities_by_severity = {
            "critical": [],
            "high": [],
            "medium": [],
            "low": [],
            "info": []
        }
        
        # Phân loại lỗ hổng dựa trên loại
        for vuln in vulnerabilities:
            vuln_type = vuln.get('vulnerability_type', '').lower()
            
            if "xss" in vuln_type or "sqli" in vuln_type or "rce" in vuln_type:
                vulnerabilities_by_severity["high"].append(vuln)
            elif "ssrf" in vuln_type or "open redirect" in vuln_type or "idor" in vuln_type:
                vulnerabilities_by_severity["medium"].append(vuln)
            elif "csrf" in vuln_type or "clickjacking" in vuln_type:
                vulnerabilities_by_severity["low"].append(vuln)
            else:
                vulnerabilities_by_severity["info"].append(vuln)
        
        # Tạo nội dung HTML
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        html_content = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SharinganV2 Report - {self.target}</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        .summary-box {{
            background-color: #f8f9fa;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 20px;
            border-left: 5px solid #007bff;
        }}
        .vulnerability {{
            background-color: #fff;
            border-radius: 5px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .critical {{
            border-left: 5px solid #dc3545;
        }}
        .high {{
            border-left: 5px solid #fd7e14;
        }}
        .medium {{
            border-left: 5px solid #ffc107;
        }}
        .low {{
            border-left: 5px solid #28a745;
        }}
        .info {{
            border-left: 5px solid #17a2b8;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 20px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
        }}
        .stat {{
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }}
        .logo {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .logo h1 {{
            font-size: 32px;
            margin: 0;
            color: #e74c3c;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">
            <h1>👁️ SharinganV2</h1>
            <p>Web Vulnerability Scanner</p>
        </div>
        
        <h2>Reconnaissance Report: {self.target}</h2>
        <p>Báo cáo được tạo vào: {current_time}</p>
        
        <div class="summary-box">
            <h3>Tóm tắt</h3>
            <table>
                <tr>
                    <td>Tổng thời gian quét:</td>
                    <td>{duration:.2f} giây</td>
                </tr>
                <tr>
                    <td>Tổng số URL phát hiện:</td>
                    <td class="stat">{len(all_urls)}</td>
                </tr>
                <tr>
                    <td>URL có tham số:</td>
                    <td class="stat">{len(parameter_urls)}</td>
                </tr>
                <tr>
                    <td>Lỗ hổng tiềm ẩn:</td>
                    <td class="stat">{len(vulnerabilities)}</td>
                </tr>
                <tr>
                    <td>Lỗ hổng High:</td>
                    <td class="stat">{len(vulnerabilities_by_severity["high"])}</td>
                </tr>
                <tr>
                    <td>Lỗ hổng Medium:</td>
                    <td class="stat">{len(vulnerabilities_by_severity["medium"])}</td>
                </tr>
            </table>
        </div>
"""
        
        # Thêm phần lỗ hổng mức độ High
        if vulnerabilities_by_severity["high"]:
            html_content += """
        <h3>Lỗ hổng mức độ High</h3>
"""
            for vuln in vulnerabilities_by_severity["high"]:
                html_content += f"""
        <div class="vulnerability high">
            <h4>{vuln.get('vulnerability_type')}</h4>
            <p><strong>URL:</strong> {vuln.get('url')}</p>
            <p><strong>Tham số:</strong> {vuln.get('param')}</p>
            <p><strong>Payload:</strong> {vuln.get('payload')}</p>
            <p><strong>Bằng chứng:</strong> {vuln.get('evidence')}</p>
        </div>
"""
        
        # Thêm phần lỗ hổng mức độ Medium
        if vulnerabilities_by_severity["medium"]:
            html_content += """
        <h3>Lỗ hổng mức độ Medium</h3>
"""
            for vuln in vulnerabilities_by_severity["medium"]:
                html_content += f"""
        <div class="vulnerability medium">
            <h4>{vuln.get('vulnerability_type')}</h4>
            <p><strong>URL:</strong> {vuln.get('url')}</p>
            <p><strong>Tham số:</strong> {vuln.get('param')}</p>
            <p><strong>Payload:</strong> {vuln.get('payload')}</p>
            <p><strong>Bằng chứng:</strong> {vuln.get('evidence')}</p>
        </div>
"""
        
        # Kết thúc HTML
        html_content += """
        <div style="text-align: center; margin-top: 30px; color: #777; font-size: 12px;">
            <p>Powered by SharinganV2 - Advanced Web Reconnaissance Tool</p>
        </div>
    </div>
</body>
</html>
"""
        
        # Lưu báo cáo vào tệp
        report_file = os.path.join(self.output_dir, "report.html")
        with open(report_file, 'w') as f:
            f.write(html_content)
        
        return report_file