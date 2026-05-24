# Daily Brief Agent

This is a small learning project that builds a daily email brief with:

- Midrand hourly weather for the next few hours
- weather snapshots for Johannesburg, Cape Town, and Durban
- a market pulse with USD/ZAR, GBP/ZAR, gold, silver, and Brent crude
- a short morning summary written from the day's signals
- top 5 South African news links
- top 5 world news links
- top 5 AI and tech story links
- an approved WhatsApp template version of the daily brief
- a separate Daily Motivation and Bible Verse email
- a private couple brief with calendar nudges, a daily history note, a fun fact, a dish photo, a short recipe, and a weekly marriage spark
- a monthly Midrand grocery-specials scan with store-specific PDF attachments

The project is intentionally split into simple modules so you can learn how a practical agent is built:

1. Collect raw context from APIs and RSS feeds, including South African, world, and AI/tech news.
2. Pass the candidate stories through a ranking prompt.
3. Write a concise morning summary from the selected facts.
4. Render the answer into text and HTML.
5. Send it by email.
6. Schedule it to run daily at 07:00.
7. Build a separate devotional email from a scripture prompt.
8. Build a private couple email for you and your spouse.
9. Build a monthly grocery-specials pack for Pick n Pay, Checkers, and Woolworths.
10. Alert you if the scheduled run fails after retries.

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
      daily_reads.py # history and fun-fact snippets for the couple brief
      google_calendar.py # read-only Google Calendar OAuth and event fetching
      grocery_specials.py # scrapes configured grocery-specials sources
      rendering.py # email text and HTML
      devotional_rendering.py # devotional text, HTML, and WhatsApp rendering
      couple_rendering.py # couple brief text and HTML rendering
      grocery_rendering.py # grocery HTML email and per-store PDFs
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

When `EMAIL_TO` has multiple comma-separated addresses, the app sends to that
list privately instead of showing the full recipient list in the email header.

The optional `ALERT_EMAIL_TO` list controls who receives scheduled-run failure
alerts. If it is empty, alerts fall back to `EMAIL_TO`.

The weather cards include `Real-time update` links. Those open the static
`docs/live-weather.html` page in a browser with the region coordinates in the
URL, then fetch live Open-Meteo data on demand.

The market card includes a `Live markets` link. That opens
`docs/live-markets.html`, which refreshes USD/ZAR, GBP/ZAR, gold, silver, and
Brent in the browser using browser-safe market feeds.

Thin RSS story summaries are best-effort enriched from the linked article page
before the email is rendered. If a site blocks the fetch, the original feed
summary is used and the card collapses naturally.

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

Set `DEVOTIONAL_EMAIL_TO` when the devotional should go to a different audience
from the main brief. If it is empty, the devotional falls back to `EMAIL_TO`.

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
Multiple `COUPLE_EMAIL_TO` addresses are also sent privately.

Preview the monthly grocery-specials pack:

```powershell
daily-brief --grocery-specials
```

Preview the grocery HTML email:

```powershell
daily-brief --grocery-specials --save-html grocery-preview.html
```

Send the grocery-specials email with store-specific PDF attachments:

```powershell
daily-brief --grocery-specials --send
```

The grocery pack reads `GROCERY_SPECIALS_SOURCES`, groups results by store, and
writes visual PDFs into `GROCERY_SPECIALS_OUTPUT_DIR`. The email highlights
where to shop, best buys, and category picks. Attachments include one combined
month-end shopping pack plus store-specific guides. Where the source exposes
the data, cards show product images, regular price, saving amount, saving
percentage, and unit price. Checkers and Pick n Pay currently use catalogue-page
imagery; Woolworths exposes product-level images. If `GROCERY_SPECIALS_EMAIL`
is empty, sending falls back to `COUPLE_EMAIL_TO`, then `EMAIL_TO`.

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

The couple brief also includes two compact daily reads: a "What happened in
history today" note from Wikipedia's on-this-day feed, with a curated fallback
if the feed is unavailable, and a deterministic local fun fact. Set
`COUPLE_DAILY_READS_ENABLED=false` if you ever want to hide those sections.

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

## Live Weather And Markets Pages

The `Real-time update` weather buttons and `Live markets` button use GitHub Pages.
The static pages live at:

```text
docs/live-weather.html
docs/live-markets.html
```

The `Live Weather Page` workflow deploys that folder to GitHub Pages whenever
`docs/**` changes. In the repository settings, set GitHub Pages to use
`GitHub Actions` as the source if it is not already enabled.

After the first successful deploy, the email buttons open:

```text
https://shivenpillay5-ai.github.io/shivz_daily_brief/live-weather.html
https://shivenpillay5-ai.github.io/shivz_daily_brief/live-markets.html
```

Each weather link includes the selected region's name, latitude, longitude, and timezone.
The markets page fetches live/delayed market data directly in the browser from
Frankfurter, Gold API, and OilPriceAPI's no-key demo feed.

## GitHub Actions Scheduling

The GitHub workflows run from GitHub's cloud runners. That means your local machine does not need to be on.

Each workflow supports `repository_dispatch` for Cronjob.org and also has a
later native GitHub `schedule:` fallback:

```text
daily-brief
daily-devotional
team-shinola-brief
grocery-specials
```

Cronjob.org is the primary trigger. Use these Cronjob.org schedules:

```text
daily-brief          07:17 Africa/Johannesburg
daily-devotional     07:29 Africa/Johannesburg
team-shinola-brief   09:17 Africa/Johannesburg
grocery-specials     Monthly on the 26th at 18:17 Africa/Johannesburg
```

The native GitHub fallback schedules run later:

```text
daily-brief          08:17 Africa/Johannesburg
daily-devotional     08:29 Africa/Johannesburg
team-shinola-brief   10:17 Africa/Johannesburg
grocery-specials     Monthly on the 26th at 19:17 Africa/Johannesburg
```

Each workflow checks for a same-day successful run and writes a GitHub Actions
cache marker after its email is sent. If another run for the same workflow
starts on the same Africa/Johannesburg date, it skips the duplicate email.
Workflow concurrency also keeps same-email runs in order so overlapping cron
and fallback runs do not race each other.
Manual workflow runs include a `force_send` input for intentionally sending
again.

### External Scheduler Primary

GitHub's native schedule trigger can be delayed or dropped, so Cronjob.org is
the preferred wake-up path:

1. GitHub Actions still does the real work.
2. An external scheduler sends a tiny HTTPS POST to GitHub at the right time.
3. GitHub receives that `repository_dispatch` event and starts the matching workflow.

Create a fine-grained GitHub token:

1. GitHub -> Settings -> Developer settings -> Personal access tokens -> Fine-grained tokens.
2. Generate a new token for only `shivenpillay5-ai/shivz_daily_brief`.
3. Repository permissions: set `Contents` to `Read and write`.
4. Copy the token once. Treat it like a password.

Test the trigger locally from PowerShell:

```powershell
$env:GITHUB_DISPATCH_TOKEN = "paste-token-here"
.\scripts\trigger_github_dispatch.ps1 -EventType daily-brief
```

The command should print `Dispatched 'daily-brief'...` and GitHub Actions should show a new `repository_dispatch` run.

Then create external scheduler jobs. `cron-job.org` is a simple free option that supports custom HTTP methods, headers, body data, test runs, and execution history.

Use this URL for all jobs:

```text
https://api.github.com/repos/shivenpillay5-ai/shivz_daily_brief/dispatches
```

Use method `POST` and these headers:

```text
Accept: application/vnd.github+json
Authorization: Bearer YOUR_FINE_GRAINED_GITHUB_TOKEN
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

Create these request bodies and schedules:

```json
{"event_type":"daily-brief"}
```

07:17 Africa/Johannesburg

```json
{"event_type":"daily-devotional"}
```

07:29 Africa/Johannesburg

```json
{"event_type":"team-shinola-brief"}
```

09:17 Africa/Johannesburg

```json
{"event_type":"grocery-specials"}
```

Monthly on the 26th at 18:17 Africa/Johannesburg.

If the scheduler only accepts UTC, use `05:17`, `05:29`, `07:17`, and `16:17` UTC.

The Team ShiNola workflow needs these repository secrets:

```text
COUPLE_EMAIL_TO
GOOGLE_CALENDAR_CREDENTIALS_JSON_B64
GOOGLE_CALENDAR_TOKEN_JSON_B64
```

These optional repository secrets let each email type use the right audience:

```text
DEVOTIONAL_EMAIL_TO
GROCERY_SPECIALS_EMAIL
ALERT_EMAIL_TO
```

If an optional recipient secret is left empty, the app falls back to `EMAIL_TO`
for the daily/devotional emails and to `COUPLE_EMAIL_TO`, then `EMAIL_TO`, for
the grocery-specials email.

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

`src/daily_brief/agent.py` coordinates the workflow: fetch weather, fetch South African/world/AI news, rank stories, render the email, and send it.

`src/daily_brief/skills/SKILL.md` contains the single skill definition for the project. It explains what the `Shivz Daily Brief` skill does, when the agent should use it, and which tools it relies on.

`src/daily_brief/tools/` contains the executable Python modules that the agent calls. This keeps the distinction clear:

- `skills/SKILL.md` is the instruction/capability description.
- `tools/*.py` is the runnable implementation.

`src/daily_brief/prompts/ranking_prompt.py` contains the core model instruction. The program gives the model candidate stories that already include titles, links, sources, and summaries. The prompt tells the model to pick exactly the best 5 without inventing URLs.

`src/daily_brief/prompts/summary_prompt.py` contains the morning-summary instruction. It gives the model the selected weather, market, South African, world, and AI/tech facts and asks for a short reader-friendly summary without inventing details.

`src/daily_brief/prompts/devotional_prompt.py` contains the devotional instruction. It gives the model one public-domain KJV verse and asks for a short practical reflection plus a broader motivational closing. If no OpenAI key is configured, the app uses the curated fallback reflection and motivational closing.

The couple brief rotates meal ideas and short recipes daily, keeps one marriage spark for the week, renders configured calendar nudges from `COUPLE_REMINDERS`, and can optionally read Google Calendar events. Recipe photos are loaded from public Wikimedia Commons URLs for previews and embedded inline when the couple email is sent.

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
# Comma-separate multiple recipients. They are sent BCC-style.
EMAIL_TO=you@example.com
# Optional. Falls back to EMAIL_TO when empty.
DEVOTIONAL_EMAIL_TO=
# Optional. Falls back to EMAIL_TO when empty.
ALERT_EMAIL_TO=
EMAIL_SUBJECT_PREFIX=Shivz Daily Brief
DEVOTIONAL_SUBJECT_PREFIX=Daily Motivation and Bible Verse

# Comma-separate multiple recipients. They are sent BCC-style.
COUPLE_EMAIL_TO=you@example.com,spouse@example.com
COUPLE_SUBJECT_PREFIX=Team ShiNola - Our Daily Brief
COUPLE_NAMES=you two
COUPLE_REMINDERS=Check the shared Gmail calendars;Confirm one family handoff
COUPLE_DAILY_READS_ENABLED=true

GROCERY_SPECIALS_EMAIL=
GROCERY_SPECIALS_SUBJECT_PREFIX=Midrand Grocery Specials
GROCERY_SPECIALS_AREA=Midrand, Gauteng
GROCERY_SPECIALS_MAX_ITEMS_PER_STORE=120
GROCERY_SPECIALS_OUTPUT_DIR=grocery-specials
GROCERY_SPECIALS_SOURCES=Woolworths|Woolworths Food Promotions|https://www.woolworths.co.za/cat/Promotions/Save/Food/_/N-1z13sk5;Checkers|My Catalogue Product Table|https://my-catalogue.co.za/checkers-specials;Pick n Pay|My Catalogue Product Table|https://my-catalogue.co.za/pick-n-pay-specials

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

SOUTH_AFRICA_NEWS_FEEDS=BusinessTech|https://businesstech.co.za/news/feed/;News24 South Africa|https://feeds.news24.com/articles/news24/SouthAfrica/rss
NEWS_FEEDS=BBC World|https://feeds.bbci.co.uk/news/world/rss.xml;The Guardian World|https://www.theguardian.com/world/rss;NPR World|https://feeds.npr.org/1004/rss.xml;UN News|https://news.un.org/feed/subscribe/en/news/all/rss.xml
AI_TECH_FEEDS=OpenAI News|https://openai.com/news/rss.xml;Google AI Blog|https://blog.google/technology/ai/rss/;TechCrunch AI|https://techcrunch.com/category/artificial-intelligence/feed/;VentureBeat AI|https://venturebeat.com/category/ai/feed/;MIT Technology Review AI|https://www.technologyreview.com/topic/artificial-intelligence/feed/
```

Feed lists are semicolon-separated. Each entry is `Name|URL`.

The email market pulse uses Frankfurter for exchange rates and Yahoo Finance's delayed chart data for commodity futures. The live browser page uses Frankfurter, Gold API, and OilPriceAPI instead because Yahoo's chart endpoint is not browser-CORS friendly. It is a morning signal, not financial advice.

## Test

```powershell
python -m unittest discover -s tests
```
