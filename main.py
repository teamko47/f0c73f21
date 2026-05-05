import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher, F, html
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

dp = Dispatcher()

start_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Кнопка 1", callback_data="button_1"),
            InlineKeyboardButton(text="Кнопка 2", callback_data="button_2"),
        ]
    ]
)


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    user_name = message.from_user.full_name if message.from_user else "друг"
    await message.answer(
        f"Привет, {html.bold(user_name)}!\n"
        "Я простой бот на aiogram. Выбери кнопку или напиши любое сообщение.",
        reply_markup=start_keyboard,
    )


@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n"
        "/start - начать работу\n"
        "/help - помощь\n\n"
        "Кнопка 1 и Кнопка 2 отправляют отдельный текст.\n"
        "Любой другой текст я повторю в ответ."
    )


@dp.callback_query(F.data == "button_1")
async def button_1_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer("Вы нажали кнопку 1. Это первый текст.")


@dp.callback_query(F.data == "button_2")
async def button_2_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer("Вы нажали кнопку 2. Это второй текст.")


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
