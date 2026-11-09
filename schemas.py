"""LLM-facing schemas for Kindling tools."""

_QA_ITEM = {
    "type": "object",
    "properties": {
        "q": {"type": "string", "description": "The question (or topic) as asked"},
        "a": {"type": "string", "description": "The user's answer, in their words — capture substance, not a transcript"},
    },
    "required": ["a"],
}

SCHEMAS = {
    "kindling_start": {
        "type": "object",
        "properties": {
            "name": {"type": "string", "description": "Who this intake is for. Omit or 'me' for "
                                                       "the operator's own profile; use the client's "
                                                       "name for client intakes."},
            "kind": {"type": "string", "enum": ["personal", "client"],
                      "description": "personal = the user themselves; client = an agency intake "
                                     "for someone else (adds an engagement section and produces "
                                     "a handoff brief)"},
            "depth": {"type": "string", "enum": ["quick", "standard", "deep"],
                       "description": "quick ~25 min core only; standard ~50-70 min with "
                                      "follow-ups; deep = full rabbit-hole, 90+ min across sessions"},
        },
        "description": "Start (or resume) a Kindling deep-intake profile.",
    },
    "kindling_next": {
        "type": "object",
        "properties": {
            "profile": {"type": "string", "description": "Profile name; omit for the active one"},
        },
        "description": "Get the next conversation section: guidance, core questions, follow-up "
                       "prompts, and care rules. Then HAVE the conversation — don't recite it.",
    },
    "kindling_save": {
        "type": "object",
        "properties": {
            "profile": {"type": "string"},
            "section": {"type": "string", "description": "Section id from kindling_next"},
            "qa": {"type": "array", "items": _QA_ITEM,
                    "description": "Q&A pairs captured from the conversation"},
            "notes": {"type": "string", "description": "Free-form observations worth keeping"},
            "complete": {"type": "boolean", "description": "true when the section is fully covered"},
        },
        "required": ["section", "qa"],
        "description": "Persist conversation answers for a section. Save after each section — "
                       "progress survives crashes and resumes anywhere.",
    },
    "kindling_status": {
        "type": "object",
        "properties": {
            "profile": {"type": "string", "description": "Omit for the active profile"},
        },
        "description": "Intake progress: coverage %, sections done/in-progress/remaining.",
    },
    "kindling_finish": {
        "type": "object",
        "properties": {
            "profile": {"type": "string"},
        },
        "description": "Compile the finished intake: memory-ready facts, hard rules, automation "
                       "candidates, and (client mode) a handoff brief. Follow its instruction "
                       "field to land the facts in memory.",
    },
    "kindling_setup_check": {
        "type": "object",
        "properties": {},
        "description": "Inspect this Hermes install (model, gateway, memory, MCP, plugins, "
                       "skills, crons) and return a personalized beginner-safe setup plan with "
                       "exact commands, plus a curated FAQ of real-world failure modes. "
                       "Read-only; never reads secret values.",
    },
    "kindling_profiles": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["list", "delete"]},
            "name": {"type": "string", "description": "Profile to delete (action=delete)"},
        },
        "description": "List or delete intake profiles. Deleting is permanent — confirm with "
                       "the user first.",
    },
}
