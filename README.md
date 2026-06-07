# Personal AI Finance Assistant

Personal AI Finance Assistant is a self-hosted Telegram bot for debt and payment tracking with a Django admin panel. It is intended for personal finance tracking, portfolio demonstration, and future extension into a more advanced finance assistant.

The bot accepts Russian natural-language finance messages, asks an LLM provider to convert them into strict JSON, creates a pending action, and writes to the database only after Telegram confirmation.

## Features

- Telegram bot powered by aiogram 3.
- Russian bot responses by default.
- Debt, credit card, loan, income, expense, and payment tracking.
- Safe pending-action confirmation flow with inline Telegram buttons.
- Django 5 admin panel with Django Unfold support.
- Admin analytics dashboard for active debt, monthly income/expenses/payments, upcoming payments, overdue payments, and debt distribution.
- OpenAI-compatible provider abstraction with OpenAI and OpenRouter implementations.
- OpenRouter free-model rotation by active model presets and priority.
- Docker Compose setup for local development and VPS deployment.
- Basic pytest coverage for finance models, action execution, LLM schemas, and Telegram access checks.

## Screenshots

Screenshots are intentionally left as placeholders until you run the project with your own data:

- Telegram confirmation flow
- Django Unfold finance admin
- Analytics dashboard

## Tech Stack

- Python 3.12+
- Django 5.x
- Django Unfold
- PostgreSQL
- Redis
- aiogram 3.x
- OpenAI SDK and httpx
- Pydantic
- Docker and Docker Compose
- pytest
- Ruff

## Local Setup With Docker Desktop

1. Copy the environment file:

```bash
cp .env.example .env
```

2. Edit `.env` and set:

```env
TELEGRAM_BOT_TOKEN=your-token
ALLOWED_TELEGRAM_USER_IDS=your-telegram-user-id
```

3. Build and start services:

```bash
docker compose up --build
```

4. Open the admin panel:

```text
http://localhost:8000/admin/
```

Default local admin credentials from `.env.example`:

```text
username: rexileer
password: 0528
```

The `web` service runs migrations and `python manage.py init_dev` automatically. You can also run them manually:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py init_dev
```

## Environment Variables

Important settings:

- `DEBUG`
- `SECRET_KEY`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL` or `DB_HOST`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_PORT`
- `REDIS_URL`
- `TELEGRAM_BOT_TOKEN`
- `ALLOWED_TELEGRAM_USER_IDS`
- `DJANGO_SUPERUSER_USERNAME`
- `DJANGO_SUPERUSER_PASSWORD`
- `DJANGO_SUPERUSER_EMAIL`
- `TIME_ZONE`
- `LANGUAGE_CODE`

The default timezone is `Europe/Moscow`. Change `TIME_ZONE` in `.env` if you need another timezone.

Never commit your real `.env`. API keys are stored plainly in the database for this self-hosted MVP, so keep server and admin access private.

## Telegram Bot Token

1. Open Telegram and message `@BotFather`.
2. Run `/newbot`.
3. Follow the prompts and copy the bot token.
4. Put the token into `.env` as `TELEGRAM_BOT_TOKEN`.

To get your Telegram user ID, message a user-info bot or inspect bot logs after sending a message. Add only your own ID to:

```env
ALLOWED_TELEGRAM_USER_IDS=123456789
```

Unauthorized users receive:

```text
Нет доступа к этому боту.
```

## LLM Provider Setup

Run `python manage.py init_dev` or `make init-dev` to create default provider and model preset records.

Then open Django admin:

1. Go to `LLM providers`.
2. Choose OpenAI or OpenRouter.
3. Paste the API key.
4. Go to `LLM model presets` and adjust model IDs.
5. Go to `LLM settings` and select the active provider and tier.

OpenAI has no free API models. Treat OpenAI cheap presets as almost-free or low-cost options and update model IDs in admin as model availability changes.

## Confirmation Flow

1. The user sends a Russian natural-language message.
2. The bot sends it to the active LLM provider with the current backend date.
3. The provider must return strict JSON matching the Pydantic schema.
4. The backend validates the JSON.
5. The backend creates a pending `BotAction`.
6. The bot shows a Russian summary and buttons:
   - `✅ Подтвердить`
   - `❌ Отменить`
7. Confirmation executes a known action handler inside a database transaction.
8. Rejection marks the action as rejected.

No free-form tool execution is supported.

## Example Messages

```text
Добавь долг по кредитке 185405, заплатить надо 12444 5 июня
Я оплатил 10000 по кредитке
Добавь доход 12000 за проект БОЗОН
Запиши расход 2500 на еду
Что мне нужно оплатить в ближайшие 7 дней?
Покажи все активные долги
Сколько я уже заплатил в этом месяце?
Добавь долг другу Ивану 5000, вернуть до 15 июня
```

## Development Commands

```bash
make build
make up
make down
make logs
make migrate
make createsuperuser
make init-dev
make test
make lint
make format
```

Without Docker:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd personal_ai_finance_assistant
python manage.py migrate
python manage.py init_dev
python manage.py runserver
```

## Roadmap

See [docs/ROADMAP.md](docs/ROADMAP.md).

## Security Notes

- This MVP is designed for one trusted self-hosted user.
- Restrict Telegram access with `ALLOWED_TELEGRAM_USER_IDS`.
- Do not commit `.env`.
- Do not expose Django admin publicly without HTTPS and strong credentials.
- API keys are stored plainly in admin by design for this MVP.
- The application avoids logging API keys.

## License

License placeholder: see [LICENSE](LICENSE).
