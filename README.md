# Tattoo Bot

Aiogram Telegram bot for tattoo sketch requests.

## Runtime

- Bot mode: polling.
- Database: SQLite via `DB_PATH`.
- FSM storage: Redis via `REDIS_URL`.
- Client main menu and master main menu are separate.
- Master/admin access is controlled by `ADMIN_IDS`.
- Master contact text is read from `MASTER_CONTACT`.

## Main Flows

- Clients can browse sketches, view the master calendar, create requests from a sketch card, see their requests, and contact the master.
- The client calendar is view-only: booking still starts from a selected sketch.
- The master can view appointments, manage the appointment calendar, and add new sketches.
- When adding a sketch, the master chooses or creates a style, fills sketch fields, reviews the summary, and saves it.

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
