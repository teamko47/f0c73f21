# Simple Telegram Bot

Простой Telegram-бот на Python с использованием aiogram 3.

## Запуск

1. Установите зависимости:

```bash
pip install -r requirements.txt
```

2. Создайте `.env` по примеру:

```bash
cp .env.example .env
```

3. Укажите токен бота в `.env`:

```env
BOT_TOKEN=your_telegram_bot_token
```

4. Запустите бота:

```bash
python main.py
```

## Команды

- `/start` - приветствие
- `/help` - список команд
- Любой текст - бот повторит сообщение
