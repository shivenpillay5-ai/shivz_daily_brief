from __future__ import annotations

"""Content rotation for the private couple brief."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from daily_brief.config import AppConfig
from daily_brief.models import CoupleBriefContent, MarriageSpark, MealIdea
from daily_brief.tools.daily_reads import (
    build_daily_history_moment,
    select_daily_fun_fact,
)
from daily_brief.tools.google_calendar import fetch_google_calendar_events


MEAL_ROTATION: tuple[MealIdea, ...] = (
    MealIdea(
        title="Chicken pesto wraps",
        description=(
            "Warm wraps with sliced chicken, pesto, baby spinach, tomato, and a little"
            " cheese. Add fruit or yoghurt on the side if the evening is busy."
        ),
        ingredients=[
            "4 wraps",
            "2 cooked chicken breasts, sliced",
            "3 tbsp pesto",
            "1 cup baby spinach",
            "1 tomato, sliced",
            "Grated cheese or feta",
        ],
        steps=[
            "Warm the wraps in a dry pan for a few seconds.",
            "Spread each wrap with pesto, then add chicken, spinach, tomato, and cheese.",
            "Fold tightly and toast seam-side down until the cheese softens.",
        ],
        prep_note="Cook extra chicken if you want an easy lunchbox win tomorrow.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Chicken_wrap_%281126876064%29.jpg?width=900"
        ),
        image_alt="Chicken wrap on a plate",
        image_credit="Photo: Father.Jack, Wikimedia Commons",
        image_credit_url=(
            "https://commons.wikimedia.org/wiki/"
            "File:Chicken_wrap_(1126876064).jpg"
        ),
    ),
    MealIdea(
        title="Mince curry and rice",
        description=(
            "A gentle mince curry with peas or mixed veg, served with rice and a quick"
            " cucumber salad."
        ),
        ingredients=[
            "500 g beef mince",
            "1 onion, chopped",
            "2 tsp curry powder",
            "1 tin chopped tomatoes",
            "1 cup frozen peas or mixed veg",
            "Cooked rice",
        ],
        steps=[
            "Brown the mince with onion in a little oil.",
            "Stir in curry powder, tomatoes, and veg, then simmer for 15 minutes.",
            "Serve over rice with cucumber or yoghurt on the side.",
        ],
        prep_note="Start the rice first, then let the curry simmer while everyone settles.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Beef_curry_rice_003.jpg?width=900"
        ),
        image_alt="Curry and rice in a bowl",
        image_credit="Photo: Ocdp, Wikimedia Commons",
        image_credit_url="https://commons.wikimedia.org/wiki/File:Beef_curry_rice_003.jpg",
    ),
    MealIdea(
        title="Creamy tomato pasta",
        description=(
            "Pasta in a tomato and cream sauce with mushrooms, chicken, or chickpeas,"
            " depending on what is already in the fridge."
        ),
        ingredients=[
            "350 g pasta",
            "1 tin chopped tomatoes",
            "1/3 cup cream or plain yoghurt",
            "1 cup mushrooms, chicken, or chickpeas",
            "Garlic, herbs, salt, and pepper",
        ],
        steps=[
            "Boil the pasta until just tender.",
            "Simmer tomatoes, garlic, herbs, and your protein or veg for 10 minutes.",
            "Stir in cream, toss with pasta, and loosen with pasta water if needed.",
        ],
        prep_note="Keep the sauce slightly loose so leftovers reheat well.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Penne_Creamy_Pasta.jpg?width=900"
        ),
        image_alt="Creamy pasta in a bowl",
        image_credit="Photo: Deumati, Wikimedia Commons",
        image_credit_url="https://commons.wikimedia.org/wiki/File:Penne_Creamy_Pasta.jpg",
    ),
    MealIdea(
        title="Sheet-pan lemon chicken",
        description=(
            "Chicken pieces, potatoes, carrots, and onions roasted together with lemon,"
            " garlic, and herbs."
        ),
        ingredients=[
            "6 chicken pieces",
            "4 potatoes, cut into chunks",
            "3 carrots, sliced",
            "1 onion, cut into wedges",
            "Lemon juice, garlic, herbs, oil, salt, and pepper",
        ],
        steps=[
            "Heat the oven to 200 C and line a large tray.",
            "Toss chicken and veg with oil, lemon, garlic, herbs, salt, and pepper.",
            "Roast for 40 to 45 minutes, turning once, until golden and cooked through.",
        ],
        prep_note="Line the tray before roasting so cleanup does not steal the evening.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "One-Pan_Balsamic_Chicken_with_Roasted_Vegetables-5_%2830545623394%29.jpg?width=900"
        ),
        image_alt="Roasted chicken and vegetables on a tray",
        image_credit="Photo: Sharon Chen, Wikimedia Commons",
        image_credit_url=(
            "https://commons.wikimedia.org/wiki/"
            "File:One-Pan_Balsamic_Chicken_with_Roasted_Vegetables-5_(30545623394).jpg"
        ),
    ),
    MealIdea(
        title="Breakfast for dinner",
        description=(
            "Eggs, toast, mushrooms, tomato, beans, and whatever breakfast-style extras"
            " make the table feel fun."
        ),
        ingredients=[
            "Eggs",
            "Toast",
            "Baked beans",
            "Mushrooms",
            "Tomatoes",
            "Cheese, avo, or sausages if available",
        ],
        steps=[
            "Toast the bread and warm the beans.",
            "Fry or scramble the eggs while mushrooms and tomatoes cook in the same pan.",
            "Put everything on a platter and let everyone build a plate.",
        ],
        prep_note="This is a good option when energy is low but everyone still needs comfort.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "British_breakfast.jpg?width=900"
        ),
        image_alt="Breakfast plate with eggs, toast, and beans",
        image_credit="Photo: Arnaud 25, Wikimedia Commons",
        image_credit_url="https://commons.wikimedia.org/wiki/File:British_breakfast.jpg",
    ),
    MealIdea(
        title="Chicken stir-fry noodles",
        description=(
            "Noodles tossed with chicken strips, frozen veg, soy sauce, ginger, and a"
            " squeeze of lemon."
        ),
        ingredients=[
            "300 g noodles",
            "2 chicken breasts, sliced",
            "2 cups frozen mixed veg",
            "2 tbsp soy sauce",
            "1 tsp grated ginger",
            "Lemon juice or sweet chilli sauce",
        ],
        steps=[
            "Cook noodles according to the packet and drain.",
            "Stir-fry chicken until cooked, then add veg, ginger, and soy sauce.",
            "Toss in noodles and finish with lemon or sweet chilli.",
        ],
        prep_note="Use frozen veg unapologetically; this brief fully approves.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Chicken_noodle_stir_fry_%281027271537%29.jpg?width=900"
        ),
        image_alt="Chicken noodle stir-fry",
        image_credit="Photo: Father.Jack, Wikimedia Commons",
        image_credit_url=(
            "https://commons.wikimedia.org/wiki/"
            "File:Chicken_noodle_stir_fry_(1027271537).jpg"
        ),
    ),
    MealIdea(
        title="Loaded baked potatoes",
        description=(
            "Baked potatoes topped with tuna mayo, beans, cheese, leftover chicken, or"
            " sweetcorn."
        ),
        ingredients=[
            "4 large potatoes",
            "Butter or olive oil",
            "Tuna mayo, beans, or leftover chicken",
            "Grated cheese",
            "Sweetcorn or chopped spring onion",
        ],
        steps=[
            "Microwave potatoes until tender, then crisp in the oven if time allows.",
            "Split open and fluff the inside with butter or oil.",
            "Add toppings and return to the oven briefly to melt the cheese.",
        ],
        prep_note="Microwave first, then crisp in the oven if time allows.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Twice_baked_potato.JPG?width=900"
        ),
        image_alt="Loaded baked potato",
        image_credit="Photo: Mark James Miller, Wikimedia Commons",
        image_credit_url="https://commons.wikimedia.org/wiki/File:Twice_baked_potato.JPG",
    ),
    MealIdea(
        title="Simple fish tacos",
        description=(
            "Pan-fried fish fingers or hake strips in wraps with slaw, yoghurt sauce,"
            " and a bit of chilli for the adults."
        ),
        ingredients=[
            "Fish fingers or hake strips",
            "Small wraps",
            "Shredded cabbage or slaw mix",
            "Plain yoghurt or mayo",
            "Lemon juice",
            "Chilli sauce for the adults",
        ],
        steps=[
            "Cook the fish until crisp and hot.",
            "Mix yoghurt or mayo with lemon juice for a quick sauce.",
            "Load wraps with slaw, fish, sauce, and chilli if wanted.",
        ],
        prep_note="Let everyone build their own; it makes dinner feel lighter.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Fish_taco-1.jpg?width=900"
        ),
        image_alt="Fish tacos with slaw",
        image_credit="Photo: Leo Chiou, Wikimedia Commons",
        image_credit_url="https://commons.wikimedia.org/wiki/File:Fish_taco-1.jpg",
    ),
    MealIdea(
        title="Chickpea and spinach curry",
        description=(
            "A one-pot chickpea curry with spinach, tomato, onion, and spices, served"
            " with rice or roti."
        ),
        ingredients=[
            "2 tins chickpeas, drained",
            "1 onion, chopped",
            "1 tin chopped tomatoes",
            "2 cups spinach",
            "2 tsp curry powder",
            "Rice or roti",
        ],
        steps=[
            "Fry onion with curry powder until fragrant.",
            "Add tomatoes and chickpeas, then simmer for 12 to 15 minutes.",
            "Stir in spinach until wilted and serve with rice or roti.",
        ],
        prep_note="Make enough for freezer portions if the pot is already out.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Spinach-Chickpea_Curry_%283117324894%29.jpg?width=900"
        ),
        image_alt="Chickpea and spinach curry",
        image_credit="Photo: Kari Sullivan, Wikimedia Commons",
        image_credit_url=(
            "https://commons.wikimedia.org/wiki/"
            "File:Spinach-Chickpea_Curry_(3117324894).jpg"
        ),
    ),
    MealIdea(
        title="Saucy chicken meatballs",
        description=(
            "Chicken or beef meatballs in a tomato sauce, served with spaghetti, rice,"
            " or rolls."
        ),
        ingredients=[
            "500 g chicken or beef mince",
            "1 egg",
            "1/2 cup breadcrumbs",
            "1 jar or tin tomato sauce",
            "Spaghetti, rice, or rolls",
            "Parmesan or cheddar",
        ],
        steps=[
            "Mix mince, egg, breadcrumbs, salt, and pepper, then shape small balls.",
            "Brown meatballs in a pan, add tomato sauce, and simmer until cooked.",
            "Serve with pasta, rice, or rolls and a little cheese.",
        ],
        prep_note="Shape the meatballs small so they cook quickly and feel kid-friendly.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Meatballs_added_to_tomato_sauce.jpg?width=900"
        ),
        image_alt="Meatballs in tomato sauce",
        image_credit="Photo: Kim, Wikimedia Commons",
        image_credit_url=(
            "https://commons.wikimedia.org/wiki/"
            "File:Meatballs_added_to_tomato_sauce.jpg"
        ),
    ),
    MealIdea(
        title="Braai-style chicken bowls",
        description=(
            "Grilled or pan-seared chicken with mealies, salad, rice, and a quick"
            " yoghurt or chutney dressing."
        ),
        ingredients=[
            "2 chicken breasts or thighs",
            "Cooked rice",
            "Mealies or sweetcorn",
            "Cucumber and tomato",
            "Plain yoghurt",
            "Chutney or lemon juice",
        ],
        steps=[
            "Season and grill or pan-sear the chicken, then slice.",
            "Build bowls with rice, corn, cucumber, tomato, and chicken.",
            "Mix yoghurt with chutney or lemon juice and spoon over the top.",
        ],
        prep_note="Use the same base for lunch bowls if there are leftovers.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Chicken_and_rice.jpg?width=900"
        ),
        image_alt="Chicken and rice bowl",
        image_credit="Photo: National Cancer Institute, Wikimedia Commons",
        image_credit_url="https://commons.wikimedia.org/wiki/File:Chicken_and_rice.jpg",
    ),
    MealIdea(
        title="Veggie omelette night",
        description=(
            "Omelettes with cheese, peppers, mushrooms, tomato, and toast. Add avo if"
            " there is one ready."
        ),
        ingredients=[
            "6 eggs",
            "1/2 cup grated cheese",
            "Mushrooms, peppers, or tomato",
            "Butter or oil",
            "Toast",
            "Avo if available",
        ],
        steps=[
            "Whisk eggs with salt and pepper.",
            "Cook veg in a pan, pour in eggs, and sprinkle cheese over the top.",
            "Fold when just set and serve with toast and avo.",
        ],
        prep_note="Cook one big folded omelette and slice it if individual omelettes feel fussy.",
        image_url=(
            "https://commons.wikimedia.org/wiki/Special:FilePath/"
            "Breakfast_Omelette.jpg?width=900"
        ),
        image_alt="Omelette on a breakfast plate",
        image_credit="Photo: Zaheer Tejani, Wikimedia Commons",
        image_credit_url="https://commons.wikimedia.org/wiki/File:Breakfast_Omelette.jpg",
    ),
)


SPARK_ROTATION: tuple[MarriageSpark, ...] = (
    MarriageSpark(
        title="Protect one small pocket",
        motivation=(
            "A strong marriage is often refreshed by small protected moments, not grand"
            " pressure. Choose one pocket this week where the two of you are fully present."
        ),
        fun_idea="Take a 20 minute walk after dinner and leave admin talk for the last five minutes only.",
        conversation_starter="What is one thing you have carried lately that I can make lighter?",
    ),
    MarriageSpark(
        title="Notice out loud",
        motivation=(
            "Love stays fresh when appreciation becomes specific. Catch one ordinary"
            " thing your spouse does well this week and say it clearly."
        ),
        fun_idea="Send one unexpected voice note during the day: short, warm, and specific.",
        conversation_starter="What made you feel most seen by me recently?",
    ),
    MarriageSpark(
        title="Make the boring lighter",
        motivation=(
            "Shared admin can quietly drain romance. Pick one household task and turn it"
            " into teamwork instead of a silent burden."
        ),
        fun_idea="Put on one favourite playlist and clear one annoying task together for 15 minutes.",
        conversation_starter="Which recurring task should we simplify or stop overcomplicating?",
    ),
    MarriageSpark(
        title="Ask a better question",
        motivation=(
            "Freshness often returns through curiosity. Ask something that reaches past"
            " schedules, logistics, and tired answers."
        ),
        fun_idea="Have dessert or tea after the kids are settled and each answer one playful question.",
        conversation_starter="What would feel like a tiny adventure for us in the next month?",
    ),
    MarriageSpark(
        title="Choose gentleness first",
        motivation=(
            "The tone between you can become the weather of the home. Lead with"
            " gentleness this week, especially when the day has been full."
        ),
        fun_idea="Create a no-rush ten minute catch-up before screens take over.",
        conversation_starter="Where do we need a softer landing for each other right now?",
    ),
    MarriageSpark(
        title="Revisit an old favourite",
        motivation=(
            "Pick something specific from an earlier chapter of your relationship: a"
            " song you played often, a takeout order, a movie, a place you used to"
            " drive to, or a small ritual that felt like yours. The point is not"
            " nostalgia for its own sake. It is a gentle reminder that you have"
            " history, private jokes, proof of resilience, and plenty of story still"
            " to build."
        ),
        fun_idea=(
            "Choose one old favourite, tell each other what you remember about that"
            " season, then repeat a small version of it this week."
        ),
        conversation_starter=(
            "Which old favourite should we bring back for one evening, and what does"
            " it remind you of?"
        ),
    ),
    MarriageSpark(
        title="Be teammates on purpose",
        motivation=(
            "Marriage feels lighter when the problem is in front of you both, not between"
            " you. Name one pressure point and face it as a team."
        ),
        fun_idea="Do a quick Sunday reset: calendar, meals, one treat, and one thing to say no to.",
        conversation_starter="What would help this week feel more like us against the problem?",
    ),
    MarriageSpark(
        title="Add a little play",
        motivation=(
            "Play keeps marriage from becoming only management. Add one silly, low-effort"
            " thing this week simply because it makes you both lighter."
        ),
        fun_idea="Run a two-song kitchen dance break while dinner is cooking.",
        conversation_starter="What have we stopped doing that used to make life feel fun?",
    ),
)


CLOSINGS: tuple[str, ...] = (
    "One useful plan, one simple meal, one warm moment. That is a good day to build from.",
    "Keep the day practical and kind. The small tone you set together will travel far.",
    "A little intention in the morning can save a lot of friction by evening.",
    "Stay on the same side of the table today, even when the schedule gets loud.",
    "Do the next ordinary thing with love. It counts more than it looks like it does.",
)


def build_couple_brief(
    brief_date: datetime,
    config: AppConfig,
) -> CoupleBriefContent:
    calendar_events = []
    calendar_note = ""
    history_moment = None
    fun_fact = None

    if config.couple.daily_reads_enabled:
        history_moment = build_daily_history_moment(brief_date)
        fun_fact = select_daily_fun_fact(brief_date)

    if config.google_calendar.enabled:
        start_datetime, end_datetime = _calendar_window(brief_date, config)
        try:
            calendar_events = fetch_google_calendar_events(
                config.google_calendar,
                start_datetime=start_datetime,
                end_datetime=end_datetime,
                timezone_name=config.location.timezone,
            )
        except Exception as exc:
            calendar_note = f"Google Calendar could not be read: {exc}"

    return CoupleBriefContent(
        names=config.couple.names,
        reminders=config.couple.reminders,
        meal=select_daily_meal(brief_date),
        spark=select_weekly_marriage_spark(brief_date),
        closing=select_daily_closing(brief_date),
        history_moment=history_moment,
        fun_fact=fun_fact,
        calendar_events=calendar_events,
        calendar_note=calendar_note,
    )


def select_daily_meal(brief_date: datetime) -> MealIdea:
    return MEAL_ROTATION[brief_date.toordinal() % len(MEAL_ROTATION)]


def select_weekly_marriage_spark(brief_date: datetime) -> MarriageSpark:
    iso_year, iso_week, _ = brief_date.isocalendar()
    return SPARK_ROTATION[(iso_year * 53 + iso_week) % len(SPARK_ROTATION)]


def select_daily_closing(brief_date: datetime) -> str:
    return CLOSINGS[brief_date.toordinal() % len(CLOSINGS)]


def _calendar_window(
    brief_date: datetime,
    config: AppConfig,
) -> tuple[datetime, datetime]:
    try:
        timezone = ZoneInfo(config.location.timezone)
    except ZoneInfoNotFoundError:
        timezone = brief_date.tzinfo

    if timezone is not None and brief_date.tzinfo is None:
        local_date = brief_date.replace(tzinfo=timezone)
    elif timezone is not None:
        local_date = brief_date.astimezone(timezone)
    else:
        local_date = brief_date

    start_datetime = local_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_datetime = start_datetime + timedelta(
        days=config.google_calendar.lookahead_days
    )
    return start_datetime, end_datetime
