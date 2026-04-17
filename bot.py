import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import asyncio

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com") 

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    # Премиальное приветствие
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏰 Войти в Королевство", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])
    
    welcome_text = (
        f"Приветствую, милорд *{message.from_user.first_name}*! 👑\n\n"
        "Ваш народ ждет своего правителя. Впереди вас ждут великие дела:\n\n"
        "🌾 Стройте фермы и добывайте ресурсы\n"
        "⚒️ Укрепляйте экономику\n"
        "⚔️ Готовьтесь к завоеваниям\n\n"
        "Готовы ли вы вписать свое имя в историю?"
    )
    
    await message.answer(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=kb
    )

async def main():
    print("Bot CityState is running...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
