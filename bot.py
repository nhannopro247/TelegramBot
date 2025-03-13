import os
import requests
import random
import string
import asyncio
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackContext

# Tải biến môi trường từ file .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
MAILTM_API = "https://api.mail.tm"

# Headers tránh lỗi 403
HEADERS = {"User-Agent": "Mozilla/5.0"}

# **Danh sách lệnh menu Telegram**
COMMANDS = [
    BotCommand("start", "Bắt đầu bot"),
    BotCommand("getmail", "Tạo email tạm thời"),
    BotCommand("inbox", "Kiểm tra hộp thư")
]

# **Hàm tạo email từ Mail.tm**
def generate_email():
    response = requests.get(f"{MAILTM_API}/domains", headers=HEADERS)
    if response.status_code != 200:
        return None
    
    domains = response.json().get("hydra:member", [])
    if not domains:
        return None

    domain = domains[0]["domain"]
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    email = f"{username}@{domain}"

    payload = {"address": email, "password": "securepassword"}
    response = requests.post(f"{MAILTM_API}/accounts", json=payload, headers=HEADERS)
    
    return email if response.status_code == 201 else None

# **Hàm lấy token đăng nhập**
def get_token(email, password="securepassword"):
    response = requests.post(f"{MAILTM_API}/token", json={"address": email, "password": password}, headers=HEADERS)
    return response.json().get("token") if response.status_code == 200 else None

# **Lệnh /start**
async def start(update: Update, context: CallbackContext) -> None:
    await context.bot.set_my_commands(COMMANDS)  # Cập nhật menu lệnh
    await update.message.reply_text("👋 Xin chào! Gõ /getmail để lấy email tạm thời.")

# **Lệnh /getmail: Tạo email tạm thời**
async def getmail(update: Update, context: CallbackContext) -> None:
    email = generate_email()
    if not email:
        await update.message.reply_text("⚠ Không thể tạo email! Vui lòng thử lại sau.")
        return

    token = get_token(email)
    if not token:
        await update.message.reply_text("⚠ Lỗi đăng nhập API!")
        return

    context.user_data["email"] = email
    context.user_data["token"] = token
    await update.message.reply_text(f"📩 Email của bạn: {email}\nGõ /inbox để kiểm tra thư.")

# **Lệnh /inbox: Kiểm tra hộp thư + Nội dung email**
async def inbox(update: Update, context: CallbackContext) -> None:
    email = context.user_data.get("email")
    token = context.user_data.get("token")

    if not email or not token:
        await update.message.reply_text("❌ Bạn chưa tạo email! Gõ /getmail để lấy email mới.")
        return

    response = requests.get(f"{MAILTM_API}/messages", headers={"Authorization": f"Bearer {token}"})
    if response.status_code != 200:
        await update.message.reply_text("⚠ Lỗi API, thử lại sau.")
        return

    messages = response.json().get("hydra:member", [])
    if not messages:
        await update.message.reply_text("📭 Hộp thư trống!")
        return

    email_id = messages[0]["id"]
    email_details = requests.get(f"{MAILTM_API}/messages/{email_id}", headers={"Authorization": f"Bearer {token}"})
    
    if email_details.status_code == 200:
        email_data = email_details.json()
        sender = email_data["from"]["address"]
        subject = email_data["subject"]
        date = email_data["createdAt"]
        body = email_data.get("text", email_data.get("html", "📜 (Không có nội dung)"))

        await update.message.reply_text(
            f"📧 Từ: {sender}\n"
            f"📌 Tiêu đề: {subject}\n"
            f"📅 Ngày gửi: {date}\n\n"
            f"📜 Nội dung:\n{body}"
        )
    else:
        await update.message.reply_text("⚠ Lỗi khi lấy nội dung email!")

# **Khởi động bot**
app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("getmail", getmail))
app.add_handler(CommandHandler("inbox", inbox))

print("✅ Bot đang chạy...")
app.run_polling()
