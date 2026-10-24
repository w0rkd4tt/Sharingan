# Quick Start Guide - Bắt đầu nhanh với Sharingan

## 🚀 3 phút để chạy Sharingan

### 1️⃣ Cài đặt nhanh (1 phút)
```bash
# Clone và setup
git clone https://github.com/yourusername/Sharingan.git
cd Sharingan
pip install -r requirements.txt
bash install.sh
```

### 2️⃣ Cấu hình nhanh (1 phút)
```bash
# Tạo file config
python sharingan.py --create-env

# Sửa file .env (chỉ cần 2 dòng này cho test)
BURP_API_URL=http://localhost:1337/v0.1
BURP_API_KEY=your_key_here
```

### 3️⃣ Chạy scan đầu tiên (1 phút)
```bash
# Scan đơn giản
python sharingan.py -t testphp.vulnweb.com

# Hoặc scan nhanh với microservices
cd microservices
docker-compose up -d
curl -X POST http://localhost:5000/sharingan/scan \
  -H "Content-Type: application/json" \
  -d '{"target": "testphp.vulnweb.com"}'
```

## 📋 Checklist cho người mới

### Trước khi scan:
- [ ] Python 3.7+ đã cài?
- [ ] Burp Suite Pro đang chạy?
- [ ] REST API của Burp đã bật?
- [ ] Có quyền scan target?

### Lệnh hay dùng:
```bash
# Scan nhanh
python sharingan.py -t example.com

# Scan kỹ với fuzzing
python sharingan.py -t example.com --fuzzing

# Scan với thông báo WhatsApp
python sharingan.py -t example.com --notification whatsapp
```

### Xem kết quả:
- 📁 `reports/all_urls.txt` - Tất cả URLs
- 📁 `reports/parameter_urls.txt` - URLs có tham số
- 📁 `reports/report.html` - Báo cáo đẹp

## 🆘 Gặp lỗi?

### "Command not found"
```bash
# Kích hoạt môi trường ảo
source venv/bin/activate
```

### "Burp connection failed"
1. Mở Burp Suite Pro
2. User options → REST API → Enable
3. Copy API key vào file .env

### "No URLs found"
```bash
# Thử với verbose mode
python sharingan.py -t example.com --verbose
```

## 💡 Tips cho newbie

1. **Test với lab trước**: `testphp.vulnweb.com`
2. **Dùng quick scan**: Nhanh và đủ cho cơ bản
3. **Đọc logs**: Hiểu tool đang làm gì
4. **Hỏi khi cần**: Tạo issue trên GitHub

## ⚡ Cheatsheet

```bash
# Cơ bản
python sharingan.py -t <target>

# Với output custom
python sharingan.py -t <target> -o myreport

# Nhiều threads (nhanh hơn)
python sharingan.py -t <target> --threads 20

# Scan API
python sharingan.py -t api.example.com --scan-config api_testing

# Full options
python sharingan.py --help
```

---
🎯 Ready to hunt? Let's go!