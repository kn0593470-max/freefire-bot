import os
import logging
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackQueryHandler

# Bật log
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Tích hợp trực tiếp Token bot của bạn
TOKEN = "8483501766:AAFSg-dWNLZjmKNQxMKQzZh2KOoyA_YBL5E"
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "@nhomsharemodallgame")
PORT = int(os.getenv("PORT", "8080"))

# URL trang web trên Render của bạn (Thay bằng link Render thật của bạn sau khi deploy)
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "https://your-app-name.onrender.com")

# Lưu trữ dữ liệu tạm thời (user_id: {"xu": 0, "doi_hom_nay": 0})
user_database = {}

# Khởi tạo Flask App
flask_app = Flask(__name__)

# Khởi tạo Telegram Application
application = Application.builder().token(TOKEN).updater(None).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if user_id not in user_database:
        user_database[user_id] = {"xu": 0, "doi_hom_nay": 0}

    # Xử lý nếu có tham gia giới thiệu (Ref) qua lệnh /start ref_xxxx
    args = context.args
    if args and args[0].startswith("ref_"):
        try:
            referrer_id = int(args[0].split("_")[1])
            # Không cho phép tự ref chính mình
            if referrer_id != user_id and referrer_id in user_database:
                # Kiểm tra xem user này đã được tính ref chưa (tránh spam)
                if "referred" not in user_database[user_id]:
                    user_database[user_id]["referred"] = True
                    user_database[referrer_id]["xu"] += 2  # Cộng 2 xu cho người giới thiệu
        except Exception as e:
            logger.error(f"Lỗi xử lý ref: {e}")

    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            await send_main_menu(update, context)
            return
    except Exception as e:
        logger.error(f"Lỗi kiểm tra thành viên: {e}")

    keyboard = [[InlineKeyboardButton("✅ Tôi đã tham gia", callback_data="check_joined")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "Vui lòng tham gia nhóm của chúng tôi để tiếp tục sử dụng:\n"
        "https://t.me/nhomsharemodallgame"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)

async def check_joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            await query.message.delete()
            await send_main_menu_callback(query, context)
        else:
            await query.answer("Bạn vẫn chưa gia nhập nhóm!", show_alert=True)
    except Exception:
        await query.answer("Có lỗi xảy ra, hãy chắc chắn bạn đã tham gia nhóm và bot là Admin!", show_alert=True)

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_database[user_id]
    
    text = (
        "Kho acc free fire:\n\n"
        "Acc level 30 : 31 (Nhấn đổi cần 10 xu)\n"
        "Acc level 5 : 102 (Nhấn đổi cần 2 xu)\n\n"
        "Mỗi ngày chỉ đổi được 2 lượt\n\n"
        f"Số dư của bạn : {data['xu']} xu\n"
        "Cách kiếm xu: chia sẻ ref (1 ref = 2xu)"
    )
    
    keyboard = [
        [InlineKeyboardButton("Đổi Acc Lv 30", callback_data="doi_lv30")],
        [InlineKeyboardButton("Đổi Acc Lv 5", callback_data="doi_lv5")],
        [InlineKeyboardButton("Kiếm Xu (Lấy link Ref)", callback_data="kiem_xu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup)

async def send_main_menu_callback(query, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    data = user_database[user_id]
    
    text = (
        "Kho acc free fire:\n\n"
        "Acc level 30 : 31 (Nhấn đổi cần 10 xu)\n"
        "Acc level 5 : 102 (Nhấn đổi cần 2 xu)\n\n"
        "Mỗi ngày chỉ đổi được 2 lượt\n\n"
        f"Số dư của bạn : {data['xu']} xu\n"
        "Cách kiếm xu: chia sẻ ref (1 ref = 2xu)"
    )
    
    keyboard = [
        [InlineKeyboardButton("Đổi Acc Lv 30", callback_data="doi_lv30")],
        [InlineKeyboardButton("Đổi Acc Lv 5", callback_data="doi_lv5")],
        [InlineKeyboardButton("Kiếm Xu (Lấy link Ref)", callback_data="kiem_xu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data_callback = query.data
    user_id = query.from_user.id

    if data_callback == "check_joined":
        await check_joined_callback(update, context)
        return

    if user_id not in user_database:
        user_database[user_id] = {"xu": 0, "doi_hom_nay": 0}

    user_data = user_database[user_id]

    if data_callback == "doi_lv30":
        if user_data["xu"] < 10:
            await query.answer("Bạn cần 10xu để tiếp tục!", show_alert=True)
        else:
            user_data["xu"] -= 10
            await query.answer("Đổi tài khoản thành công! (Lv 30)", show_alert=True)
    elif data_callback == "doi_lv5":
        if user_data["xu"] < 2:
            await query.answer("Bạn cần 2xu để tiếp tục!", show_alert=True)
        else:
            user_data["xu"] -= 2
            await query.answer("Đổi tài khoản thành công! (Lv 5)", show_alert=True)
    elif data_callback == "kiem_xu":
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        await query.answer(f"Link giới thiệu của bạn: {ref_link}", show_alert=True)

# Đăng ký các Handler
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put(update)
    return "OK", 200

@flask_app.route("/", methods=["GET"])
def index():
    return "Bot is running via Webhook!", 200

async def setup_webhook():
    await application.initialize()
    webhook_url = f"{RENDER_EXTERNAL_URL}/{TOKEN}"
    await application.bot.set_url(webhook_url)
    logger.info(f"Đã cài đặt Webhook thành công tới: {webhook_url}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(setup_webhook())
    flask_app.run(host="0.0.0.0", port=PORT)
