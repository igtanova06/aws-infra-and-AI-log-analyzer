# Telegram Bot Setup - Hoàn Tất ✅

## Thông Tin Bot

- **Bot Name**: nhutHao05_log_analyzer_bot
- **Bot Username**: @nhutHao05_log_analyzer_bot
- **Bot Token**: `8721800274:AAFDTroQlg8T4KT07nIpeyPV0G3Z3ZHu1gs`
- **Chat ID**: `8788132884`
- **Bot URL**: https://t.me/nhutHao05_log_analyzer_bot

## Các File Đã Cấu Hình

### 1. Local Development
- ✅ `AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui/.env` - File môi trường local
- ✅ `AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui/.env.example` - Template đã cập nhật

### 2. Ansible Deployment
- ✅ `ansible/inventory/group_vars/all.yml` - Biến Ansible cho deployment
- ✅ `ansible/templates/app.env.j2` - Template môi trường cho EC2

## Cách Sử Dụng

### Test Local
```bash
cd AI_Log_Analysis-Project-1/bedrock-log-analyzer-ui
python -m streamlit run streamlit_app.py
```

### Deploy lên AWS
```bash
cd ansible
ansible-playbook -i inventory/aws_ec2.yml playbooks/site.yml
```

## Kiểm Tra Bot Hoạt Động

### 1. Test gửi tin nhắn thủ công
```python
import requests

bot_token = "8721800274:AAFDTroQlg8T4KT07nIpeyPV0G3Z3ZHu1gs"
chat_id = "8788132884"
message = "🤖 Test message from Log Analyzer"

url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
data = {"chat_id": chat_id, "text": message}

response = requests.post(url, data=data)
print(response.json())
```

### 2. Trigger alert từ hệ thống
- Chạy `simulate_attack.py` để tạo log bất thường
- Hệ thống sẽ tự động gửi cảnh báo qua Telegram

## Bảo Mật

⚠️ **LƯU Ý QUAN TRỌNG**:
- Bot token là thông tin nhạy cảm, không commit vào Git
- File `.env` đã được thêm vào `.gitignore`
- Chỉ chia sẻ token với người có quyền truy cập hệ thống

## Tính Năng Telegram Alert

Bot sẽ gửi thông báo khi:
- ✅ Phát hiện SQL Injection
- ✅ Phát hiện XSS Attack
- ✅ Phát hiện Brute Force Login
- ✅ Phát hiện Path Traversal
- ✅ Phát hiện bất kỳ pattern tấn công nào trong `correlation_rules.json`

## Troubleshooting

### Bot không gửi tin nhắn
1. Kiểm tra bot token và chat ID
2. Đảm bảo đã nhắn tin cho bot ít nhất 1 lần
3. Kiểm tra biến môi trường `TELEGRAM_ALERTS_ENABLED=true`

### Lỗi kết nối
```bash
# Test kết nối bot
curl "https://api.telegram.org/bot8721800274:AAFDTroQlg8T4KT07nIpeyPV0G3Z3ZHu1gs/getMe"
```

## Tài Liệu Tham Khảo

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [BotFather Commands](https://core.telegram.org/bots#botfather)
- [Telegram Bot Tutorial](https://core.telegram.org/bots/tutorial)
