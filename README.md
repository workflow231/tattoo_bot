# Tattoo Bot

Aiogram Telegram bot for tattoo sketch requests.

## Runtime

- Bot mode: polling.
- Database: SQLite via `DB_PATH`.
- FSM storage: Redis via `REDIS_URL`.

## Docker Compose

1. Create a local `.env` from `.env.example` and set real values:

```env
BOT_TOKEN="your-telegram-bot-token"
ADMIN_IDS="123456789"
MASTER_CONTACT="@master_username"
```

2. Build and start:

```bash
docker compose build
docker compose up -d
```

On startup the bot service runs:

```bash
alembic upgrade head
python -m bot.main
```

SQLite data is stored in the `tattoo_bot_data` Docker volume at
`/app/data/tattoo_bot.db`. Redis data is stored in the `redis_data` volume.

## Useful Commands

```bash
docker compose logs -f bot
docker compose run --rm bot alembic upgrade head
docker compose down
```

Do not commit real `.env` values or bot tokens.
