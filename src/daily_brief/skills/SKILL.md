# Shivz Daily Brief Skill

## What This Skill Does

Build and send the daily `Shivz Daily Brief`.

The brief includes:

- Midrand hourly weather for the next few hours
- Johannesburg, Cape Town, and Durban weather snapshots
- a market pulse with USD/ZAR, GBP/ZAR, gold, silver, and Brent crude
- top world news links
- top AI and tech story links
- a polished HTML email layout
- an optional concise WhatsApp text version

## When The Agent Should Use This Skill

Use this skill when the user wants to:

- preview the daily brief
- send the daily brief by email
- send the daily brief by WhatsApp
- schedule the brief to run every morning
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
6. Render the text, HTML email, and WhatsApp message using the rendering tool.
7. Send the email using the email tool when `--send` is used.
8. Send WhatsApp messages using the WhatsApp tool when `--send-whatsapp` is used.

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
- `rendering.py` creates the plain-text and HTML email.
- `email.py` sends the final email through SMTP.
- `whatsapp.py` sends the concise text brief through the WhatsApp Cloud API.

## Prompt Used By This Skill

The ranking prompt lives in:

```text
src/daily_brief/prompts/ranking_prompt.py
```

When an OpenAI API key is configured, the ranking tool gives candidate stories to that prompt and asks the model to select the best stories.

If no OpenAI key is configured, the ranking tool uses deterministic fallback logic.

## Important Constraints

- Do not invent links.
- Use only URLs collected from configured feeds.
- Keep the email reader-facing and polished.
- Keep the WhatsApp version short enough for a text message.
- Show Midrand first when hourly weather is configured.
- Keep Midrand hourly detail in email, but summarize it in WhatsApp.
- Hide noisy feed warnings from the HTML email.
- If one feed fails, continue building the brief from the remaining feeds.
