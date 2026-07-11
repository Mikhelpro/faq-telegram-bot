# Med Star Internal Medicine Clinic — FAQ Telegram Bot

A Telegram bot that auto-answers common patient questions using fuzzy text matching
against a database of FAQs you manage right from Telegram. Unmatched
questions get logged and (optionally) forwarded to admins.

## ⚠️ Before launch

`seed.py` still has one FAQ marked `[PLACEHOLDER]`:
- Insurance providers accepted

Edit that entry directly in `seed.py`, then redeploy. Phone number, services, and hours are already filled in.

## How it works

- Every incoming message is fuzzy-matched (via `rapidfuzz`) against stored
  FAQ questions and keywords.
- A match above the confidence threshold (default 65/100) gets answered
  instantly.
- No match → the question is logged to the `unanswered` table and, if
  `FORWARD_UNANSWERED=true`, sent to your admin DM so you can reply manually
  and later add it as a real FAQ.
- No AI API calls, no external cost — pure string matching. Good for a
  focused set of FAQs. If your FAQ list grows large or phrasing varies a
  lot, swap `utils/matcher.py` for an embeddings-based matcher (e.g. via the
  Gemini/OpenAI embeddings API) later.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`:
- `BOT_TOKEN` — from [@BotFather](https://t.me/BotFather)
- `ADMIN_IDS` — your numeric Telegram user id(s), comma-separated. Get yours
  from [@userinfobot](https://t.me/userinfobot)

Run it:

```bash
python main.py
```

`seed.py` runs automatically on every startup and inserts the baseline FAQs
if the table is empty — no separate step needed. Edit `SEED_FAQS` in that
file directly to change what ships by default.

## Using the bot

**Everyone:**
- `/start`, `/help` — intro, with buttons for location and channel
- `/faq` — browse all questions grouped by category
- `/location` — Google Maps link as a button
- `/channel` — Telegram channel link as a button
- Just type a question in plain language

**Admins only** (must be in `ADMIN_IDS`):
- `/admin` — show this command list in-chat
- `/addfaq question | answer | category | keyword1,keyword2` — category and
  keywords are optional
- `/editfaq id | new question | new answer` — leave a field blank to keep it
  unchanged
- `/delfaq id`
- `/listfaq` — all FAQs with IDs
- `/unanswered` — recent questions nobody had an answer for
- `/resolve id` — mark an unanswered entry as handled
- `/stats` — FAQ count, users seen, top questions by hits

Example:
```
/addfaq Do you have a pediatrician on staff? | Not currently — we focus on internal medicine, but we can refer you to a trusted pediatric clinic nearby. | services | pediatrician,children,kids
```

## Deploying to Render (free plan)

Render's **free plan only supports Web Services** (not Background Workers), and free Web Services **don't get a persistent disk** and **spin down after 15 minutes with no inbound HTTP traffic**. This bot is built around those constraints:

- `main.py` runs a tiny HTTP server (`/`) alongside the bot's Telegram polling, purely so Render's port scanner sees an open port and doesn't kill the service.
- Since there's no disk, the SQLite file is wiped on every restart/redeploy. To avoid losing your FAQs, `seed.py` re-inserts a baseline set of FAQs automatically on every startup **only if the table is empty** — so restarts don't duplicate data, but anything added later via `/addfaq` in Telegram will NOT survive a restart. Edit the FAQs in `seed.py` directly and redeploy for anything you want to keep permanently.
- To stop the free service from spinning down, use an uptime pinger (same pattern as your other bots) — e.g. **UptimeRobot** hitting your Render URL's `/` path every 5–10 minutes. Free web services spin down after 15 min of no inbound traffic, so anything more frequent than that keeps it alive.

**If you outgrow these limits** (want live `/addfaq` edits to persist, or want zero spin-down), the two options are:
1. Upgrade the service to a paid instance type ($7/mo Starter) — unlocks persistent disks and removes spin-down.
2. Migrate `database.py` from SQLite to Render's free Postgres instead of a disk-backed file — Postgres data isn't tied to the web service's ephemeral filesystem.

### Steps

1. Push this repo to GitHub.
2. In Render: **New → Blueprint** → point at the repo → it reads `render.yaml`.
3. Set `BOT_TOKEN` and `ADMIN_IDS` as env vars in the Render dashboard (marked `sync: false` so they're not committed to git).
4. Deploy. Once live, copy the service's `.onrender.com` URL.
5. Set up UptimeRobot (or similar) to ping that URL every 5–10 minutes to prevent spin-down.

## Extending it later

- **Bilingual (English/Amharic)**: store a `language` column on `faqs` and
  detect the user's language, similar to your electricity bill-splitting
  bot's approach.
- **AI fallback**: instead of just logging unanswered questions, pipe them
  through Gemini (like MikhelAssist) for a best-effort generated answer,
  clearly labeled as auto-generated, before falling back to a human.
- **Inline buttons**: use `/faq` results as inline keyboard buttons instead
  of a text list, so users tap instead of retype.
- **Multi-tenant**: if you want to reuse this same codebase for other clients
  clients, add a `bot_id`/`client_id` column and scope FAQs per client with
  one shared codebase.

## Project structure

```
faq_bot/
├── main.py              # entry point: healthcheck server + bot polling
├── config.py             # env var loading
├── database.py            # SQLite layer (faqs, unanswered, users)
├── seed.py                # baseline FAQs, auto-applied on every startup
├── handlers/
│   ├── user.py            # /start, /help, /faq, /location, /channel, catch-all question handler
│   └── admin.py           # /addfaq, /editfaq, /delfaq, /listfaq, /unanswered, /resolve, /stats
├── utils/
│   └── matcher.py          # rapidfuzz-based best-match logic
├── requirements.txt
├── .env.example
├── .python-version
└── render.yaml
```
