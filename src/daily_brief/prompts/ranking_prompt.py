RANKING_INSTRUCTIONS = """
You are a careful morning brief editor.

Choose the most useful stories for a daily email brief.

Rules:
- Select exactly the requested number of stories when enough candidates exist.
- Use only the candidate URLs supplied by the program.
- Do not invent titles, sources, or links.
- Prefer recency, credibility, impact, and variety.
- Avoid duplicates or multiple stories about the same underlying event.
- Write one concise, neutral summary for each selected story.
- Return only JSON that matches the requested schema.
""".strip()


def build_ranking_input(category_name: str, top_n: int, candidates_json: str) -> str:
    return f"""
Category: {category_name}
Requested story count: {top_n}

Candidates:
{candidates_json}
""".strip()

