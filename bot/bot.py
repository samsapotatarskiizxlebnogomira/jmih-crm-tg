import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from aiogram.filters import Command
import asyncio

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBAPP_URL = os.getenv("WEBAPP_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def webapp_kb() -> InlineKeyboardMarkup:
    # ЧИСТАЯ inline-кнопка с WebApp, без обычных ссылок
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Открыть CRM",
                    web_app=WebAppInfo(url=WEBAPP_URL),
                )
            ]
        ]
    )


@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "привет! это мини-CRM для ЖМЫХ.\nнажми кнопку ниже, чтобы открыть мини-приложение.",
        reply_markup=webapp_kb(),
    )


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())