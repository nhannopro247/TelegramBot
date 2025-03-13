#!/bin/bash
echo "🔄 Đang kiểm tra cập nhật..."

# Chuyển đến thư mục bot
cd /home/ubuntu/TelegramBot  # ⚠ Thay đường dẫn đúng với bot của bạn

# Tải bản cập nhật mới nhất từ GitHub
git pull origin main

# Restart bot nếu có cập nhật
echo "✅ Bot đã được cập nhật! Restarting..."
pkill -f bot.py  # Dừng bot cũ
python3 bot.py &  # Chạy bot mới
