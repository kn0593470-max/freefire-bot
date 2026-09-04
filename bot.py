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
# Chuyển về Kênh của bạn
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "@nhomsharemodallgame")
PORT = int(os.getenv("PORT", "8080"))

# Lưu trữ dữ liệu tạm thời (user_id: {"xu": 0})
user_database = {}

# Kho acc ảo
FAKE_ACCOUNTS_LV30 = [
    "💎 <b>TÀI KHOẢN FREE FIRE LV.30</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>accshop30_1@gmail.com</code>\n🔑 Mật khẩu: <code>pass123456</code>\n⚡ Trạng thái: Sẵn sàng chiến đấu!",
    "💎 <b>TÀI KHOẢN FREE FIRE LV.30</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>ffvip_30_pro@gmail.com</code>\n🔑 Mật khẩu: <code>ffpro999</code>\n⚡ Trạng thái: Trắng thông tin, full skin!",
    "💎 <b>TÀI KHOẢN FREE FIRE LV.30</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>freefire_lv30_az@gmail.com</code>\n🔑 Mật khẩu: <code>aabbcc123</code>\n⚡ Trạng thái: Uy tín, chất lượng!"
]

FAKE_ACCOUNTS_LV5 = [
    "🔥 <b>TÀI KHOẢN FREE FIRE LV.5</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>accnhanh_1@gmail.com</code>\n🔑 Mật khẩu: <code>12345678</code>\n⚡ Trạng thái: Sạch đẹp, vào là chơi!",
    "🔥 <b>TÀI KHOẢN FREE FIRE LV.5</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>newbie_ff_2@gmail.com</code>\n🔑 Mật khẩu: <code>abcxyz888</code>\n⚡ Trạng thái: Nick phụ ngon lành!"
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

    # Kiểm tra xem user đã ở trong Kênh chưa
    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            await send_main_menu(update, context)
            return
    except Exception as e:
        logger.error(f"Lỗi kiểm tra thành viên kênh: {e}")

    # Nếu chưa tham gia, hiển thị giao diện bắt buộc đẹp mắt
    keyboard = [
        [InlineKeyboardButton("📢 Ghé thăm & Tham gia Kênh", url="https://t.me/nhomsharemodallgame")],
        [InlineKeyboardButton("✅ Tôi đã tham gia", callback_data="check_joined")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "<b>⚠️ THÔNG BÁO XÁC NHẬN</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Để sử dụng hệ thống đổi Acc Free Fire miễn phí, bạn vui lòng tham gia kênh của chúng tôi trước:\n\n"
        "👉 <b>Kênh:</b> @nhomsharemodallgame\n\n"
        "<i>Sau khi tham gia xong, hãy bấm nút bên dưới để vào hệ thống!</i>"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
    elif update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")

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
            await query.answer("Bạn vui lòng tham gia kênh trước!", show_alert=True)
    except Exception:
        await query.answer("Bạn vui lòng tham gia kênh (Đảm bảo bot đã là Admin Kênh)", show_alert=True)

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_database[user_id]
    
    text = (
        "🎮 <b>HỆ THỐNG ĐỔI ACC FREE FIRE VIP</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📦 <b>Kho tài khoản hiện có:</b>\n"
        "• <b>Acc Level 30:</b> Kho còn 31 acc <i>(Giá: 10 xu)</i>\n"
        "• <b>Acc Level 5:</b> Kho còn 102 acc <i>(Giá: 2 xu)</i>\n\n"
        "📌 <i>Giới hạn: Mỗi ngày đổi tối đa 2 lượt.</i>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Số dư của bạn:</b> <code>{data['xu']} xu</code>\n"
        "🎁 <b>Cách kiếm xu:</b> Chia sẻ link giới thiệu (1 Ref = 2 xu)"
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 Đổi Acc Lv 30 (10 Xu)", callback_data="doi_lv30")],
        [InlineKeyboardButton("🔥 Đổi Acc Lv 5 (2 Xu)", callback_data="doi_lv5")],
        [InlineKeyboardButton("🎁 Kiếm Xu (Lấy Link Ref)", callback_data="kiem_xu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def send_main_menu_callback(query, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    data = user_database[user_id]
    
    text = (
        "🎮 <b>HỆ THỐNG ĐỔI ACC FREE FIRE VIP</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📦 <b>Kho tài khoản hiện có:</b>\n"
        "• <b>Acc Level 30:</b> Kho còn 31 acc <i>(Giá: 10 xu)</i>\n"
        "• <b>Acc Level 5:</b> Kho còn 102 acc <i>(Giá: 2 xu)</i>\n\n"
        "📌 <i>Giới hạn: Mỗi ngày đổi tối đa 2 lượt.</i>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Số dư của bạn:</b> <code>{data['xu']} xu</code>\n"
        "🎁 <b>Cách kiếm xu:</b> Chia sẻ link giới thiệu (1 Ref = 2 xu)"
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 Đổi Acc Lv 30 (10 Xu)", callback_data="doi_lv30")],
        [InlineKeyboardButton("🔥 Đổi Acc Lv 5 (2 Xu)", callback_data="doi_lv5")],
        [InlineKeyboardButton("🎁 Kiếm Xu (Lấy Link Ref)", callback_data="kiem_xu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

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
            await query.answer("❌ Bạn không đủ 10 xu để đổi acc Lv 30!", show_alert=True)
        else:
            user_data["xu"] -= 10
            acc_info = random.choice(FAKE_ACCOUNTS_LV30)
            await query.answer("🎉 Đổi acc thành công!", show_alert=False)
            await context.bot.send_message(chat_id=user_id, text=f"✅ <b>GIAO DỊCH THÀNH CÔNG</b>\n\n{acc_info}", parse_mode="HTML")
            
    elif data_callback == "doi_lv5":
        if user_data["xu"] < 2:
            await query.answer("❌ Bạn không đủ 2 xu để đổi acc Lv 5!", show_alert=True)
        else:
            user_data["xu"] -= 2
            acc_info = random.choice(FAKE_ACCOUNTS_LV5)
            await query.answer("🎉 Đổi acc thành công!", show_alert=False)
            await context.bot.send_message(chat_id=user_id, text=f"✅ <b>GIAO DỊCH THÀNH CÔNG</b>\n\n{acc_info}", parse_mode="HTML")
            
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
