import os
import logging
import random
import sqlite3
import asyncio
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, 
    ContextTypes, 
    CommandHandler, 
    CallbackQueryHandler
)

# Bật log
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Token bot và cấu hình
TOKEN = "8483501766:AAFSg-dWNLZjmKNQxMKQzZh2KOoyA_YBL5E"
GROUP_CHAT_ID = os.getenv("GROUP_CHAT_ID", "@nhomsharemodallgame")
PORT = int(os.getenv("PORT", "8080"))

ADMIN_ID = 7907990385  # ID Admin được quyền cộng xu

# --- QUẢN LÝ CƠ SỞ DỮ LIỆU SQLITE (LƯU TRỮ VĨNH VIỄN) ---
def init_db():
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            xu INTEGER DEFAULT 0,
            joined INTEGER DEFAULT 0,
            has_been_referred INTEGER DEFAULT 0,
            referrer_id INTEGER DEFAULT 0,
            reward_given INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def get_user(user_id):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT xu, joined, has_been_referred, referrer_id, reward_given FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        cursor.execute("INSERT INTO users (user_id, xu, joined) VALUES (?, 0, 0)", (user_id,))
        conn.commit()
        row = (0, 0, 0, 0, 0)
    conn.close()
    return {"xu": row[0], "joined": row[1], "has_been_referred": row[2], "referrer_id": row[3], "reward_given": row[4]}

def update_user_field(user_id, field, value):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute(f"UPDATE users SET {field} = ? WHERE user_id = ?", (value, user_id))
    conn.commit()
    conn.close()

def add_user_xu(user_id, amount):
    conn = sqlite3.connect("bot_database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT xu FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row:
        new_xu = row[0] + amount
        cursor.execute("UPDATE users SET xu = ? WHERE user_id = ?", (new_xu, user_id))
    else:
        cursor.execute("INSERT INTO users (user_id, xu, joined) VALUES (?, ?, 0)", (user_id, amount))
    conn.commit()
    conn.close()

# Kho tài khoản
stock_clone30 = 30
stock_clone58 = 50

FAKE_ACCOUNTS_CLONE30 = [
    "💎 <b>ACC CLONE LEVEL 30</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>clone30_pro_1@gmail.com</code>\n🔑 Mật khẩu: <code>pass30vn123</code>\n⚡ Trạng thái: Sẵn sàng chiến!",
    "💎 <b>ACC CLONE LEVEL 30</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>clone30_vip_99@gmail.com</code>\n🔑 Mật khẩu: <code>ffpro2026</code>\n⚡ Trạng thái: Trắng thông tin, full skin!"
]

FAKE_ACCOUNTS_CLONE58 = [
    "🔥 <b>ACC CLONE LEVEL 5-8</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>clone58_1@gmail.com</code>\n🔑 Mật khẩu: <code>clone123456</code>\n⚡ Trạng thái: Sạch đẹp, cày kéo mượt mà!",
    "🔥 <b>ACC CLONE LEVEL 5-8</b>\n━━━━━━━━━━━━━━━━━━━\n📧 Tài khoản: <code>clone58_2@gmail.com</code>\n🔑 Mật khẩu: <code>abcxyz789</code>\n⚡ Trạng thái: Nick phụ ngon lành!"
]

flask_app = Flask(__name__)
application = Application.builder().token(TOKEN).updater(None).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    get_user(user_id) # Khởi tạo nếu chưa có

    # Xử lý ref
    args = context.args
    if args and args[0].startswith("ref_"):
        try:
            referrer_id = int(args[0].split("_")[1])
            if referrer_id != user_id:
                u_data = get_user(user_id)
                if not u_data["has_been_referred"]:
                    update_user_field(user_id, "has_been_referred", 1)
                    update_user_field(user_id, "referrer_id", referrer_id)
        except Exception as e:
            logger.error(f"Lỗi xử lý ref: {e}")

    # Nếu người dùng đã từng join trước đó, vào thẳng menu
    u_data = get_user(user_id)
    if u_data["joined"] == 1:
        await send_main_menu(update, context)
        return

    # Kiểm tra thực tế trên Kênh
    is_joined = False
    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            is_joined = True
    except Exception as e:
        logger.error(f"Lỗi kiểm tra thành viên kênh: {e}")

    if is_joined:
        update_user_field(user_id, "joined", 1)
        u_data = get_user(user_id)
        if u_data["has_been_referred"] == 1 and u_data["reward_given"] == 0:
            referrer_id = u_data["referrer_id"]
            add_user_xu(referrer_id, 2)
            update_user_field(user_id, "reward_given", 1)
            try:
                await context.bot.send_message(chat_id=referrer_id, text="🎉 <b>Có người vừa bấm link ref và join kênh thành công! Bạn được cộng +2 xu.</b>", parse_mode="HTML")
            except Exception:
                pass

        await send_main_menu(update, context)
        return

    # Chưa tham gia
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

    try:
        member = await context.bot.get_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id)
        if member.status in ["creator", "administrator", "member"]:
            update_user_field(user_id, "joined", 1)
            u_data = get_user(user_id)
            
            if u_data["has_been_referred"] == 1 and u_data["reward_given"] == 0:
                referrer_id = u_data["referrer_id"]
                add_user_xu(referrer_id, 2)
                update_user_field(user_id, "reward_given", 1)
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
    u_data = get_user(user_id)
    
    text = (
        "🎮 <b>HỆ THỐNG ĐỔI ACC FREE FIRE VIP</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📦 <b>Kho tài khoản hiện có:</b>\n"
        f"• <b>Acc Clone Lv 30:</b> <code>{stock_clone30} acc</code> <i>(Giá: 15 xu)</i>\n"
        f"• <b>Acc Clone Lv 5-8:</b> <code>{stock_clone58} acc</code> <i>(Giá: 10 xu)</i>\n\n"
        "📌 <i>Lưu ý: Người được mời phải join kênh thành công bạn mới nhận được xu.</i>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Số dư của bạn:</b> <code>{u_data['xu']} xu</code>\n"
        "🎁 <b>Cách kiếm xu:</b> Lấy link chia sẻ, người khác bấm vào và join kênh (1 Ref = 2 xu)"
    )
    keyboard = [
        [InlineKeyboardButton("💎 Đổi Clone Lv 30 (15 Xu)", callback_data="doi_clone30")],
        [InlineKeyboardButton("🔥 Đổi Clone Lv 5-8 (10 Xu)", callback_data="doi_clone58")],
        [InlineKeyboardButton("🎁 Kiếm Xu (Lấy Link Ref)", callback_data="kiem_xu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")

async def send_main_menu_callback(query, context: ContextTypes.DEFAULT_TYPE):
    user_id = query.from_user.id
    u_data = get_user(user_id)
    
    text = (
        "🎮 <b>HỆ THỐNG ĐỔI ACC FREE FIRE VIP</b>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "📦 <b>Kho tài khoản hiện có:</b>\n"
        f"• <b>Acc Clone Lv 30:</b> <code>{stock_clone30} acc</code> <i>(Giá: 15 xu)</i>\n"
        f"• <b>Acc Clone Lv 5-8:</b> <code>{stock_clone58} acc</code> <i>(Giá: 10 xu)</i>\n\n"
        "📌 <i>Lưu ý: Người được mời phải join kênh thành công bạn mới nhận được xu.</i>\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        f"💰 <b>Số dư của bạn:</b> <code>{u_data['xu']} xu</code>\n"
        "🎁 <b>Cách kiếm xu:</b> Lấy link chia sẻ, người khác bấm vào và join kênh (1 Ref = 2 xu)"
    )
    keyboard = [
        [InlineKeyboardButton("💎 Đổi Clone Lv 30 (15 Xu)", callback_data="doi_clone30")],
        [InlineKeyboardButton("🔥 Đổi Clone Lv 5-8 (10 Xu)", callback_data="doi_clone58")],
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

    u_data = get_user(user_id)

    if data_callback == "doi_clone30":
        if stock_clone30 <= 0:
            await query.answer("❌ Kho Acc Clone Lv 30 đã hết hàng!", show_alert=True)
        elif u_data["xu"] < 15:
            await query.answer("❌ Bạn cần 15 xu để đổi Acc Clone Lv 30!", show_alert=True)
        else:
            add_user_xu(user_id, -15)
            stock_clone30 -= 1
            acc_info = random.choice(FAKE_ACCOUNTS_CLONE30)
            await query.answer("🎉 Đổi acc thành công!", show_alert=False)
            await context.bot.send_message(chat_id=user_id, text=f"✅ <b>GIAO DỊCH THÀNH CÔNG</b>\n\n{acc_info}", parse_mode="HTML")
            
    elif data_callback == "doi_clone58":
        if stock_clone58 <= 0:
            await query.answer("❌ Kho Acc Clone Lv 5-8 đã hết hàng!", show_alert=True)
        elif u_data["xu"] < 10:
            await query.answer("❌ Bạn cần 10 xu để đổi Acc Clone Lv 5-8!", show_alert=True)
        else:
            add_user_xu(user_id, -10)
            stock_clone58 -= 1
            acc_info = random.choice(FAKE_ACCOUNTS_CLONE58)
            await query.answer("🎉 Đổi acc thành công!", show_alert=False)
            await context.bot.send_message(chat_id=user_id, text=f"✅ <b>GIAO DỊCH THÀNH CÔNG</b>\n\n{acc_info}", parse_mode="HTML")
            
    elif data_callback == "kiem_xu":
        bot_username = context.bot.username
        ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        await query.answer("Link giới thiệu của bạn đã sẵn sàng!", show_alert=True)
        await context.bot.send_message(
            chat_id=user_id, 
            text=f"🔗 <b>Link giới thiệu của bạn:</b>\n<code>{ref_link}</code>\n\n<i>Hãy gửi link này cho bạn bè. Khi họ bấm vào và tham gia kênh, bạn sẽ tự động nhận được +2 xu!</i>",
            parse_mode="HTML"
        )

# --- LỆNH /addxu DẠNG NHANH MỘT DÒNG ---
async def admin_addxu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Bạn không có quyền sử dụng lệnh này.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("❌ Sai cú pháp!\n👉 Cách dùng: <code>/addxu [ID] [Số xu]</code>\nVí dụ: <code>/addxu 7907990385 50</code>", parse_mode="HTML")
        return

    try:
        target_id = int(args[0])
        amount = int(args[1])
        
        # Cộng xu vào DB
        add_user_xu(target_id, amount)
        
        await update.message.reply_text(f"✅ Đã thêm xu hoàn tất cho ID: <code>{target_id}</code> (+{amount} xu)", parse_mode="HTML")
        
        # Báo cho user được cộng xu biết
        try:
            await context.bot.send_message(chat_id=target_id, text=f"🎁 Bạn vừa được Admin cộng thêm <b>{amount} xu</b> vào tài khoản!", parse_mode="HTML")
        except Exception:
            pass

    except ValueError:
        await update.message.reply_text("❌ ID hoặc số xu phải là dạng số nguyên!")

# Đăng ký các Handler
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("addxu", admin_addxu))
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
    return "Bot is running via Webhook with SQLite DB!", 200

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=PORT)
