import os
import logging
import random
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, ContextTypes, CommandHandler, CallbackQueryHandler

# Bật log
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Token bot của bạn
TOKEN = "8483501766:AAFSg-dWNLZjmKNQxMKQzZh2KOoyA_YBL5E"
# Link nhóm chat mới của bạn
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "@nhomchatsharemod")
PORT = int(os.getenv("PORT", "8080"))

# Lưu trữ dữ liệu tạm thời (user_id: {"xu": 0})
user_database = {}

# Kho acc ảo để bot tự trả khi khách đổi thành công
FAKE_ACCOUNTS_LV30 = [
    "🎮 Acc FF Lv.30\nTK: accshop30_1@gmail.com | MK: pass123456\nTrạng thái: Sẵn sàng chiến!",
    "🎮 Acc FF Lv.30\nTK: ffvip_30_pro@gmail.com | MK: ffpro999\nTrạng thái: Trắng thông tin!",
    "🎮 Acc FF Lv.30\nTK: freefire_lv30_az@gmail.com | MK: aabbcc123\nTrạng thái: Có skin súng!"
]

FAKE_ACCOUNTS_LV5 = [
    "🎮 Acc FF Lv.5 (New)\nTK: accnhanh_1@gmail.com | MK: 12345678\nTrạng thái: Sạch đẹp!",
    "🎮 Acc FF Lv.5 (New)\nTK: newbie_ff_2@gmail.com | MK: abcxyz888\nTrạng thái: Nick phụ ngon lành!"
]

# Khởi tạo Flask App
flask_app = Flask(__name__)

# Khởi tạo Telegram Application
application = Application.builder().token(TOKEN).updater(None).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if user_id not in user_database:
        user_database[user_id] = {"xu": 0}

    # Xử lý ref
    args = context.args
    if args and args[0].startswith("ref_"):
        try:
            referrer_id = int(args[0].split("_")[1])
            if referrer_id != user_id and referrer_id in user_database:
                if "referred" not in user_database[user_id]:
                    user_database[user_id]["referred"] = True
                    user_database[referrer_id]["xu"] += 2  # Cộng 2 xu cho người giới thiệu
        except Exception as e:
            logger.error(f"Lỗi xử lý ref: {e}")

    # Kiểm tra xem user đã ở trong nhóm chat chưa
    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            await send_main_menu(update, context)
            return
    except Exception as e:
        logger.error(f"Lỗi kiểm tra thành viên nhóm: {e}")

    # Nếu chưa tham gia, hiển thị yêu cầu
    keyboard = [[InlineKeyboardButton("✅ Tôi đã tham gia", callback_data="check_joined")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "Bạn vui lòng tham gia nhóm để tiếp tục sử dụng:\n"
        "https://t.me/nhomchatsharemod"
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
            try:
                await query.message.delete()
            except Exception:
                pass
            await send_main_menu_callback(query, context)
        else:
            await query.answer("Bạn vui lòng tham gia nhóm", show_alert=True)
    except Exception:
        await query.answer("Bạn vui lòng tham gia nhóm", show_alert=True)

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
        user_database[user_id] = {"xu": 0}

    user_data = user_database[user_id]

    if data_callback == "doi_lv30":
        if user_data["xu"] < 10:
            await query.answer("Bạn cần 10 xu để đổi acc Lv 30!", show_alert=True)
        else:
            user_data["xu"] -= 10
            acc_info = random.choice(FAKE_ACCOUNTS_LV30)
            await query.answer("Đổi thành công!", show_alert=False)
            await context.bot.send_message(chat_id=user_id, text=f"🎉 Bạn đã đổi thành công:\n\n{acc_info}")
            
    elif data_callback == "doi_lv5":
        if user_data["xu"] < 2:
            await query.answer("Bạn cần 2 xu để đổi acc Lv 5!", show_alert=True)
        else:
            user_data["xu"] -= 2
            acc_info = random.choice(FAKE_ACCOUNTS_LV5)
            await query.answer("Đổi thành công!", show_alert=False)
            await context.bot.send_message(chat_id=user_id, text=f"🎉 Bạn đã đổi thành công:\n\n{acc_info}")
            
    elif data_callback == "kiem_xu":
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        await query.answer(f"Link giới thiệu của bạn: {ref_link}", show_alert=True)

# Đăng ký Handler
application.add_handler(CommandHandler("start", start))
application.add_handler(CallbackQueryHandler(button_handler))

@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    json_data = request.get_json(force=True)
    update = Update.de_json(json_data, application.bot)
    
    async def run_update():
        if not application.running:
            await application.initialize()
        await application.process_update(update)

    asyncio.run(run_update())
    return "OK", 200

@flask_app.route("/", methods=["GET"])
def index():
    return "Bot is running via Webhook!", 200

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=PORT)
