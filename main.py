import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("8792438629:AAFA9k0QrLqEv1W4XQwf1XsuJ7hSRNNx71g")

dp = Dispatcher()


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_name = message.from_user.full_name if message.from_user else "друг"
    await message.answer(
        f"Привет, {html.bold(user_name)}!\n"
        "Я простой бот на aiogram. Напиши любое сообщение, и я отвечу."
    )


@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n"
        "/start - начать работу\n"
        "/help - помощь\n\n"
        "Любой другой текст я повторю в ответ."
    )


@dp.message(F.text)
async def echo_handler(message: Message) -> None:
    await message.answer(f"Вы написали: {html.quote(message.text)}")


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Add it to .env or environment variables.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
