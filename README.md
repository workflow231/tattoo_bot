# Tattoo Bot

Aiogram Telegram bot for appointment requests. This branch uses neutral
client/admin wording: categories and services are shown in the UI, while the
internal database models remain `Style` and `Sketch`.

## Runtime

- Bot mode: webhook by default in Docker Compose, polling fallback via `BOT_MODE=polling`.
- Database: SQLite via `DB_PATH`.
- FSM storage: Redis via `REDIS_URL`.
- Public webhook endpoint: Tailscale Funnel forwards HTTPS traffic to the bot.
- Client main menu and master main menu are separate.
- Master/admin access is controlled by `ADMIN_IDS`.
- Master contact text is read from `MASTER_CONTACT`.
- Service UI mode is controlled by `SIMPLE_BOT`.

## Main Flows

- Clients start from the `Запись` button.
- With `SIMPLE_BOT=false`, clients choose a category, then choose a service,
  open the service card, and create a request.
- With `SIMPLE_BOT=true`, clients choose a service directly. Categories are not
  shown to clients or admins.
- The client calendar is view-only: booking still starts from a selected
  service.
- The master can view appointments, manage the appointment calendar, and manage
  services.
- In full mode the master can manage categories and services. In simple mode the
  master manages only services; an internal category is used by the bot.
- The booking flow does not add a separate "contact master" step. The existing
  master contact button remains a separate support action.
- This UI mode does not change the database schema and does not require a
  migration.

## Docker Compose

1. Create a local `.env` from `.env.example` and set real values:

```env
BOT_TOKEN="your-telegram-bot-token"
BOT_MODE="webhook"
ADMIN_IDS="123456789"
MASTER_CONTACT="@master_username"
SIMPLE_BOT="false"
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

## Service UI Mode

`SIMPLE_BOT` switches how categories are shown in the bot UI:

- `SIMPLE_BOT=false`: full mode. The client flow is
  `Запись -> Категории -> Услуги -> карточка услуги -> заявка`. Admins can add,
  edit, and delete categories and services.
- `SIMPLE_BOT=true`: simple mode. The client flow is
  `Запись -> Услуги -> карточка услуги -> заявка`. Categories are hidden from
  clients and admins; admins add services directly.

This setting only affects UI and flow. It does not rename database tables, does
not rename internal `Style`/`Sketch` models, and does not require a migration.

## Client Texts

Client-facing text can be customized in `config/client_texts.json`. The file is
loaded by the bot on startup/use and already contains the default texts.

Supported keys:

- `welcome_new_user`
- `welcome_existing_user`
- `master_contact`
- `master_contact_missing`
- `appointment_created`
- `appointment_confirmed`
- `appointment_rejected`
- `reminder_tomorrow`
- `stale_session`

Allowed placeholders:

- `master_contact`: `{contact}`
- `appointment_confirmed`: `{appointment_date}`, `{appointment_time}`,
  `{sketch_name}`
- `reminder_tomorrow`: `{appointment_date}`, `{appointment_time}`,
  `{sketch_name}`

Limitations:

- Telegram messages are limited to 4096 characters.
- Empty, too long, missing, or invalid text values fall back to built-in defaults.
- Do not use unknown placeholders or positional placeholders such as `{}`.
- HTML/Markdown parse mode is not enabled for custom texts.
- Do not put tokens, passwords, webhook secrets, or Tailscale auth keys in this
  file.

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
