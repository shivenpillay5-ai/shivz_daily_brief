# Daily Brief Agent

This is a small learning project that builds a daily email brief with:

- Midrand hourly weather for the next few hours
- weather snapshots for Johannesburg, Cape Town, and Durban
- a market pulse with USD/ZAR, GBP/ZAR, gold, silver, and Brent crude
- a short morning summary written from the day's signals
- top 5 world news links
- top 5 AI and tech story links
- an approved WhatsApp template version of the daily brief
- a separate Daily Motivation and Bible Verse email
- a private couple brief with calendar nudges, a dish photo, a short recipe, and a weekly marriage spark

The project is intentionally split into simple modules so you can learn how a practical agent is built:

1. Collect raw context from APIs and RSS feeds.
2. Pass the candidate stories through a ranking prompt.
3. Write a concise morning summary from the selected facts.
4. Render the answer into text and HTML.
5. Send it by email.
6. Schedule it to run daily at 07:00.
7. Build a separate devotional email from a scripture prompt.
8. Build a private couple email for you and your spouse.
9. Alert you if the scheduled run fails after retries.

## Project Map

```text
daily-brief-agent/
  src/daily_brief/
    agent.py       # coordinates the daily brief workflow
    config.py      # reads .env settings
    main.py        # command-line entry point
    models.py      # shared data shapes
    http_client.py # small HTTP helper
    skills/
      SKILL.md     # explains the single Shivz Daily Brief skill
    tools/
      weather.py   # calls Open-Meteo
      market.py    # fetches FX and commodity market data
      news.py      # reads RSS/Atom feeds
      ranking.py   # prompt-based ranking, with fallback ranking
      summary.py   # prompt-based morning summary, with fallback summary
      devotional.py # scripture rotation and devotional reflection
      couple.py    # private couple brief content rotation
      google_calendar.py # read-only Google Calendar OAuth and event fetching
      rendering.py # email text and HTML
      devotional_rendering.py # devotional text, HTML, and WhatsApp rendering
      couple_rendering.py # couple brief text and HTML rendering
      email.py     # SMTP sending
      alerts.py    # failure alert email
      whatsapp.py  # WhatsApp Cloud API sending
    prompts/
      ranking_prompt.py   # model instructions for selecting stories
      summary_prompt.py   # model instructions for the morning summary
      devotional_prompt.py # model instructions for the devotional reflection
  scripts/
    run_daily_brief.ps1
    register_windows_task.ps1
  tests/
```

## Setup

From this folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

Copy the example config:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`.

For Gmail, use an app password, not your normal account password.

## First Run

Preview the brief without sending email:

```powershell
daily-brief
```

Preview the designed HTML email in your browser:

```powershell
daily-brief --no-openai --save-html preview.html
```

Send the email:

```powershell
daily-brief --send
```

Send the WhatsApp version:

```powershell
daily-brief --send-whatsapp --no-openai
```

Send the approved WhatsApp template notification:

```powershell
daily-brief --send-whatsapp-template
```

That sends the approved `shivz_daily_brief_v1` template with four body values:
date, weather, world headlines, and AI/tech headlines.

Force the non-OpenAI fallback ranking:

```powershell
daily-brief --no-openai
```

Preview the Daily Motivation and Bible Verse email:

```powershell
daily-brief --devotional
```

Preview the devotional HTML:

```powershell
daily-brief --devotional --save-html devotional-preview.html
```

Send the devotional email:

```powershell
daily-brief --devotional --send
```

Preview the private couple brief:

```powershell
daily-brief --couple
```

Preview the couple HTML:

```powershell
daily-brief --couple --save-html couple-preview.html
```

Send the couple email:

```powershell
daily-brief --couple --send
```

`--couple --send` uses `COUPLE_EMAIL_TO`, not `EMAIL_TO`, so the private note does not accidentally go to the wider family list.

## Google Calendar Setup For The Couple Brief

The Google Calendar integration is read-only. It uses Google's Calendar API Python OAuth pattern with the `https://www.googleapis.com/auth/calendar.readonly` scope.

1. In Google Calendar, share any calendars you want included with the Google account that will run this app.
2. In Google Cloud Console, enable the Google Calendar API for a project.
3. Configure the OAuth consent screen for testing.
4. Create an OAuth Client ID with application type `Desktop app`.
5. Download the client JSON file and save it in this project as `credentials.json`.
6. Install or refresh dependencies:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

7. Set these values in `.env`:

```text
GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=token.json
GOOGLE_CALENDAR_IDS=primary|Shiven;your-wife-calendar-id@gmail.com|Nolene
GOOGLE_CALENDAR_LOOKAHEAD_DAYS=3
GOOGLE_CALENDAR_MAX_EVENTS_PER_CALENDAR=12
```

8. Run the one-time auth command:

```powershell
.\.venv\Scripts\daily-brief.exe --google-calendar-auth
```

That opens a browser login and saves `token.json`. After that:

```powershell
.\.venv\Scripts\daily-brief.exe --couple --save-html couple-preview.html
```

The couple brief will show a calendar snapshot above the nudges. Both `credentials.json` and `token.json` are ignored by git.

## Scheduling At 07:00

The scheduled task is the alarm clock. The agent is the Python workflow it wakes up.

First test that email sending works:

```powershell
daily-brief --send --no-openai
```

Then register the 07:00 task:

```powershell
.\scripts\register_windows_task.ps1
```

That registers a Windows Scheduled Task named `DailyBriefAgent` to run every day at 07:00.
Each scheduled run writes a log file into `logs/`.

## GitHub Actions Scheduling

The GitHub workflows run from GitHub's cloud runners. That means your local machine does not need to be on.

The news brief workflow in `.github/workflows/daily-brief.yml` starts at 07:00 Africa/Johannesburg time.
The devotional workflow in `.github/workflows/daily-devotional.yml` starts at 07:10 Africa/Johannesburg time.
The Team ShiNola workflow in `.github/workflows/daily-couple-brief.yml` starts at 09:00 Africa/Johannesburg time.
The cron values in those files are written in UTC: `05:00`, `05:10`, and `07:00`, because South Africa is UTC+2.

The Team ShiNola workflow needs these repository secrets:

```text
COUPLE_EMAIL_TO
GOOGLE_CALENDAR_CREDENTIALS_JSON_B64
GOOGLE_CALENDAR_TOKEN_JSON_B64
```

Create the two Google Calendar secret values from the local OAuth files:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("credentials.json")) | Set-Clipboard
```

Save the clipboard value as `GOOGLE_CALENDAR_CREDENTIALS_JSON_B64`, then run:

```powershell
[Convert]::ToBase64String([IO.File]::ReadAllBytes("token.json")) | Set-Clipboard
```

Save that clipboard value as `GOOGLE_CALENDAR_TOKEN_JSON_B64`.

If sending fails, each workflow retries inside the same run:

- attempt 1 at the scheduled time
- attempt 2 after a 15 minute wait
- attempt 3 after another 15 minute wait

If all three attempts fail, the app sends a failure alert email using the same SMTP settings. The alert includes a link to the failed GitHub Actions run and the latest captured log output.

To send the WhatsApp template from GitHub Actions, add these repository secrets too:

```text
WHATSAPP_ENABLED
WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_BUSINESS_ACCOUNT_ID
WHATSAPP_ACCESS_TOKEN
WHATSAPP_TO
```

Use a Meta System User access token for `WHATSAPP_ACCESS_TOKEN` in GitHub Actions.
The temporary token from the WhatsApp API setup screen is useful for testing, but it can expire and is not a good daily scheduler token.

The workflow uses `WHATSAPP_TEMPLATE_NAME=shivz_daily_brief_v1` and `WHATSAPP_TEMPLATE_LANGUAGE=en`.

## How The Prompt Fits In

`src/daily_brief/agent.py` coordinates the workflow: fetch weather, fetch news, rank stories, render the email, and send it.

`src/daily_brief/skills/SKILL.md` contains the single skill definition for the project. It explains what the `Shivz Daily Brief` skill does, when the agent should use it, and which tools it relies on.

`src/daily_brief/tools/` contains the executable Python modules that the agent calls. This keeps the distinction clear:

- `skills/SKILL.md` is the instruction/capability description.
- `tools/*.py` is the runnable implementation.

`src/daily_brief/prompts/ranking_prompt.py` contains the core model instruction. The program gives the model candidate stories that already include titles, links, sources, and summaries. The prompt tells the model to pick exactly the best 5 without inventing URLs.

`src/daily_brief/prompts/summary_prompt.py` contains the morning-summary instruction. It gives the model the selected weather, market, world, and AI/tech facts and asks for a short reader-friendly summary without inventing details.

`src/daily_brief/prompts/devotional_prompt.py` contains the devotional instruction. It gives the model one public-domain KJV verse and asks for a short practical reflection plus a broader motivational closing. If no OpenAI key is configured, the app uses the curated fallback reflection and motivational closing.

The couple brief rotates meal ideas and short recipes daily, keeps one marriage spark for the week, renders configured calendar nudges from `COUPLE_REMINDERS`, and can optionally read Google Calendar events. Recipe photos are loaded from public Wikimedia Commons URLs.

That separation is important:

- code gathers facts
- the prompt makes judgment calls
- rendering and email sending stay deterministic

If `OPENAI_API_KEY` is not set, the app still runs with fallback ranking, a fallback morning summary, and fallback devotional reflections and motivation.

## Useful Environment Variables

```text
OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5

MARKET_PULSE_ENABLED=true

LOCATION_NAME=Johannesburg
LATITUDE=-26.2041
LONGITUDE=28.0473
TIMEZONE=Africa/Johannesburg
WEATHER_LOCATIONS=Midrand|-25.9992|28.1263|Africa/Johannesburg|hourly;Johannesburg|-26.2041|28.0473|Africa/Johannesburg;Cape Town|-33.9249|18.4241|Africa/Johannesburg;Durban|-29.8587|31.0218|Africa/Johannesburg

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_TO=you@example.com
EMAIL_SUBJECT_PREFIX=Shivz Daily Brief
DEVOTIONAL_SUBJECT_PREFIX=Daily Motivation and Bible Verse

COUPLE_EMAIL_TO=you@example.com,spouse@example.com
COUPLE_SUBJECT_PREFIX=Team ShiNola - Our Daily Brief
COUPLE_NAMES=you two
COUPLE_REMINDERS=Check the shared Gmail calendars;Confirm one family handoff

GOOGLE_CALENDAR_ENABLED=true
GOOGLE_CALENDAR_CREDENTIALS_FILE=credentials.json
GOOGLE_CALENDAR_TOKEN_FILE=token.json
GOOGLE_CALENDAR_IDS=primary|Shiven;your-wife-calendar-id@gmail.com|Nolene
GOOGLE_CALENDAR_LOOKAHEAD_DAYS=3

WHATSAPP_ENABLED=true
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_BUSINESS_ACCOUNT_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_TO=27821234567
WHATSAPP_TEMPLATE_NAME=shivz_daily_brief_v1
WHATSAPP_TEMPLATE_LANGUAGE=en
```

Feed lists are semicolon-separated. Each entry is `Name|URL`.

The market pulse uses Frankfurter for exchange rates and Yahoo Finance's delayed chart data for commodity futures. It is a morning signal, not financial advice.

## Test

```powershell
python -m unittest discover -s tests
```
