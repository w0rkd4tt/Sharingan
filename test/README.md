# Test Scripts

## test_whatsapp_notification.py

Script để test chức năng gửi thông báo WhatsApp.

### Cách sử dụng

#### 1. Test trực tiếp với WhatsApp API
```bash
# Test message đơn giản
python test_whatsapp_notification.py -m "Hello from Sharingan!"

# Test với file đính kèm
python test_whatsapp_notification.py -m "Scan report ready" -f /path/to/report.pdf
```

#### 2. Test qua Microservice
```bash
# Khởi động microservice trước
cd ../microservices
docker-compose up notification-service

# Test qua microservice
python test_whatsapp_notification.py -m "Test via microservice" --microservice

# Test với custom URL
python test_whatsapp_notification.py -m "Test" --microservice --service-url http://localhost:5002
```

#### 3. Full test (tạo report và gửi)
```bash
python test_whatsapp_notification.py -m "Full test with report" --full-test
```

### Yêu cầu

1. File `.env` phải có các biến sau:
```env
WHATSAPP_ACCESS_TOKEN=your_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_id_here
WHATSAPP_RECIPIENT_NUMBER=+84xxxxxxxxx
```

2. Nếu test qua microservice, cần start service trước:
```bash
cd microservices
docker-compose up notification-service
```

### Các options

- `-m, --message`: Message cần gửi (bắt buộc)
- `-f, --file`: Đường dẫn file cần gửi kèm
- `--microservice`: Test qua microservice thay vì direct API
- `--service-url`: URL của microservice (mặc định: http://localhost:5002)
- `--full-test`: Chạy full test bao gồm tạo report

### Troubleshooting

#### Lỗi "Missing WhatsApp credentials"
- Kiểm tra file `.env` có đầy đủ thông tin
- Chạy `python sharingan.py --create-env` để tạo template

#### Lỗi "Cannot connect to microservice"
- Đảm bảo microservice đang chạy
- Check: `docker ps | grep notification-service`

#### Lỗi "Failed to send message"
- Kiểm tra access token còn hạn
- Kiểm tra số điện thoại đúng format (+84...)
- Kiểm tra quota của WhatsApp Business API