from __future__ import annotations

"""Daily scripture and reflection tool."""

import json
from dataclasses import dataclass
from datetime import datetime

from daily_brief.config import AppConfig
from daily_brief.http_client import post_json
from daily_brief.models import DevotionalContent, ScriptureVerse
from daily_brief.prompts.devotional_prompt import (
    DEVOTIONAL_INSTRUCTIONS,
    build_devotional_input,
)
from daily_brief.tools.ranking import RESPONSES_API_URL


@dataclass(frozen=True)
class VerseSeed:
    reference: str
    text: str
    title: str
    reflection: str


KJV = "KJV"

VERSE_ROTATION: tuple[VerseSeed, ...] = (
    VerseSeed(
        reference="Psalm 118:24",
        text="This is the day which the LORD hath made; we will rejoice and be glad in it.",
        title="Start With Gratitude",
        reflection=(
            "This verse pulls the day back into perspective before the noise gets loud. "
            "It reminds us that today is not just another block on the calendar; it is a gift "
            "to receive with intention. Rejoicing does not mean everything is easy. It means "
            "we choose to begin from gratitude instead of anxiety, and from trust instead of rush."
        ),
    ),
    VerseSeed(
        reference="Philippians 4:13",
        text="I can do all things through Christ which strengtheneth me.",
        title="Strength For Today",
        reflection=(
            "Paul is not promising effortless success; he is pointing to a strength deeper than mood, "
            "energy, or perfect circumstances. This verse is encouragement for the tasks that feel heavy "
            "and the moments that ask more of you than you expected. The focus is not self-pressure. "
            "It is steady reliance on Christ for what is needed today."
        ),
    ),
    VerseSeed(
        reference="Proverbs 3:5-6",
        text=(
            "Trust in the LORD with all thine heart; and lean not unto thine own understanding. "
            "In all thy ways acknowledge him, and he shall direct thy paths."
        ),
        title="Trust The Path",
        reflection=(
            "This scripture invites us to loosen our grip on needing every answer in advance. Trusting God "
            "does not mean switching off wisdom; it means refusing to make our own understanding the final "
            "authority. As you acknowledge Him in the ordinary parts of the day, direction often comes one "
            "faithful step at a time."
        ),
    ),
    VerseSeed(
        reference="Isaiah 41:10",
        text=(
            "Fear thou not; for I am with thee: be not dismayed; for I am thy God: "
            "I will strengthen thee; yea, I will help thee; yea, I will uphold thee with the right hand of my righteousness."
        ),
        title="Held And Helped",
        reflection=(
            "The comfort in this verse is not that fear never appears, but that fear is not left unanswered. "
            "God speaks presence, strength, help, and support into the places where we feel thin. Whatever "
            "today carries, you do not have to meet it as though you are unsupported. There is grace beneath "
            "your feet and help beside you."
        ),
    ),
    VerseSeed(
        reference="Psalm 46:10",
        text="Be still, and know that I am God: I will be exalted among the heathen, I will be exalted in the earth.",
        title="Stillness Has Strength",
        reflection=(
            "Stillness is not weakness. It is the decision to stop letting panic set the pace. This verse calls "
            "us to remember who God is before we react to what is in front of us. A quiet heart can see more "
            "clearly, choose more wisely, and carry the day with less strain."
        ),
    ),
    VerseSeed(
        reference="Romans 8:28",
        text="And we know that all things work together for good to them that love God, to them who are the called according to his purpose.",
        title="Good Is Still Working",
        reflection=(
            "This verse does not pretend every situation is good. It says God is able to work through all things "
            "toward His purpose. That gives us courage when life feels unfinished or unclear. You may not see "
            "the full picture today, but you can trust that God is not wasting the pieces."
        ),
    ),
    VerseSeed(
        reference="Lamentations 3:22-23",
        text="It is of the LORD'S mercies that we are not consumed, because his compassions fail not. They are new every morning: great is thy faithfulness.",
        title="Mercy This Morning",
        reflection=(
            "The beauty of this verse is its freshness. Yesterday's worries, mistakes, and weight do not get "
            "the final word over today. God's mercy meets the morning before the inbox, the schedule, or the "
            "pressure does. Begin from that: compassion has not run out, and faithfulness has not gone missing."
        ),
    ),
    VerseSeed(
        reference="Joshua 1:9",
        text=(
            "Have not I commanded thee? Be strong and of a good courage; be not afraid, neither be thou dismayed: "
            "for the LORD thy God is with thee whithersoever thou goest."
        ),
        title="Courage With Company",
        reflection=(
            "Courage in this verse is not personality type or bravado. It is rooted in God's presence. The call "
            "to be strong comes with the promise that you are not walking alone. Whatever room you enter, task "
            "you face, or decision you carry today, let courage come from knowing who goes with you."
        ),
    ),
    VerseSeed(
        reference="1 Peter 5:7",
        text="Casting all your care upon him; for he careth for you.",
        title="Put It Down",
        reflection=(
            "This is a wonderfully practical verse. It does not say to polish your worries until they look more "
            "spiritual. It says to cast them on God. The reason is simple and personal: He cares for you. Today, "
            "prayer can be the place where the weight moves from your shoulders into stronger hands."
        ),
    ),
    VerseSeed(
        reference="James 1:5",
        text="If any of you lack wisdom, let him ask of God, that giveth to all men liberally, and upbraideth not; and it shall be given him.",
        title="Ask For Wisdom",
        reflection=(
            "Needing wisdom is not failure; it is an invitation to ask. This verse shows God's generosity toward "
            "people who admit they do not know everything. Before forcing a decision or overthinking every angle, "
            "pause and ask for wisdom. God is not reluctant to guide a humble heart."
        ),
    ),
    VerseSeed(
        reference="Psalm 23:1",
        text="The LORD is my shepherd; I shall not want.",
        title="Enough For The Road",
        reflection=(
            "A shepherd does not only point from a distance; he leads, protects, and provides along the way. This "
            "verse reminds us that God's care is personal and present. You may still have needs, plans, and "
            "questions, but you are not abandoned to manage them alone. The Shepherd knows the road."
        ),
    ),
    VerseSeed(
        reference="Matthew 11:28",
        text="Come unto me, all ye that labour and are heavy laden, and I will give you rest.",
        title="Rest Is Offered",
        reflection=(
            "Jesus speaks directly to tired people, not polished people. The invitation is not to perform better "
            "first, but to come. Rest here is more than sleep; it is relief for the soul that has been carrying "
            "too much alone. Let this verse give you permission to bring the weight to Christ today."
        ),
    ),
    VerseSeed(
        reference="Hebrews 11:1",
        text="Now faith is the substance of things hoped for, the evidence of things not seen.",
        title="Faith Before Sight",
        reflection=(
            "Faith often has to stand before the evidence feels complete. This verse reminds us that hope is not "
            "empty wishing; it has substance when it is anchored in God. You may not see every outcome today, "
            "but you can still take the next faithful step with confidence."
        ),
    ),
    VerseSeed(
        reference="John 14:27",
        text=(
            "Peace I leave with you, my peace I give unto you: not as the world giveth, give I unto you. "
            "Let not your heart be troubled, neither let it be afraid."
        ),
        title="A Different Peace",
        reflection=(
            "The peace Jesus gives is not dependent on the world becoming quiet first. It is different because it "
            "comes from Him, not from perfect control. This verse is a gentle command to your heart: do not let "
            "trouble take the driver's seat. Receive peace as a gift before the day starts bargaining for it."
        ),
    ),
    VerseSeed(
        reference="Micah 6:8",
        text=(
            "He hath shewed thee, O man, what is good; and what doth the LORD require of thee, "
            "but to do justly, and to love mercy, and to walk humbly with thy God?"
        ),
        title="Keep It Simple",
        reflection=(
            "This verse cuts through spiritual clutter with a simple shape for the day: justice, mercy, and humble "
            "walking with God. It is practical faith with its sleeves rolled up. In your decisions, conversations, "
            "and work, look for the path that is fair, compassionate, and humble."
        ),
    ),
    VerseSeed(
        reference="Galatians 6:9",
        text="And let us not be weary in well doing: for in due season we shall reap, if we faint not.",
        title="Do Not Give Up",
        reflection=(
            "Good work can still be tiring. This verse acknowledges the weariness while giving us a reason to keep "
            "going. Faithfulness often grows quietly before it becomes visible. If you are doing the right thing "
            "and it feels slow, take heart. Due season is still in God's hands."
        ),
    ),
)


def build_daily_devotional(
    brief_date: datetime,
    config: AppConfig,
    use_openai: bool = True,
) -> DevotionalContent:
    seed = select_daily_verse(brief_date)
    verse = ScriptureVerse(
        reference=seed.reference,
        text=seed.text,
        translation=KJV,
    )

    if use_openai and config.openai_api_key:
        try:
            return _write_with_openai(verse, seed, config)
        except Exception as exc:
            print(f"OpenAI devotional failed; using fallback. {exc}")

    return _fallback_devotional(verse, seed)


def select_daily_verse(brief_date: datetime) -> VerseSeed:
    return VERSE_ROTATION[brief_date.toordinal() % len(VERSE_ROTATION)]


def _write_with_openai(
    verse: ScriptureVerse,
    seed: VerseSeed,
    config: AppConfig,
) -> DevotionalContent:
    verse_payload = {
        "reference": verse.reference,
        "translation": verse.translation,
        "text": verse.text,
    }
    payload = {
        "model": config.openai_model,
        "instructions": DEVOTIONAL_INSTRUCTIONS,
        "input": build_devotional_input(
            json.dumps(verse_payload, ensure_ascii=True, indent=2),
        ),
        "max_output_tokens": 700,
        "text": {
            "format": {
                "type": "json_schema",
                "name": "daily_devotional",
                "strict": True,
                "schema": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "title": {"type": "string"},
                        "reflection": {"type": "string"},
                    },
                    "required": ["title", "reflection"],
                },
            }
        },
    }
    response = post_json(
        RESPONSES_API_URL,
        payload=payload,
        headers={"Authorization": f"Bearer {config.openai_api_key}"},
    )
    data = json.loads(_extract_output_text(response))
    title = str(data.get("title", "")).strip() or seed.title
    reflection = str(data.get("reflection", "")).strip() or seed.reflection
    return DevotionalContent(
        title=title,
        verse=verse,
        reflection=reflection,
        used_openai=True,
    )


def _fallback_devotional(
    verse: ScriptureVerse,
    seed: VerseSeed,
) -> DevotionalContent:
    return DevotionalContent(
        title=seed.title,
        verse=verse,
        reflection=seed.reflection,
        used_openai=False,
    )


def _extract_output_text(response: dict[str, object]) -> str:
    output_text = response.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text

    parts: list[str] = []
    output = response.get("output")
    if isinstance(output, list):
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content")
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                text = part.get("text")
                if isinstance(text, str):
                    parts.append(text)

    text = "\n".join(parts).strip()
    if not text:
        raise RuntimeError("OpenAI response did not include output text.")
    return text
