"""Onboard Me question bank — the deep-intake interview.

Design rules baked into this data:
- ONE question at a time is enforced by the skill, not here; sections are
  conversation guides, not forms.
- Every section has `followups`: prompts for the agent to go deeper BEFORE
  moving on. The magic of a good intake is the second and third question.
- `sensitive` sections carry `care` guidance: offer, never press; skipping
  is always allowed and never asked about twice.
- `why` tells the agent (and, if asked, the user) what the section feeds.
"""

SECTIONS = [
    {
        "id": "basics",
        "title": "Who you are",
        "why": "Identity, timezone, and communication style — used in almost every future reply.",
        "est_minutes": 6,
        "sensitive": False,
        "opener": "Start warm and easy. This section should feel like the first five minutes "
                  "of a good conversation, not a form.",
        "questions": [
            "What should I call you?",
            "Where in the world are you — city or timezone?",
            "How did you end up here with Hermes, and what made you set it up?",
            "How do you want me to talk to you — casual or formal, short answers or deep dives?",
            "Any words, phrases, or habits you already know you'd hate in an assistant?",
        ],
        "followups": [
            "If they mention coming from another AI (Claude, ChatGPT, Gemini), ask what they loved and what annoyed them there — that is the single best predictor of preferences.",
            "If they answer a style question with 'whatever's fine', offer two concrete examples and ask which feels closer.",
        ],
        "care": None,
    },
    {
        "id": "daily_life",
        "title": "Your days",
        "why": "Routines, energy patterns, and personal context — lets the agent time things right and speak like someone who knows them.",
        "est_minutes": 8,
        "sensitive": True,
        "opener": "Frame it as 'so I can fit into your life instead of bumping into it'. "
                  "Everything here is optional.",
        "questions": [
            "Walk me through a normal day, from waking up to winding down.",
            "What hours are you sharpest? When do you usually hit a wall?",
            "What do you do outside of work — hobbies, obsessions, rabbit holes?",
            "Who's in your life that I might hear about — family, partner, roommates, pets? Only what you're comfortable sharing.",
            "How do you like reminders — gentle nudges or blunt ones?",
        ],
        "followups": [
            "When they name a hobby, ask one genuine follow-up about it (what got them into it, where they are with it now). People open up when the assistant is actually curious.",
            "If they describe a pain point in their day ('mornings are chaos'), dig once: what would removing it look like?",
        ],
        "care": "Personal life is offered, never pressed. If an answer is short or deflecting, "
                "move on naturally and do not return to it. Never ask twice about anything "
                "they declined once.",
    },
    {
        "id": "work",
        "title": "Your work",
        "why": "Job, business, customers, and tool stack — the raw material for most concrete help the agent will give.",
        "est_minutes": 10,
        "sensitive": False,
        "opener": "Most people light up here. Let them talk shop.",
        "questions": [
            "What do you do for work — job, business, both?",
            "If you own or run something: what does it do, and who are your customers?",
            "What does your role actually eat most of your time day to day?",
            "Which tools and software could you not do your work without?",
            "What recurring tasks do you already wish you could hand to someone else?",
        ],
        "followups": [
            "For every tool they name, note what it's FOR in their workflow, not just the name.",
            "When they name a recurring task, ask how often it happens and roughly how long it takes — this becomes automation candidates later.",
            "Ask what 'busy season' looks like for them, if they have one.",
        ],
        "care": None,
    },
    {
        "id": "goals",
        "title": "Where you're headed",
        "why": "Short- and long-term goals — lets the agent connect daily tasks to what actually matters to them.",
        "est_minutes": 8,
        "sensitive": False,
        "opener": "Shift energy from present to future. 'Okay, let's zoom out a bit.'",
        "questions": [
            "Six months from now, what would have to be true for you to say things are going great?",
            "What are you actively building toward this year?",
            "What's something you've wanted to start for a while but haven't?",
            "What's the biggest bottleneck or drain holding you back right now?",
        ],
        "followups": [
            "For each goal, ask what the very next step is — and whether anything is stopping that step today.",
            "If a goal is vague ('grow the business'), ask what number or event would mean 'grown'.",
        ],
        "care": None,
    },
    {
        "id": "ai_use",
        "title": "How you want to use AI",
        "why": "Expectations, delegation appetite, and past AI frustrations — calibrates how autonomous the agent should be.",
        "est_minutes": 8,
        "sensitive": False,
        "opener": "Be honest that this shapes how the agent behaves, not just what it knows.",
        "questions": [
            "Have you used AI assistants before? What worked, and what was disappointing?",
            "What would you most like me to take off your plate in the first month?",
            "When should I check with you first, and when should I just handle it and tell you after?",
            "Is there anything you want AI to never touch — topics, accounts, decisions?",
        ],
        "followups": [
            "If they say 'just do everything', probe for the one exception — there is always one (money, messages to their boss, public posts).",
            "Ask how they felt when a past assistant got something wrong — it reveals their real risk tolerance.",
        ],
        "care": None,
    },
    {
        "id": "preferences",
        "title": "Taste",
        "why": "Likes, dislikes, and aesthetic sense — the difference between an assistant that's useful and one that feels like yours.",
        "est_minutes": 6,
        "sensitive": False,
        "opener": "Fun section. Keep it light.",
        "questions": [
            "What apps or products do you love, and what makes them good?",
            "What do you hate in software — or in writing?",
            "How do you like to consume things: video, reading, podcasts? Where?",
            "Any topics you want kept out of our conversations entirely — news, politics, sports?",
        ],
        "followups": [
            "Capture specifics: 'hates em dashes', 'loves bullet points', 'wants sources linked'. Vague taste ('make it nice') deserves one concrete either/or example.",
        ],
        "care": None,
    },
    {
        "id": "boundaries",
        "title": "Hard rules",
        "why": "The never-do list. This section protects the user and is the foundation of trust.",
        "est_minutes": 6,
        "sensitive": False,
        "opener": "Set the tone: these are written down and treated as law, not suggestions.",
        "questions": [
            "What should I never do without asking you first — spending money, sending messages, posting publicly?",
            "Who should I never contact, or never mention you to?",
            "Any accounts, folders, or topics that are strictly off limits?",
            "When I'm unsure whether something is safe, what do you want me to do?",
        ],
        "followups": [
            "Translate each answer into a rule and read it back: 'So: never send email to clients without showing you a draft first. Correct?'",
            "Ask about the scariest thing an AI could do with their access — the answer is usually the most important rule.",
        ],
        "care": None,
    },
    {
        "id": "rhythms",
        "title": "Your week",
        "why": "Recurring schedule and cadence — feeds automations like briefs, reminders, and quiet hours.",
        "est_minutes": 6,
        "sensitive": False,
        "opener": "Practical section — this is where automations get designed.",
        "questions": [
            "What does a typical week look like — fixed meetings, routines, recurring obligations?",
            "Would you want a daily brief or summary? When should it land?",
            "Any deadlines, launches, or events coming up that I should know about now?",
            "Are there hours when I should never ping you?",
        ],
        "followups": [
            "Every 'I always forget to X' is an automation candidate — write it down verbatim.",
        ],
        "care": None,
    },
    {
        "id": "vision",
        "title": "The picture",
        "why": "Synthesis — ends the intake on their terms and converts everything into a first action.",
        "est_minutes": 5,
        "sensitive": False,
        "opener": "Wind-down energy. Reflect back two or three things you learned before asking.",
        "questions": [
            "If I were perfect at this, what does your life look like a month from now?",
            "What's the first thing we should build or set up together after this conversation?",
            "What haven't I asked about that you want me to know?",
        ],
        "followups": [
            "Whatever they answer for 'first thing', the agent should propose doing it immediately after the intake — momentum is the point.",
        ],
        "care": None,
    },
]

# Extra leading section for client intake (agencies setting Hermes up for a client).
CLIENT_SECTION = {
    "id": "engagement",
    "title": "The engagement",
    "why": "Defines whose agent this is: the client, not the operator. Everything downstream caters to the client.",
    "est_minutes": 8,
    "sensitive": False,
    "opener": "Ask the OPERATOR these questions about the client before the client intake begins.",
    "questions": [
        "Who is the client — company, and the person whose agent this becomes?",
        "What's your relationship and mandate: what have they asked you to set up?",
        "Whose preferences win when yours and theirs differ? (Default: theirs.)",
        "What will you deliver at the end — a configured agent, a brief, training?",
        "Anything the client has told you they're sensitive about?",
    ],
    "followups": [
        "Record the client's name, company, and the operator's name separately — the profile belongs to the client.",
    ],
    "care": None,
}

DEPTH = {
    "quick": {"max_questions_per_section": 3, "followup_passes": 0,
              "note": "Hit the core questions, minimal follow-ups, ~25 minutes total."},
    "standard": {"max_questions_per_section": 5, "followup_passes": 1,
                 "note": "Core questions plus one genuine follow-up each where it matters, ~50-70 minutes."},
    "deep": {"max_questions_per_section": 99, "followup_passes": 3,
             "note": "Full rabbit-hole mode: follow every interesting thread, 90+ minutes across sessions."},
}

SECTION_ORDER = [s["id"] for s in SECTIONS]


def sections_for(kind):
    """client profiles get the engagement section prepended."""
    if kind == "client":
        return [CLIENT_SECTION] + SECTIONS
    return list(SECTIONS)


def get_section(kind, sid):
    for s in sections_for(kind):
        if s["id"] == sid:
            return s
    return None
