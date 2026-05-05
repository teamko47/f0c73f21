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
from openai import AsyncOpenAI, OpenAIError


load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MARKETPLACE_ASSISTANT_PROMPT = """
Ты экспертный Telegram-консультант по маркетплейсам OZON и Wildberries.
Отвечай на русском языке, коротко и по делу.

Помогай по темам:
- создание и оптимизация карточек товаров;
- SEO, ключевые слова, названия, описания и характеристики;
- цены, скидки, акции, юнит-экономика и маржинальность;
- FBO/FBS/realFBS, поставки, остатки, логистика и возвраты;
- реклама, продвижение, аналитика и отчеты;
- типовые ошибки селлеров и план действий.

Если вопрос не про OZON, Wildberries, e-commerce или продажи на маркетплейсах,
вежливо скажи, что специализируешься на OZON и WB, и предложи переформулировать вопрос.
Если для точного ответа не хватает данных, задай 1-3 уточняющих вопроса.
Не выдумывай актуальные тарифы, правила и даты; если данные могут измениться,
посоветуй сверить их в личном кабинете маркетплейса или официальной справке.
"""

dp = Dispatcher()
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

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
        "Я отвечаю на вопросы по OZON и Wildberries. Выбери кнопку или задай вопрос.",
        reply_markup=start_keyboard,
    )


@dp.message(Command("help"))
async def command_help_handler(message: Message) -> None:
    await message.answer(
        "Доступные команды:\n"
        "/start - начать работу\n"
        "/help - помощь\n\n"
        "Кнопка 1 и Кнопка 2 отправляют отдельный текст.\n"
        "Любой другой вопрос я передам AI-консультанту по OZON и WB."
    )


@dp.callback_query(F.data == "button_1")
async def button_1_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Кнопка 1: могу помочь улучшить карточку товара для OZON или WB. "
            "Пришлите название товара, категорию и текущее описание."
        )


@dp.callback_query(F.data == "button_2")
async def button_2_handler(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "Кнопка 2: могу разобрать продажи и продвижение. "
            "Пришлите нишу, цену, себестоимость, комиссию и текущие показатели."
        )


@dp.message(F.text)
async def marketplace_question_handler(message: Message, bot: Bot) -> None:
    if not openai_client:
        await message.answer("OPENAI_API_KEY is not set. Add it to .env or hosting environment variables.")
        return

    question = message.text.strip()
    if not question:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        response = await openai_client.responses.create(
            model=OPENAI_MODEL,
            instructions=MARKETPLACE_ASSISTANT_PROMPT,
            input=question,
            max_output_tokens=900,
        )
    except OpenAIError as error:
        logging.exception("OpenAI API request failed: %s", error)
        await message.answer("Не удалось получить ответ от OpenAI. Попробуйте еще раз чуть позже.")
        return

    answer = response.output_text.strip()
    if not answer:
        answer = "OpenAI вернул пустой ответ. Попробуйте переформулировать вопрос."

    for chunk in split_telegram_message(answer):
        await message.answer(chunk, parse_mode=None)


def split_telegram_message(text: str, limit: int = 4000) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks = []
    current = ""
    for paragraph in text.split("\n"):
        if len(current) + len(paragraph) + 1 <= limit:
            current = f"{current}\n{paragraph}".strip()
            continue

        if current:
            chunks.append(current)
            current = ""

        while len(paragraph) > limit:
            chunks.append(paragraph[:limit])
            paragraph = paragraph[limit:]

        current = paragraph

    if current:
        chunks.append(current)

    return chunks


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is not set. Add it to .env or environment variables.")
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to .env or environment variables.")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
