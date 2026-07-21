# Tattoo Bot

Aiogram Telegram bot for tattoo sketch requests.

## Runtime

- `main` is the Railway/webhook deployment branch and has no Tailscale/Funnel
  service or Tailscale env variables.
- `tailscale-funnel` keeps the alternative Docker Compose deployment with
  Tailscale/Funnel.
- Bot mode: webhook by default, polling fallback via `BOT_MODE=polling`.
- Database: SQLite via `DB_PATH`.
- FSM storage: Redis via `REDIS_URL`.
- Public webhook endpoint: an external HTTPS reverse proxy forwards traffic to the bot.
- Client main menu and master main menu are separate.
- Master/admin access is controlled by `ADMIN_IDS`.
- Master contact text is read from `MASTER_CONTACT`.
- Calendar dates and daily reminders use `BOT_TIMEZONE`; default fallback is
  `Europe/Moscow`.

## Main Flows

- Clients start from the `Запись` button and choose one of three request types:
  catalog sketch, custom sketch photo, or request without a sketch.
- `Выбрать эскиз` opens the existing sketch catalog flow.
- The sketch card has `Создать заявку`, `Чат с мастером`, `Назад`, and
  `Главное меню`; there is no separate `Оставить комментарий` button on the
  sketch card.
- For `Мой эскиз`, the bot accepts only a Telegram photo and attaches it to the
  appointment request. The master sees that photo next to the admin appointment
  card.
- Clients can view the master calendar, see their requests, contact the master,
  and open `Мои соцсети`.
- The client calendar is view-only: booking starts from the `Запись` menu.
- Appointment slots are treated as busy for both `pending` and `confirmed`
  appointments. `rejected` and `cancelled` appointments free the slot.
- The master can view appointments, manage the appointment calendar, configure
  working hours, and manage sketches.
- When adding a sketch, the master chooses or creates a style, fills sketch fields, reviews the summary, and saves it.

## Deployment

### Railway / main

Use the `main` branch for Railway deployment. Set the same env variables as in
`.env.example` in Railway variables. Railway provides the public HTTPS endpoint;
set `WEBHOOK_URL` to that public URL and keep `WEBHOOK_PATH` aligned with the
bot route.

The app starts with:

```bash
python -m bot.main
```

`bot.main` applies database migrations before starting polling or webhook mode.

### Docker Compose

For local Docker Compose or self-hosted webhook deployment, create a local `.env`
from `.env.example` and set real values:

```env
BOT_TOKEN="your-telegram-bot-token"
BOT_MODE="webhook"
ADMIN_IDS="123456789"
MASTER_CONTACT="@master_username"
BOT_TIMEZONE="Europe/Moscow"
WEBHOOK_URL="https://your-public-webhook-host.example.com"
WEBHOOK_PATH="/webhook"
WEBHOOK_SECRET_TOKEN="replace-with-random-webhook-secret"
```

Build and start:

```bash
docker compose build
docker compose up -d
```

In webhook mode the bot registers:

```text
WEBHOOK_URL + WEBHOOK_PATH
```

with Telegram and validates Telegram's webhook secret header using
`WEBHOOK_SECRET_TOKEN`. An external HTTPS reverse proxy should expose the same
public `WEBHOOK_URL` and forward requests to the bot service.

The `main` branch Docker Compose file contains only `bot` and `redis`. It does
not contain Tailscale/Funnel wiring. Use the `tailscale-funnel` branch when a
Tailscale Funnel container is required.

SQLite data is stored in the `tattoo_bot_data` Docker volume at
`/app/data/tattoo_bot.db`. Redis data is stored in the `redis_data` volume.
Treat the SQLite volume and backups as sensitive: appointment records can include
Telegram user IDs, usernames, comments, and Telegram `file_id` values for client
sketch photos.

`BOT_TIMEZONE` must be an IANA timezone name supported by Python `zoneinfo`,
for example `Europe/Moscow`. If the value is empty or invalid, the bot safely
falls back to `Europe/Moscow`. Calendar "today" checks and the daily reminder
job use this timezone. If the container has no system timezone database, the
last fallback is fixed UTC+3 for the default `Europe/Moscow` setting.

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
- `my_socials`
- `main_menu`
- `choose_action`
- `booking_menu_prompt`
- `custom_sketch_menu_prompt`
- `custom_sketch_photo_prompt`
- `custom_sketch_photo_required`
- `appointment_choose_date`
- `appointment_choose_available_day`
- `appointment_no_slots_for_date`
- `appointment_date_unavailable`
- `appointment_date_in_past`
- `appointment_temporary_day_off`
- `appointment_weekly_day_off`
- `appointment_choose_time`
- `appointment_choose_time_button`
- `appointment_comment_prompt`
- `appointment_cancelled`
- `appointment_create_missing_data`
- `appointment_create_failed`
- `appointment_missing_data`
- `appointment_sketch_missing`
- `appointment_sketch_unavailable`
- `appointment_summary`
- `appointment_card`
- `appointment_list_item`
- `appointment_back_to_sketch_card`
- `appointments_choose_from_list`
- `appointments_empty`
- `appointments_list`
- `appointment_not_found`
- `appointment_not_selected`
- `user_unknown`
- `appointment_user_cancelled`
- `appointment_cancel_confirmed_not_allowed`
- `appointment_cancel_unavailable`
- `catalog_empty`
- `catalog_empty_short`
- `catalog_choose_style_button`
- `catalog_style_empty`
- `catalog_choose_sketch_button`
- `catalog_sketch_unavailable`
- `catalog_return_failed`
- `catalog_open_failed`
- `catalog_choose_style_title`
- `catalog_choose_sketch_title`
- `catalog_page_title`
- `client_calendar_opened`
- `client_calendar_use_inline_buttons`
- `client_calendar_no_slots`
- `client_calendar_day_slots`
- `client_calendar_month`

Allowed placeholders:

- `master_contact`: `{contact}`
- `appointment_confirmed`: `{appointment_date}`, `{appointment_time}`,
  `{sketch_name}`
- `reminder_tomorrow`: `{appointment_date}`, `{appointment_time}`,
  `{sketch_name}`
- `appointment_choose_date`: `{month_title}`
- `appointment_summary`: `{sketch_name}`, `{appointment_date}`,
  `{appointment_time}`, `{comment}`
- `appointment_card`: `{appointment_id}`, `{sketch_name}`, `{appointment_date}`,
  `{appointment_time}`, `{status}`, `{comment}`
- `appointment_list_item`: `{appointment_id}`, `{appointment_date}`,
  `{appointment_time}`, `{status}`
- `appointments_list`: `{appointments}`
- `catalog_page_title`: `{title}`, `{page}`, `{pages}`
- `client_calendar_day_slots`: `{appointment_date}`, `{available_times}`
- `client_calendar_month`: `{month_title}`

Limitations:

- Telegram messages are limited to 4096 characters.
- Empty, too long, missing, or invalid text values fall back to built-in defaults.
- Default `my_socials` text is `Соц сети еще не добавленны`.
- Do not use unknown placeholders or positional placeholders such as `{}`.
- HTML/Markdown parse mode is not enabled for custom texts.
- Do not put tokens, passwords, webhook secrets, or deployment auth keys in this
  file.

## Useful Commands

```bash
docker compose config --no-interpolate
docker compose logs -f bot
docker compose run --rm bot alembic upgrade head
docker compose down
```

For local polling without webhook, set:

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

Do not commit real `.env` values, bot tokens, or webhook secrets.
