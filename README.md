# Daily Brief Agent

This is a small learning project that builds a daily email brief with:

- Midrand hourly weather for the next few hours
- weather snapshots for Johannesburg, Cape Town, and Durban
- a market pulse with USD/ZAR, GBP/ZAR, gold, silver, and Brent crude
- a short morning summary written from the day’s signals
- top 5 world news links
- top 5 AI and tech story links

The project is intentionally split into simple modules so you can learn how a practical agent is built:

1. Collect raw context from APIs and RSS feeds.
2. Pass the candidate stories through a ranking prompt.
3. Write a concise morning summary from the selected facts.
4. Render the answer into text and HTML.
5. Send it by email.
6. Schedule it to run daily at 07:00.

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
      rendering.py # email text and HTML
      email.py     # SMTP sending
      whatsapp.py  # WhatsApp Cloud API sending
    prompts/
      ranking_prompt.py   # model instructions for selecting stories
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

Force the non-OpenAI fallback ranking:

```powershell
daily-brief --no-openai
```

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

## How The Prompt Fits In

`src/daily_brief/agent.py` coordinates the workflow: fetch weather, fetch news, rank stories, render the email, and send it.

`src/daily_brief/skills/SKILL.md` contains the single skill definition for the project. It explains what the `Shivz Daily Brief` skill does, when the agent should use it, and which tools it relies on.

`src/daily_brief/tools/` contains the executable Python modules that the agent calls. This keeps the distinction clear:

- `skills/SKILL.md` is the instruction/capability description.
- `tools/*.py` is the runnable implementation.

`src/daily_brief/prompts/ranking_prompt.py` contains the core model instruction. The program gives the model candidate stories that already include titles, links, sources, and summaries. The prompt tells the model to pick exactly the best 5 without inventing URLs.

`src/daily_brief/prompts/summary_prompt.py` contains the morning-summary instruction. It gives the model the selected weather, market, world, and AI/tech facts and asks for a short reader-friendly summary without inventing details.

That separation is important:

- code gathers facts
- the prompt makes judgment calls
- rendering and email sending stay deterministic

If `OPENAI_API_KEY` is not set, the app still runs with fallback ranking and a fallback morning summary.

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

WHATSAPP_ENABLED=true
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_BUSINESS_ACCOUNT_ID=...
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_TO=27821234567
```

Feed lists are semicolon-separated. Each entry is `Name|URL`.

The market pulse uses Frankfurter for exchange rates and Yahoo Finance's delayed chart data for commodity futures. It is a morning signal, not financial advice.

## Test

```powershell
python -m unittest discover -s tests
```
