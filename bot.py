import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import WebAppInfo, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
import asyncio

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEBAPP_URL = os.getenv("WEBAPP_URL", "https://your-domain.com") # URL где будет хоститься фронтенд

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start"))
async def start(message: types.Message):
    # Кнопка для запуска Mini App
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🏰 Управлять городом", 
            web_app=WebAppInfo(url=WEBAPP_URL)
        )]
    ])
    
    await message.answer(
        f"Привет, Мэр {message.from_user.first_name}! 🏰\n\n"
        "Твой город ждет тебя. Строй фермы, добывай золото и расширяй границы на мировой карте.\n\n"
        "Готов основать величайшее королевство?",
        reply_markup=kb
    )

async def main():
    print("Бот CityState запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
