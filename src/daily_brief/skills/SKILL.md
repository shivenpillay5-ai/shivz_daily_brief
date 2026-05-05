# Shivz Daily Brief Skill

## What This Skill Does

Build and send the daily `Shivz Daily Brief`, the companion `Daily Motivation and Bible Verse` email, and the private `Team ShiNola - Our Daily Brief` couple email.

The brief includes:

- Midrand hourly weather for the next few hours
- Johannesburg, Cape Town, and Durban weather snapshots
- a market pulse with USD/ZAR, GBP/ZAR, gold, silver, and Brent crude
- a concise morning summary written from the collected facts
- top world news links
- top AI and tech story links
- a polished HTML email layout
- an optional concise WhatsApp text version
- a separate devotional email with a KJV scripture, short reflection, and motivational closing
- a private couple email with calendar nudges, a dish photo, a short recipe, and a weekly marriage spark

## When The Agent Should Use This Skill

Use this skill when the user wants to:

- preview the daily brief
- send the daily brief by email
- send the daily brief by WhatsApp
- preview or send the Daily Motivation and Bible Verse email
- preview or send the private couple email
- schedule the brief to run every morning
- send a failure alert if the scheduled run fails
- understand or adjust how the brief is created

## How The Agent Runs The Skill

The agent is implemented in:

```text
src/daily_brief/agent.py
```

The agent coordinates the workflow in this order:

1. Read configuration from `.env`.
2. Fetch configured weather locations using the weather tool.
3. Fetch market data using the market tool.
4. Fetch world news and AI/tech news using the news tool.
5. Rank stories using the ranking tool.
6. Write the morning summary using the summary tool.
7. Render the text, HTML email, and WhatsApp message using the rendering tool.
8. Send the email using the email tool when `--send` is used.
9. Send WhatsApp messages using the WhatsApp tool when `--send-whatsapp` is used.
10. Send a failure alert using the alerts tool when `--send-failure-alert` is used.

For `--devotional`, the agent uses a smaller workflow:

1. Select the day's KJV scripture from the devotional tool.
2. Write the reflection and motivational closing using the devotional prompt, or use curated fallbacks.
3. Render text, HTML, and WhatsApp versions using the devotional rendering tool.
4. Send through the same email or WhatsApp tools.

For `--couple`, the agent uses a separate deterministic workflow:

1. Read couple-specific recipients, names, and reminders from `.env`.
2. Select the day's meal idea, recipe, and dish photo.
3. Fetch read-only Google Calendar events when `GOOGLE_CALENDAR_ENABLED=true`.
4. Select the week's marriage spark.
5. Render text and HTML versions using the couple rendering tool.
6. Send only to `COUPLE_EMAIL_TO`.

## Tools Used By This Skill

The executable Python tools live in:

```text
src/daily_brief/tools/
```

Tool files:

- `weather.py` fetches current, daily, and optional hourly weather from Open-Meteo.
- `market.py` fetches exchange rates and commodity futures for the market pulse.
- `news.py` reads RSS and Atom feeds.
- `ranking.py` ranks candidate stories.
- `summary.py` writes a short morning summary from the selected facts.
- `rendering.py` creates the plain-text and HTML email.
- `devotional.py` selects the scripture and writes the devotional reflection and motivation.
- `devotional_rendering.py` creates the devotional plain-text, HTML, and WhatsApp versions.
- `couple.py` selects couple brief meal ideas, reminders, and marriage sparks.
- `couple_rendering.py` creates the couple brief plain-text and HTML email.
- `google_calendar.py` authorizes read-only Google Calendar access and fetches events.
- `email.py` sends the final email through SMTP.
- `alerts.py` sends a concise failure alert with the failed run link and log tail.
- `whatsapp.py` sends the concise text brief through the WhatsApp Cloud API.

## Prompt Used By This Skill

The ranking prompt lives in:

```text
src/daily_brief/prompts/ranking_prompt.py
```

When an OpenAI API key is configured, the ranking tool gives candidate stories to that prompt and asks the model to select the best stories.

If no OpenAI key is configured, the ranking tool uses deterministic fallback logic.
The summary tool follows the same pattern: use the model when `OPENAI_API_KEY` exists, otherwise write a deterministic fallback summary.
The devotional tool also follows this pattern: use the model when available, otherwise use a curated KJV verse, fallback reflection, and motivational closing.
The couple tool is deterministic for now and does not call OpenAI.

## Important Constraints

- Do not invent links.
- Use only URLs collected from configured feeds.
- Keep the email reader-facing and polished.
- Keep the WhatsApp version short enough for a text message.
- Show Midrand first when hourly weather is configured.
- Keep Midrand hourly detail in email, but summarize it in WhatsApp.
- Hide noisy feed warnings from the HTML email.
- If one feed fails, continue building the brief from the remaining feeds.
- If the scheduled GitHub run fails after retries, send one failure alert email.
- Use public-domain KJV text for the devotional scripture unless a licensed Bible source is added later.
- Require `COUPLE_EMAIL_TO` before sending the private couple email.
- Keep Google Calendar access read-only unless the user explicitly asks for write support later.
