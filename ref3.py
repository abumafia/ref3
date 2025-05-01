import json
import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ChatMemberStatus
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import CommandStart, Command
from aiogram.utils.markdown import hbold
from aiogram.client.default import DefaultBotProperties
from fastapi import FastAPI, Request
from aiogram.webhook.aiohttp_server import SimpleRequestHandler

from starlette.responses import Response
import uvicorn

API_TOKEN = "7624885474:AAHj1FolBwjGBN3xLlSf7JECxoLLAyChRYk"
ADMIN_ID = 6606638731

app = FastAPI()

@app.get("/")
async def home():
    return {"message": "Bot ishlayapti!"}

@app.post("/webhook")
async def webhook(req: Request):
    return await dp.feed_webhook_update(bot=bot, update=await req.json())

CHANNELS = [
    {"id": "@Yaqinlarimga_tabriklar02", "name": "Yaqinlarimga tabriklarim guruhi"},
    {"id": "@yashil_hayot74", "name": "Green Leaf guruhi"},
    {"id" : "@hallaym", "name": "HALLAYM Kanali"}
]

# === Bot init ===
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# === Database ===
def load_data():
    try:
        with open("database.json", "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open("database.json", "w") as f:
        json.dump(data, f, indent=2)

async def add_user(user_id, name, referrer=None):
    data = load_data()
    user_id_str = str(user_id)

    if user_id_str not in data:
        data[user_id_str] = {
            "name": name,
            "referrer": referrer,
            "invited": [],
            "points": 0
        }

        if referrer and str(referrer) in data:
            # Referrerga point qo‘shiladi va invited listga qo‘shiladi
            data[str(referrer)]["invited"].append(user_id)
            data[str(referrer)]["points"] += 1
            invited_count = data[str(referrer)]["points"]
            referrer_name = data[str(referrer)]["name"]

            # Referrerga xabar yuborish
            msg = f"🎉 Siz orqali {name} botga qo‘shildi! Sizga 1 ball berildi.\n"
            if invited_count < 10:
                msg += f"Yana {10 - invited_count} ta referal qilsangiz, turnirda qatnasha olasiz."
            else:
                msg += "✅ Siz endilikda Yaqinlarimga Tabriklarim ijtimoiy loyihasi ijodkorlari tomonidan rejalashtirilgan turnirlarda qatnasha olasiz!"
            try:
                await bot.send_message(referrer, msg)
            except:
                pass

            # Referalga ham referrer haqida bildirish
            try:
                await bot.send_message(
                    user_id,
                    f"""👋 Siz {referrer_name} havolasi orqali botga qo‘shildingiz.

Endi siz ham Turnirlarda qatnashib bepul sov'g'alarni qo'lga kirita olasiz:
1-shart: Eng ko'p taklif qiluvchiga 1ta Audio tabrik
2-shart: Eng ko'p Guruhimizga A'zolar qo'shganga 1ta Audio tabrik
3-shart: Random orqali tasodifiy ishtirokchiga 1ta Audio tabrik!

Diqqat qiling, Turnirlar har mavsum o'tkazilishi mumkin!!!
"""
                )
            except:
                pass

        save_data(data)

# === UI ===
def subscription_keyboard():
    buttons = [[InlineKeyboardButton(text=f"➕ {ch['name']}", url=f"https://t.me/{ch['id'].lstrip('@')}")] for ch in CHANNELS]
    buttons.append([InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="verify")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def main_menu():
    return ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [KeyboardButton(text="🏱 Referallarim")],
        [KeyboardButton(text="📊 Turnir reytingi")]
    ])

# === Subscription check ===
async def check_subscriptions(user_id: int) -> bool:
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                return False
        except:
            return False
    return True

# === Handlers ===
@dp.message(CommandStart())
async def start_handler(msg: Message, command: CommandStart):
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    ref = command.args
    user_id = msg.from_user.id
    name = msg.from_user.full_name

    if not await check_subscriptions(user_id):
        await msg.answer("⛔ Botdan foydalanish uchun quyidagi kanallarga obuna bo‘ling:", reply_markup=subscription_keyboard())
        return

    await add_user(user_id, name, referrer=int(ref) if ref and ref.isdigit() else None)

    referral_link = f"https://t.me/{bot_username}?start={user_id}"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📤 Do‘stlarga ulashish",
                url=f"https://t.me/share/url?url={referral_link}&text=👋 Salom! Mana men foydalanyotgan eng yaxshi konkurs bot, siz bu bot orqali yaqinlaringizni qalbiga quvonch ulasha olasiz:"
            )
        ]
    ])

    await msg.answer(
        f"""👋 Salom, {name}!

🥰 YAQINLARINGIZNI TABRIKLANG

Assalomu alaykum mehrli inson! 
Sizda ajoyib imkoniyat bor. 

@SAMIMIY_DILNOMALAR kanalimizga 10 ta do‘stingizni taklif qiling 
va ZULFIZAR QORYOGʻDIYEVA dan mehrli dil izhorlarini qoʻlga kiriting.

Quyidagi tugmani bosib referal havolangizni do‘stlarga ulashing:

🔗 {referral_link}
""",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "verify")
async def verify_subscription(call: CallbackQuery):
    user_id = call.from_user.id
    not_joined = []
    for ch in CHANNELS:
        try:
            member = await bot.get_chat_member(ch["id"], user_id)
            if member.status not in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                not_joined.append(ch["name"])
        except:
            not_joined.append(ch["name"])
    if not not_joined:
        await call.message.edit_text("✅ Obunalar tasdiqlandi! Asosiy menu ochildi.")
        await call.message.answer("Menu:", reply_markup=main_menu())
    else:
        await call.answer("🚫 Siz quyidagi kanallarga hali obuna bo‘lmagansiz:\n" + "\n".join(not_joined), show_alert=True)

@dp.message(F.text == "🏱 Referallarim")
async def my_referrals(msg: Message):
    data = load_data()
    user = data.get(str(msg.from_user.id))
    if user:
        invited_names = [data.get(str(uid), {}).get("name", "Noma’lum") for uid in user["invited"]]
        invited_list = "\n".join(invited_names) if invited_names else "—"
        await msg.answer(f"🧮 Sizning ballaringiz: {user['points']}\n👥 Taklif qilgan do‘stlaringiz:\n{invited_list}")
    else:
        await msg.answer("Sizning ma'lumotlaringiz topilmadi.")

@dp.message(F.text == "📊 Turnir reytingi")
async def show_ranking(msg: Message):
    data = load_data()
    sorted_users = sorted(data.items(), key=lambda x: x[1]["points"], reverse=True)
    text = "🏆 Turnir reytingi:\n\n"
    for i, (uid, info) in enumerate(sorted_users[:10], 1):
        text += f"{i}. {info['name']} – {info['points']} ball\n"
    await msg.answer(text)

@dp.message(Command("reset"))
async def reset_cmd(msg: Message):
    if msg.from_user.id == ADMIN_ID:
        reset_all_points()
        await msg.answer("🔄 Turnir ballari nolga tushirildi.")
    else:
        await msg.answer("⛔ Siz admin emassiz!")

@dp.message(Command("broadcast"))
async def broadcast_cmd(msg: Message):
    if msg.from_user.id != ADMIN_ID:
        return
    parts = msg.text.split(" ", 1)
    if len(parts) < 2:
        await msg.answer("❗ E'lon yuborish: /broadcast Matn")
        return
    text = parts[1]
    data = load_data()
    sent = 0
    for uid in data:
        try:
            await bot.send_message(uid, f"📢 {text}")
            sent += 1
        except:
            continue
    await msg.answer(f"✅ {sent} ta foydalanuvchiga yuborildi.")

# === Run bot ===
async def main():
    webhook_url = "https://ref3-xlii.onrender.com/webhook"  # bu render domeningiz
    await bot.set_webhook(webhook_url)
    await dp.start_webhook(
        webhook_path="/webhook",
        on_startup=None,
        on_shutdown=None,
        bot=bot
    )
