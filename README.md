# Tattoo Bot

Aiogram Telegram bot for tattoo sketch requests.

## Runtime

- Bot mode: webhook by default in Docker Compose, polling fallback via `BOT_MODE=polling`.
- Database: SQLite via `DB_PATH`.
- FSM storage: Redis via `REDIS_URL`.
- Public webhook endpoint: Tailscale Funnel forwards HTTPS traffic to the bot.
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
BOT_MODE="webhook"
ADMIN_IDS="123456789"
MASTER_CONTACT="@master_username"
WEBHOOK_URL="https://your-tailnet-host.your-tailnet.ts.net"
WEBHOOK_PATH="/webhook"
WEBHOOK_SECRET_TOKEN="replace-with-random-webhook-secret"
TS_AUTHKEY="replace-with-ephemeral-tailscale-auth-key"
TAILSCALE_HOSTNAME="tattoo-bot"
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

In webhook mode the bot registers:

```text
WEBHOOK_URL + WEBHOOK_PATH
```

with Telegram and validates Telegram's webhook secret header using
`WEBHOOK_SECRET_TOKEN`. Tailscale Funnel should expose the same public
`WEBHOOK_URL`.

Use an ephemeral, ACL-scoped Tailscale auth key for `TS_AUTHKEY`. Rotate the key
after first deployment or whenever it may have been exposed in local shell,
Docker Desktop, or compose logs.

SQLite data is stored in the `tattoo_bot_data` Docker volume at
`/app/data/tattoo_bot.db`. Redis data is stored in the `redis_data` volume.
Tailscale state is stored in the `tailscale_state` volume.

## Useful Commands

```bash
docker compose config --no-interpolate
docker compose logs -f bot
docker compose logs -f tailscale
docker compose run --rm bot alembic upgrade head
docker compose down
```

For local polling without webhook/Funnel, set:

```env
BOT_MODE="polling"
REDIS_URL="redis://localhost:6379/0"
```

## Tests

```bash
pytest
ruff check .
black --check .
pre-commit run -a
```

Do not commit real `.env` values, bot tokens, webhook secrets, or Tailscale auth keys.
