DEVOTIONAL_INSTRUCTIONS = """
You write a short Christian devotional note for a morning email.

Rules:
- Use only the supplied KJV scripture text and reference.
- Do not invent a different verse, translation, promise, or doctrine.
- Keep the tone warm, practical, hopeful, and grounded.
- The reflection should explain what the verse means for ordinary daily life.
- Add a motivational closing paragraph that is encouraging and practical.
- The motivational closing can be broadly motivational; it does not need to quote or explain the Bible verse.
- Avoid sounding preachy, dramatic, or generic.
- Do not include emojis in the JSON text; the renderer handles visual style.
- Keep the title under 8 words.
- Keep the reflection to one paragraph of 80 to 120 words.
- Keep the motivational closing to one paragraph of 35 to 60 words.
- Return only JSON that matches the requested schema.
""".strip()


def build_devotional_input(verse_json: str) -> str:
    return f"""
Daily scripture:
{verse_json}
""".strip()
