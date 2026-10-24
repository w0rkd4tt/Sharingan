# Hướng dẫn sử dụng Sharingan cho người mới bắt đầu

## Mục lục
1. [Giới thiệu](#giới-thiệu)
2. [Cài đặt](#cài-đặt)
3. [Cấu hình cơ bản](#cấu-hình-cơ-bản)
4. [Sử dụng cơ bản](#sử-dụng-cơ-bản)
5. [Sử dụng Microservices](#sử-dụng-microservices)
6. [Các tính năng nâng cao](#các-tính-năng-nâng-cao)
7. [Xử lý sự cố](#xử-lý-sự-cố)

## 1. Giới thiệu

### Sharingan là gì?
Sharingan là một công cụ quét bảo mật web tự động, giúp bạn:
- Tìm kiếm các URL và endpoint ẩn trên website
- Phát hiện lỗ hổng bảo mật phổ biến
- Tích hợp với Burp Suite Professional
- Nhận thông báo qua WhatsApp hoặc Telegram

### Yêu cầu hệ thống
- Python 3.7 trở lên
- Burp Suite Professional (với REST API)
- Tài khoản WhatsApp Business hoặc Telegram Bot
- RAM tối thiểu 4GB
- Kết nối Internet ổn định

## 2. Cài đặt

### Bước 1: Clone project
```bash
git clone https://github.com/yourusername/Sharingan.git
cd Sharingan
```

### Bước 2: Cài đặt Python dependencies
```bash
# Tạo môi trường ảo (khuyến khích)
python3 -m venv venv

# Kích hoạt môi trường ảo
# Trên Linux/Mac:
source venv/bin/activate
# Trên Windows:
venv\Scripts\activate

# Cài đặt dependencies
pip install -r requirements.txt
```

### Bước 3: Cài đặt các công cụ bên ngoài
```bash
# Chạy script cài đặt tự động
bash install.sh

# Hoặc cài đặt thủ công:
# 1. ParamSpider
git clone https://github.com/devanshbatham/ParamSpider
cd ParamSpider
pip install -r requirements.txt
cd ..

# 2. Waybackurls
go install github.com/tomnomnom/waybackurls@latest

# 3. Hakrawler
go install github.com/hakluke/hakrawler@latest

# 4. Katana
go install github.com/projectdiscovery/katana/cmd/katana@latest

# 5. Gau
go install github.com/lc/gau/v2/cmd/gau@latest
```

## 3. Cấu hình cơ bản

### Bước 1: Tạo file cấu hình mẫu
```bash
# Tạo file .env mẫu
python sharingan.py --create-env

# Tạo các template mẫu
python sharingan.py --create-templates

# Tạo file config mẫu
python sharingan.py --create-config
```

### Bước 2: Cấu hình Burp Suite
1. Mở Burp Suite Professional
2. Vào **User options** → **REST API**
3. Enable REST API service
4. Copy API key

### Bước 3: Cấu hình thông báo

#### Cho WhatsApp:
1. Đăng ký tài khoản [WhatsApp Business API](https://business.whatsapp.com/developers/docs)
2. Lấy Access Token và Phone Number ID
3. Cấu hình số điện thoại nhận thông báo

#### Cho Telegram:
1. Tạo bot với [@BotFather](https://t.me/botfather)
2. Lấy Bot Token
3. Lấy Chat ID (gửi tin nhắn cho bot và check https://api.telegram.org/bot<TOKEN>/getUpdates)

### Bước 4: Chỉnh sửa file .env
```bash
# Mở file .env
nano .env

# Cập nhật các giá trị:
BURP_API_URL=http://localhost:1337/v0.1
BURP_API_KEY=your_burp_api_key_here

# Chọn service thông báo (whatsapp hoặc telegram)
NOTIFICATION_SERVICE=whatsapp

# Cấu hình WhatsApp
WHATSAPP_ACCESS_TOKEN=your_whatsapp_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_id
WHATSAPP_RECIPIENT_NUMBER=+84912345678

# Hoặc cấu hình Telegram
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

## 4. Sử dụng cơ bản

### Scan đơn giản
```bash
# Scan cơ bản một domain
python sharingan.py -t example.com

# Scan với output tùy chỉnh
python sharingan.py -t example.com -o reports/example
```

### Scan với fuzzing
```bash
# Bật chế độ fuzzing (kiểm tra lỗ hổng sâu hơn)
python sharingan.py -t example.com --fuzzing
```

### Scan với nhiều threads
```bash
# Tăng tốc độ scan với 20 threads
python sharingan.py -t example.com --threads 20
```

### Xem các tùy chọn
```bash
python sharingan.py --help
```

## 5. Sử dụng Microservices

### Khởi động với Docker
```bash
cd microservices

# Build và chạy tất cả services
docker-compose up --build

# Chạy ở chế độ background
docker-compose up -d
```

### Sử dụng API Gateway

#### 1. Kiểm tra health của services
```bash
curl http://localhost:5000/sharingan/health
```

#### 2. Thực hiện full scan
```bash
curl -X POST http://localhost:5000/sharingan/scan \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "scan_config": "quick",
    "notification_service": "whatsapp"
  }'
```

#### 3. Chỉ crawl URLs
```bash
curl -X POST http://localhost:5003/crawl/start \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "crawlers": ["paramspider", "waybackurls"]
  }'
```

#### 4. Kiểm tra trạng thái crawl
```bash
curl http://localhost:5003/crawl/status/{task_id}
```

## 6. Các tính năng nâng cao

### Sử dụng scan configurations

Sharingan có 6 cấu hình scan sẵn:

1. **default**: Cân bằng giữa tốc độ và độ chính xác
2. **quick**: Scan nhanh, chỉ kiểm tra lỗi cơ bản
3. **thorough**: Scan kỹ lưỡng, kiểm tra toàn diện
4. **custom**: Tùy chỉnh theo nhu cầu
5. **api_testing**: Tối ưu cho REST API
6. **owasp_top10**: Tập trung vào OWASP Top 10

```bash
# Sử dụng scan configuration
python sharingan.py -t example.com --scan-config thorough
```

### Tùy chỉnh crawler tools

```bash
# Chỉ sử dụng một số crawler cụ thể
curl -X POST http://localhost:5003/crawl/start \
  -H "Content-Type: application/json" \
  -d '{
    "target": "example.com",
    "crawlers": ["paramspider", "katana"]
  }'
```

### Gửi thông báo tùy chỉnh

```bash
# Gửi message
curl -X POST http://localhost:5002/notify/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Scan đã hoàn tất!",
    "service": "whatsapp"
  }'

# Gửi file báo cáo
curl -X POST http://localhost:5002/notify/document \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "/path/to/report.html",
    "caption": "Báo cáo scan example.com",
    "service": "whatsapp"
  }'
```

## 7. Xử lý sự cố

### Lỗi thường gặp

#### 1. "Burp API connection failed"
- Kiểm tra Burp Suite đang chạy
- Kiểm tra REST API đã được enable
- Kiểm tra API key đúng

#### 2. "WhatsApp notification failed"
- Kiểm tra access token còn hạn
- Kiểm tra số điện thoại đúng format (+84...)
- Kiểm tra kết nối internet

#### 3. "No URLs found"
- Target có thể có robots.txt nghiêm ngặt
- Thử với các crawler khác
- Kiểm tra kết nối internet

### Debug mode
```bash
# Chạy với verbose mode để xem chi tiết
python sharingan.py -t example.com --verbose

# Xem logs của microservices
docker-compose logs -f scanner-service
```

### Kiểm tra kết quả

Kết quả scan được lưu trong thư mục `reports/`:
- `all_urls.txt`: Tất cả URLs tìm được
- `parameter_urls.txt`: URLs có parameters
- `report.html`: Báo cáo chi tiết dạng HTML
- `report.md`: Báo cáo dạng Markdown

## Tips cho người mới

1. **Bắt đầu với quick scan**: Để làm quen với tool
2. **Sử dụng threads vừa phải**: 10-20 threads là đủ
3. **Theo dõi notifications**: Để biết tiến độ scan
4. **Đọc báo cáo kỹ**: Hiểu rõ các lỗ hổng tìm được
5. **Test trên lab trước**: Dùng DVWA hoặc WebGoat để thực hành

## Lưu ý về bảo mật

⚠️ **CẢNH BÁO**: 
- Chỉ scan các website bạn có quyền
- Không scan website của người khác mà không có sự cho phép
- Tuân thủ luật pháp về an ninh mạng
- Sử dụng có trách nhiệm

## Hỗ trợ

Nếu gặp vấn đề:
1. Kiểm tra [Issues](https://github.com/yourusername/Sharingan/issues) trên GitHub
2. Đọc [FAQ](FAQ.md)
3. Tạo issue mới với đầy đủ thông tin lỗi

---

Happy hunting! 🎯