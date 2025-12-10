# JMIH CRM Bot

Телеграм-бот + backend для CRM-системы сети магазинов **ЖМЫХ / VapeXP**.

## Описание

Бот и web-сервис помогают:
- вести учёт клиентов,
- отслеживать заказы и обращения,
- автоматизировать коммуникацию между продавцами и администрацией.

## Стек

- Python 3.x
- FastAPI /
- Aiogram / Telebot
- PostgreSQL


## Запуск локально

```bash
git clone https://github.com/samsapotatarskiizxlebnogomira/jmih-crm-bot.git
cd jmih-crm-bot

python -m venv venv
source venv/bin/activate  # macOS / Linux
pip install -r requirements.txt

cp .env.example .env      
# отредактировать .env под свою БД / токены

# пример команды запуска
uvicorn app.main:app --host 0.0.0.0 --port 8000
