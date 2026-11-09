"""Kindling — light your hearth. Registration: tools, first-session hook,
slash command, bundled skill."""

from pathlib import Path

from .schemas import SCHEMAS
from .tools import HANDLERS

TOOL_DESCRIPTIONS = {
    "kindling_start": "Start or resume a deep-intake profile (personal or client) — the "
                       "structured getting-to-know-you conversation that gives the agent context",
    "kindling_next": "Next conversation section: guidance, questions, follow-up prompts",
    "kindling_save": "Persist a section's Q&A (call after each section; resumable)",
    "kindling_status": "Intake progress: coverage %, sections done/remaining",
    "kindling_finish": "Compile intake into memory-ready facts, hard rules, automation candidates, "
                        "client brief",
    "kindling_setup_check": "Inspect this Hermes install and return a personalized beginner setup "
                             "plan + real-world FAQ fixes",
    "kindling_profiles": "List or delete intake profiles",
}

GREET_CONTEXT = (
    "[kindling] This looks like a fresh Hermes install with no intake profile yet. If the user "
    "is new or hasn't been onboarded, briefly offer the Kindling deep intake: a guided "
    "conversation (~30-60 min, resumable) where you learn who they are, their work, goals, "
    "preferences and hard rules, so every future session starts with real context. If they say "
    "yes: call kindling_start, then follow the bundled kindling skill. If they decline or "
    "ignore the offer, drop it completely — do not mention it again; they can re-enable it "
    "any time with /kindling start."
)


_CFG = {"auto_greet": True}


def _pre_llm(session_id="", is_first_turn=False, platform="", **kwargs):
    """First-turn-only onboarding offer. Fail silent — a hook must never break a turn."""
    try:
        if not is_first_turn or not _CFG.get("auto_greet", True):
            return None
        from . import engine
        if engine.greet_decision(str(session_id), str(platform)) != "greet":
            return None
        return {"context": GREET_CONTEXT}
    except Exception:
        return None


def _slash_kindling(raw_args: str = "") -> str:
    import json as _json
    args = (raw_args or "").strip().lower()
    if args in ("", "status"):
        return HANDLERS["kindling_status"]({})
    if args.startswith("start"):
        rest = args[5:].strip()
        return HANDLERS["kindling_start"]({"name": rest or "", "kind": "personal"})
    if args.startswith("client"):
        rest = args[6:].strip()
        return HANDLERS["kindling_start"]({"name": rest, "kind": "client"})
    if args == "setup":
        return HANDLERS["kindling_setup_check"]({})
    if args == "finish":
        return HANDLERS["kindling_finish"]({})
    if args in ("dismiss", "stop-asking"):
        from . import engine
        engine.dismiss()
        return _json.dumps({"ok": True, "message": "Kindling will not offer the intake again. "
                                                    "Re-enable with /kindling undismiss."})
    if args == "undismiss":
        from . import engine
        engine.undismss()
        return _json.dumps({"ok": True})
    return _json.dumps({"error": f"unknown subcommand {args!r}",
                        "usage": "/kindling [status|start [name]|client <name>|setup|finish|dismiss]"})


def register(ctx):
    try:
        _CFG["auto_greet"] = bool(ctx.get_config("auto_greet", True))
    except Exception:
        _CFG["auto_greet"] = True

    for name, schema in SCHEMAS.items():
        ctx.register_tool(
            name=name,
            toolset="kindling",
            schema=schema,
            handler=HANDLERS[name],
            description=TOOL_DESCRIPTIONS.get(name, name),
        )

    ctx.register_hook("pre_llm_call", _pre_llm)

    try:
        ctx.register_command(
            "kindling", _slash_kindling,
            description="Onboarding intake: /kindling [status|start [name]|client <name>|setup|finish|dismiss]",
            args_hint="[status|start|client <name>|setup|finish|dismiss]",
        )
    except Exception:
        pass  # slash command is a convenience; never fail registration over it

    skills_dir = Path(__file__).parent / "skills"
    if skills_dir.exists():
        for child in sorted(skills_dir.iterdir()):
            skill_md = child / "SKILL.md"
            if child.is_dir() and skill_md.exists():
                ctx.register_skill(child.name, skill_md)
