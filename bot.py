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
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "@nhomsharemodallgame")
PORT = int(os.getenv("PORT", "8080"))

# Lưu trữ dữ liệu người dùng
user_database = {}

# Số lượng kho acc thực tế (Tự động trừ khi có người mua)
stock_clone30 = 30  # Số lượng Acc Clone Level 30 ban đầu
stock_clone58 = 50  # Số lượng Acc Clone Level 5-8 ban đầu

# Kho acc ảo tương ứng
FAKE_ACCOUNTS_CLONE30 = [
    "💎 <b>ACC CLONE LEVEL 30</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>clone30_pro_1@gmail.com</code>\n🔑 Mật khẩu: <code>pass30vn123</code>\n⚡ Trạng thái: Sẵn sàng chiến!",
    "💎 <b>ACC CLONE LEVEL 30</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>clone30_vip_99@gmail.com</code>\n🔑 Mật khẩu: <code>ffpro2026</code>\n⚡ Trạng thái: Trắng thông tin, full skin!"
]

FAKE_ACCOUNTS_CLONE58 = [
    "🔥 <b>ACC CLONE LEVEL 5-8</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>clone58_1@gmail.com</code>\n🔑 Mật khẩu: <code>clone123456</code>\n⚡ Trạng thái: Sạch đẹp, cày kéo mượt mà!",
    "🔥 <b>ACC CLONE LEVEL 5-8</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>clone58_2@gmail.com</code>\n🔑 Mật khẩu: <code>abcxyz789</code>\n⚡ Trạng thái: Nick phụ ngon lành!"
]

# Khởi tạo Flask App
flask_app = Flask(__name__)

# Khởi tạo Telegram Application
application = Application.builder().token(TOKEN).updater(None).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    if user_id not in user_database:
        user_database[user_id] = {"xu": 0, "joined": False}

    # Xử lý ref
    args = context.args
    if args and args[0].startswith("ref_"):
        try:
            referrer_id = int(args[0].split("_")[1])
            if referrer_id != user_id and referrer_id in user_database:
                if not user_database[user_id].get("has_been_referred", False):
                    user_database[user_id]["has_been_referred"] = True
                    user_database[user_id]["referrer_id"] = referrer_id
        except Exception as e:
            logger.error(f"Lỗi xử lý ref: {e}")

    # Nếu người dùng đã từng xác nhận join trước đó thì vào thẳng menu luôn
    if user_database[user_id].get("joined", False):
        await send_main_menu(update, context)
        return

    # Kiểm tra thực tế trên Telegram
    is_joined = False
    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            is_joined = True
    except Exception as e:
        logger.error(f"Lỗi kiểm tra thành viên kênh: {e}")

    if is_joined:
        user_database[user_id]["joined"] = True
        if user_database[user_id].get("has_been_referred", False) and not user_database[user_id].get("reward_given", False):
            referrer_id = user_database[user_id].get("referrer_id")
            if referrer_id and referrer_id in user_database:
                user_database[referrer_id]["xu"] += 2
                user_database[user_id]["reward_given"] = True
                try:
                    await context.bot.send_message(chat_id=referrer_id, text="🎉 <b>Có người vừa bấm link ref và join kênh thành công! Bạn được cộng +2 xu.</b>", parse_mode="HTML")
                except Exception:
                    pass

        await send_main_menu(update, context)
        return

    # Nếu chưa tham gia, hiển thị yêu cầu
    keyboard = [
        [InlineKeyboardButton("📢 Ghé thăm & Tham gia Kênh", url="https://t.me/nhomsharemodallgame")],
        [InlineKeyboardButton("✅ Tôi đã tham gia", callback_data="check_joined")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = (
        "<b>⚠️ THÔNG BÁO XÁC NHẬN</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "Để sử dụng hệ thống đổi Acc Free Fire, bạn bắt buộc phải tham gia kênh:\n\n"
        "👉 <b>Kênh:</b> @nhomsharemodallgame\n\n"
        "<i>Sau khi tham gia xong, hãy bấm nút bên dưới để vào hệ thống!</i>"
    )
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def check_joined_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if user_id not in user_database:
        user_database[user_id] = {"xu": 0, "joined": False}

    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            user_database[user_id]["joined"] = True
            
            if user_database[user_id].get("has_been_referred", False) and not user_database[user_id].get("reward_given", False):
                referrer_id = user_database[user_id].get("referrer_id")
                if referrer_id and referrer_id in user_database:
                    user_database[referrer_id]["xu"] += 2
                    user_database[user_id]["reward_given"] = True
                    try:
                        await context.bot.send_message(chat_id=referrer_id, text="🎉 <b>Có người vừa bấm link ref và join kênh thành công! Bạn được cộng +2 xu.</b>", parse_mode="HTML")
                    except Exception:
                        pass

            try:
                await query.message.delete()
            except Exception:
                pass
            await send_main_menu_callback(query, context)
        else:
            await query.answer("❌ Bạn chưa tham gia kênh, vui lòng bấm tham gia trước!", show_alert=True)
    except Exception:
        await query.answer("❌ Lỗi kiểm tra. Đảm bảo bot đã là Admin của Kênh!", show_alert=True)

async def send_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = user_database[user_id]
    
    text = (
        "🎮 <b>HỆ THỐNG ĐỔI ACC FREE FIRE VIP</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📦 <b>Kho tài khoản hiện có:</b>\n"
        f"• <b>Acc Clone Lv 30:</b> <code>{stock_clone30} acc</code> <i>(Giá: 40 xu)</i>\n"
        f"• <b>Acc Clone Lv 5-8:</b> <code>{stock_clone58} acc</code> <i>(Giá: 20 xu)</i>\n\n"
        "📌 <i>Lưu ý: Người được mời phải join kênh thành công bạn mới nhận được xu.</i>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Số dư của bạn:</b> <code>{data['xu']} xu</code>\n"
        "🎁 <b>Cách kiếm xu:</b> Lấy link chia sẻ, người khác bấm vào và join kênh (1 Ref = 2 xu)"
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 Đổi Clone Lv 30 (40 Xu)", callback_data="doi_clone30")],
        [InlineKeyboardButton("🔥 Đổi Clone Lv 5-8 (20 Xu)", callback_data="doi_clone58")],
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
        f"• <b>Acc Clone Lv 30:</b> <code>{stock_clone30} acc</code> <i>(Giá: 40 xu)</i>\n"
        f"• <b>Acc Clone Lv 5-8:</b> <code>{stock_clone58} acc</code> <i>(Giá: 20 xu)</i>\n\n"
        "📌 <i>Lưu ý: Người được mời phải join kênh thành công bạn mới nhận được xu.</i>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Số dư của bạn:</b> <code>{data['xu']} xu</code>\n"
        "🎁 <b>Cách kiếm xu:</b> Lấy link chia sẻ, người khác bấm vào và join kênh (1 Ref = 2 xu)"
    )
    
    keyboard = [
        [InlineKeyboardButton("💎 Đổi Clone Lv 30 (40 Xu)", callback_data="doi_clone30")],
        [InlineKeyboardButton("🔥 Đổi Clone Lv 5-8 (20 Xu)", callback_data="doi_clone58")],
        [InlineKeyboardButton("🎁 Kiếm Xu (Lấy Link Ref)", callback_data="kiem_xu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stock_clone30, stock_clone58
    query = update.callback_query
    data_callback = query.data
    user_id = query.from_user.id

    if data_callback == "check_joined":
        await check_joined_callback(update, context)
        return

    if user_id not in user_database:
        user_database[user_id] = {"xu": 0, "joined": False}

    user_data = user_database[user_id]

    if data_callback == "doi_clone30":
        if stock_clone30 <= 0:
            await query.answer("❌ Kho Acc Clone Lv 30 đã hết hàng!", show_alert=True)
        elif user_data["xu"] < 40:
            await query.answer("❌ Bạn cần 40 xu để đổi Acc Clone Lv 30!", show_alert=True)
        else:
            user_data["xu"] -= 40
            stock_clone30 -= 1  # Trừ 1 acc trong kho
            acc_info = random.choice(FAKE_ACCOUNTS_CLONE30)
            await query.answer("🎉 Đổi acc thành công!", show_alert=False)
            await context.bot.send_message(chat_id=user_id, text=f"✅ <b>GIAO DỊCH THÀNH CÔNG</b>\n\n{acc_info}", parse_mode="HTML")
            
    elif data_callback == "doi_clone58":
        if stock_clone58 <= 0:
            await query.answer("❌ Kho Acc Clone Lv 5-8 đã hết hàng!", show_alert=True)
        elif user_data["xu"] < 20:
            await query.answer("❌ Bạn cần 20 xu để đổi Acc Clone Lv 5-8!", show_alert=True)
        else:
            user_data["xu"] -= 20
            stock_clone58 -= 1  # Trừ 1 acc trong kho
            acc_info = random.choice(FAKE_ACCOUNTS_CLONE58)
            await query.answer("🎉 Đổi acc thành công!", show_alert=False)
            await context.bot.send_message(chat_id=user_id, text=f"✅ <b>GIAO DỊCH THÀNH CÔNG</b>\n\n{acc_info}", parse_mode="HTML")
            
    elif data_callback == "kiem_xu":
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        await query.answer(f"Link giới thiệu của bạn đã sẵn sàng!", show_alert=True)
        await context.bot.send_message(
            chat_id=user_id, 
            text=f"🔗 <b>Link giới thiệu của bạn:</b>\n<code>{ref_link}</code>\n\n<i>Hãy gửi link này cho bạn bè. Khi họ bấm vào và tham gia kênh, bạn sẽ tự động nhận được +2 xu!</i>",
            parse_mode="HTML"
        )

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
