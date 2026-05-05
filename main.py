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
MARKETPLACE_WEB_SEARCH_ENABLED = os.getenv(
    "MARKETPLACE_WEB_SEARCH_ENABLED",
    os.getenv("OZON_WEB_SEARCH_ENABLED", "true"),
).lower() == "true"
MARKETPLACE_KNOWLEDGE_DOMAINS = [
    "seller-edu.ozon.ru",
    "docs.ozon.com",
    "seller.wildberries.ru",
]

MARKETPLACE_ASSISTANT_PROMPT = """
Ты экспертный Telegram-консультант по маркетплейсам OZON и Wildberries.
Отвечай на русском языке живо, дружелюбно и по-человечески, как опытный коллега в чате.
Не звучи как сухая инструкция или робот. Можно коротко поддержать собеседника, но без лишней воды.

Помогай по темам:
- создание и оптимизация карточек товаров;
- SEO, ключевые слова, названия, описания и характеристики;
- цены, скидки, акции, юнит-экономика и маржинальность;
- FBO/FBS/realFBS, поставки, остатки, логистика и возвраты;
- реклама, продвижение, аналитика и отчеты;
- типовые ошибки селлеров и план действий.

На обычные разговорные сообщения тоже отвечай нормально: здоровайся, поддерживай беседу,
уточняй, чем помочь, и мягко возвращай разговор к OZON/Wildberries, если это уместно.
Если человек пишет неформально, отвечай в таком же спокойном человеческом стиле.

По вопросам OZON используй официальную базу знаний и документацию:
- seller-edu.ozon.ru;
- docs.ozon.com.

По вопросам Wildberries используй официальный справочный центр продавцов:
- seller.wildberries.ru/instructions.

Сначала опирайся на найденные официальные источники OZON или Wildberries, затем давай практический вывод.
Если в официальных источниках нет точного ответа, прямо скажи об этом и предложи, где проверить
в личном кабинете продавца или официальной справке маркетплейса.

Если вопрос не про OZON, Wildberries, e-commerce или продажи на маркетплейсах,
не отмахивайся сразу. Если это обычная беседа, ответь по-человечески.
Если просят экспертный ответ вне твоей темы, кратко скажи, что лучше всего помогаешь по OZON и WB.
Если для точного ответа не хватает данных, задай 1-3 уточняющих вопроса.
Не выдумывай актуальные тарифы, правила и даты; если данные могут измениться,
посоветуй сверить их в личном кабинете маркетплейса или официальной справке.
Когда используешь официальные страницы OZON или Wildberries, в конце добавляй блок "Источники" с URL.
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

    if not await should_answer_message(message, bot):
        return

    question = message.text.strip()
    if not question:
        return

    await bot.send_chat_action(chat_id=message.chat.id, action="typing")

    try:
        response, _used_web_search = await ask_openai(question)
    except OpenAIError as error:
        logging.exception("OpenAI API request failed: %s", error)
        await message.answer("Не удалось получить ответ от OpenAI. Попробуйте еще раз чуть позже.")
        return

    answer = response.output_text.strip()
    if not answer:
        answer = "OpenAI вернул пустой ответ. Попробуйте переформулировать вопрос."

    citations = collect_url_citations(response)
    if citations and "Источники" not in answer:
        answer = f"{answer}\n\nИсточники:\n" + "\n".join(f"- {url}" for url in citations[:5])

    for chunk in split_telegram_message(answer):
        await message.answer(chunk, parse_mode=None)


async def should_answer_message(message: Message, bot: Bot) -> bool:
    if message.chat.type == "private":
        return True

    bot_user = await bot.get_me()
    text = message.text or ""
    text_lower = text.lower()
    mention = f"@{bot_user.username.lower()}" if bot_user.username else ""

    if mention and mention in text_lower:
        return True

    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user.id == bot_user.id

    bot_names = [bot_user.first_name]
    if bot_user.username:
        bot_names.append(bot_user.username)

    return any(name and name.lower() in text_lower for name in bot_names)


async def ask_openai(question: str):
    request = build_openai_request(question)

    if not MARKETPLACE_WEB_SEARCH_ENABLED:
        return await openai_client.responses.create(**request), False

    web_request = {
        **request,
        "tools": [
            {
                "type": "web_search",
                "filters": {"allowed_domains": MARKETPLACE_KNOWLEDGE_DOMAINS},
            }
        ],
        "tool_choice": "auto",
    }

    try:
        return await openai_client.responses.create(**web_request), True
    except OpenAIError as error:
        logging.exception("OpenAI web search request failed, retrying without web search: %s", error)
        return await openai_client.responses.create(**request), False


def build_openai_request(question: str) -> dict:
    return {
        "model": OPENAI_MODEL,
        "instructions": MARKETPLACE_ASSISTANT_PROMPT,
        "input": (
            "Ответь на вопрос продавца маркетплейса. "
            "Для вопросов по OZON и Wildberries используй официальные источники из разрешённых доменов.\n\n"
            f"Вопрос: {question}"
        ),
        "max_output_tokens": 1200,
    }


def collect_url_citations(response) -> list[str]:
    urls = []
    for output_item in getattr(response, "output", []) or []:
        for content_item in getattr(output_item, "content", []) or []:
            for annotation in getattr(content_item, "annotations", []) or []:
                url = getattr(annotation, "url", None)
                if url and url not in urls:
                    urls.append(url)
    return urls


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
