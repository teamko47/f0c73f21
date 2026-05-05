# Simple Telegram Bot

Telegram-бот на Python с использованием aiogram 3 и OpenAI.
Бот отвечает на вопросы по маркетплейсам OZON и Wildberries.

## Запуск

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Создайте `.env` по примеру:

```bash
cp .env.example .env
```

3. Укажите токены в `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

4. Запустите бота:

```bash
python main.py
```

## Команды

- `/start` - приветствие
- `/help` - список команд
- `Кнопка 1` - подсказка по карточке товара
- `Кнопка 2` - подсказка по продажам и продвижению
- Любой текст - AI-ответ по OZON и Wildberries

## Групповые чаты

Бота можно добавить в Telegram-чат. Он отвечает на текстовые сообщения, которые получает.
Если включен privacy mode у BotFather, Telegram может не передавать боту все сообщения группы.
Чтобы бот видел все вопросы в группе, отключите privacy mode через BotFather:

```text
/setprivacy
```
