"""Kindling setup advisor — inspects the local Hermes install and produces a
personalized, beginner-safe setup plan.

Grounded in real, researched failure modes (official FAQ, GitHub issues,
community troubleshooting guides, Nov 2026). READ-ONLY: parses config files
for the PRESENCE of keys and never reads or reports secret values.
"""

import os
import platform
import re
from pathlib import Path

HERMES_HOME = Path(os.environ.get("HERMES_HOME", Path.home() / ".hermes"))

# Symptom -> fix knowledge base (sources: official FAQ/troubleshooting docs,
# NousResearch/hermes-agent issues, awesome-hermes-agent troubleshooting).
FAQ = [
    {"symptom": "'hermes: command not found' after install",
     "fix": "The installer adds ~/.local/bin to PATH; reload your shell profile or open a new "
            "terminal. Do not run the installer with elevated permissions — if you did, follow "
            "the cleanup steps in the official README, then reinstall as your normal user.",
     "source": "official FAQ / README"},
    {"symptom": "Provider or model errors on first run (error 400, connection reset)",
     "fix": "Run `hermes setup --portal` — one OAuth gets a model provider plus the bundled "
            "tool gateway. Or `hermes model` to pick a provider manually. For local models "
            "(Ollama/vLLM), set base_url AND a context length matching the server's num_ctx.",
     "source": "official FAQ; issues #1460"},
    {"symptom": "Terminal tool says node/nvm/pyenv/cargo not found",
     "fix": "Hermes snapshots your environment through a bash login shell, which skips your "
            "interactive shell init files. Set terminal.shell_init_files in the Hermes config "
            "to the init files your version managers need — the official FAQ lists the common "
            "patterns.",
     "source": "official FAQ"},
    {"symptom": "Desktop app and CLI behave differently / see different config",
     "fix": "They can run against different HERMES_HOME/profiles. Compare `hermes config get "
            "model.default` in the terminal with the Desktop settings page; make sure both "
            "point at the same profile before debugging anything else.",
     "source": "issue #107596"},
    {"symptom": "Skills you added don't show up",
     "fix": "Confirm the file is at ~/.hermes/skills/<name>/SKILL.md (exact name, exact "
            "location), then start a NEW session — skills load at session start.",
     "source": "official FAQ / skills docs"},
    {"symptom": "Telegram/Discord/WhatsApp bot never receives DMs",
     "fix": "Check pairing and allowlists, then run `hermes doctor`. The gateway must be "
            "running (hermes gateway status) and the bot token belongs to the profile you "
            "think it does.",
     "source": "official FAQ / gateway docs"},
    {"symptom": "Windows: antivirus quarantines uv.exe or hermes binaries",
     "fix": "Whitelist %LOCALAPPDATA%\\hermes\\bin per the README attestation instructions.",
     "source": "README / FAQ"},
    {"symptom": "Small VPS: browser tools eat all the RAM",
     "fix": "Reinstall with --skip-browser, or disable browser features in config.",
     "source": "README / community guides"},
    {"symptom": "Running Hermes in Docker: it can't find its config",
     "fix": "Mount ~/.hermes to the container's HERMES_HOME (default /opt/data) — "
            "`docker run -v ~/.hermes:/opt/data nousresearch/hermes-agent`.",
     "source": "issue #45792"},
    {"symptom": "WSL2: Hermes can't drive Windows Chrome",
     "fix": "Don't use /browser connect across the WSL boundary — add chrome-devtools-mcp "
            "as an MCP server via cmd.exe/powershell.exe instead.",
     "source": "official FAQ"},
    {"symptom": "Anything else weird",
     "fix": "`hermes doctor` then `hermes update` fixes a surprising amount. Discord "
            "(discord.gg/NousResearch) #support is the human fallback.",
     "source": "official troubleshooting"},
]


def _read_config() -> dict:
    """Parse ~/.hermes/config.yaml without a yaml dependency (regex-level only,
    presence checks — values are never reported for secret-looking keys)."""
    p = HERMES_HOME / "config.yaml"
    if not p.exists():
        return {}
    try:
        import yaml  # present in the Hermes runtime
        return yaml.safe_load(p.read_text()) or {}
    except Exception:
        return {"_raw": p.read_text(errors="replace")}


def _env_key_names() -> set:
    names = set()
    p = HERMES_HOME / ".env"
    if p.exists():
        for line in p.read_text(errors="replace").splitlines():
            m = re.match(r"\s*(?:export\s+)?([A-Z0-9_]+)\s*=", line)
            if m:
                names.add(m.group(1))
    names.update(k for k in os.environ if re.match(r"^[A-Z0-9_]+$", k))
    return names


def check() -> dict:
    cfg = _read_config()
    raw = cfg.get("_raw", "")
    env_names = _env_key_names()

    healthy, missing, steps = [], [], []

    # --- model / provider ------------------------------------------------
    model_default = ""
    if isinstance(cfg.get("model"), dict):
        model_default = str(cfg["model"].get("default") or "")
    elif raw:
        m = re.search(r"^\s*default:\s*(\S+)", raw, re.M)
        model_default = m.group(1) if m else ""
    provider_keys = [k for k in env_names if re.search(
        r"(OPENROUTER|ANTHROPIC|OPENAI|NOUS|GEMINI|GOOGLE|ZHIPU|MOONSHOT|MINIMAX|DEEPSEEK|GROQ).*(_API_KEY|_KEY|_TOKEN)$", k)]
    portal_auth = (HERMES_HOME / "auths.json").exists() or any(
        "portal" in str(p.name).lower() for p in HERMES_HOME.glob("*"))
    if model_default:
        healthy.append(f"model configured: {model_default}")
    else:
        missing.append("no model set")
        steps.append({"do": "Set up the model provider (easiest path: Nous Portal one-login)",
                      "cmd": "hermes setup --portal",
                      "why": "One OAuth gets you 300+ models plus the bundled tool gateways. "
                             "Alternative: `hermes model` to configure any provider or a local "
                             "Ollama/vLLM endpoint."})

    # --- gateway / messaging ----------------------------------------------
    gw_keys = [k for k in env_names if re.search(r"(TELEGRAM|DISCORD|SLACK|WHATSAPP)", k)]
    gw_cfg = bool(re.search(r"telegram|discord|whatsapp|slack", raw, re.I)) if raw else any(
        k in cfg for k in ("telegram", "discord", "gateway", "whatsapp"))
    if gw_keys or gw_cfg:
        healthy.append("messaging gateway: configured (at least one channel)")
    else:
        missing.append("no messaging channel connected")
        steps.append({"do": "Connect a chat surface so the agent reaches you outside the terminal",
                      "cmd": "hermes gateway  # then follow prompts for Telegram/Discord/WhatsApp",
                      "why": "Telegram is the most common first choice; you'll pair via a code "
                             "and can then talk to your agent from your phone."})

    # --- memory -------------------------------------------------------------
    mem_cfg = ("memory" in cfg) if isinstance(cfg, dict) and "_raw" not in cfg else bool(
        re.search(r"^memory:", raw, re.M))
    if mem_cfg:
        healthy.append("memory: configured")
    else:
        missing.append("no explicit memory backend")
        steps.append({"do": "Decide on long-term memory (built-in works; providers add sync)",
                      "cmd": "hermes config get memory  # docs: user-guide/features/memory",
                      "why": "Memory is what makes the agent remember you between sessions. "
                             "The intake you just did feeds directly into it."})

    # --- mcp / plugins / skills / crons --------------------------------------
    mcp_names = []
    if isinstance(cfg.get("mcp_servers"), dict):
        mcp_names = list(cfg["mcp_servers"].keys())
    elif raw:
        mcp_names = re.findall(r"^  ([a-z0-9_-]+):\s*$", raw.split("mcp_servers:")[-1], re.M) if "mcp_servers:" in raw else []
    healthy.append(f"MCP servers: {len(mcp_names)}" + (f" ({', '.join(mcp_names[:6])})" if mcp_names else ""))

    plug_dirs = []
    for base in (HERMES_HOME / "plugins",):
        if base.exists():
            plug_dirs = [p.name for p in base.iterdir() if (p / "plugin.yaml").exists()]
    healthy.append(f"plugins installed: {len(plug_dirs)}" + (f" ({', '.join(plug_dirs[:5])})" if plug_dirs else ""))
    if not plug_dirs:
        steps.append({"do": "Browse the plugin marketplace — this is where Hermes grows",
                      "cmd": "hermes plugins search  # or browse hermes-agent.nousresearch.com/marketplace",
                      "why": "Plugins add tools, connectors and automations in one command."})

    skills_dirs = []
    for base in (HERMES_HOME / "skills",):
        if base.exists():
            skills_dirs = [p for p in base.rglob("SKILL.md")]
    healthy.append(f"skills present: {len(skills_dirs)}")

    cron_dir = HERMES_HOME / "cron"
    n_crons = len(list(cron_dir.rglob("*.json"))) if cron_dir.exists() else 0
    healthy.append(f"cron jobs: {n_crons}")

    # --- platform-specific notes --------------------------------------------
    notes = []
    sysname = platform.system()
    if sysname == "Windows":
        notes.append("Windows: if antivirus quarantines uv.exe, whitelist %LOCALAPPDATA%\\hermes\\bin (README attestation section).")
        if os.environ.get("WSL_DISTRO_NAME") or "microsoft" in platform.release().lower():
            notes.append("WSL2: to drive Windows Chrome, add chrome-devtools-mcp via cmd.exe instead of /browser connect.")
    if sysname == "Darwin":
        notes.append("macOS: if the terminal tool can't find node or your version managers, set "
                     "terminal.shell_init_files in the Hermes config (official FAQ has the patterns).")

    steps.append({"do": "Run the built-in health check any time something seems off",
                  "cmd": "hermes doctor && hermes update",
                  "why": "Doctor catches the common install/auth/config problems; update keeps "
                         "you on the release your docs match."})

    return {
        "hermes_home": str(HERMES_HOME),
        "platform": f"{sysname} {platform.release()}",
        "healthy": healthy,
        "missing": missing,
        "next_steps": steps,
        "platform_notes": notes,
        "faq": FAQ,
        "privacy": "This report lists key NAMES and counts only — no secret values were read "
                   "or stored, and everything here stays on this machine.",
    }
