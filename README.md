# Kindling

**Light your hearth.** Deep conversational onboarding for Hermes Agent —
the getting-to-know-you layer every new user (and every agency client)
should get before anything else.

Hermes is more powerful than any agent most people have used, and the
learning curve is real. Kindling replaces "figure it out yourself" with two
guided experiences:

1. **The deep intake** — a warm, structured conversation (quick ~25 min,
   standard ~50-70, deep 90+ across sessions) where the agent learns who you
   are: your days, your work, your goals, your taste, your hard rules. It
   compiles into memory-ready facts, so every future session starts with
   context instead of zero.
2. **The setup walkthrough** — `kindling_setup_check` inspects the actual
   install (model, gateway, memory, MCP, plugins, skills, crons) and returns
   a personalized plan with exact commands, plus a curated FAQ of real
   beginner failure modes harvested from the official docs, GitHub issues
   and community troubleshooting guides.

## Why a plugin and not a prompt

- The question bank is a **conversation engine, not a form**: sections carry
  opener guidance, follow-up prompts, and care rules for sensitive topics,
  and the bundled skill enforces the doctrine (one question at a time,
  follow up before moving on, reflect back, save after every section).
- **Resumable by design** — every section is persisted to
  `~/.hermes/plugin-data/kindling/profiles/<name>.json` as it completes.
  Close the laptop mid-intake; `/kindling status` picks it up days later.
- **Client mode** for agencies: run the same intake FOR a client, with an
  engagement section, per-client profiles that never mix, and a compiled
  handoff brief. The agent caters to the client, not the operator.
- `kindling_finish` doesn't just summarize — it separates **hard rules**
  (saved verbatim to memory), declarative facts, and **automation
  candidates** harvested from what the user said they keep forgetting.
- The setup advisor is **read-only and secret-blind**: it reports key
  *names* and counts, never values.

## Tools

| Tool | What it does |
|---|---|
| `kindling_start` | Create/resume a profile (personal or client; quick/standard/deep) |
| `kindling_next` | Next section: guidance, questions, follow-ups, care rules |
| `kindling_save` | Persist a section's Q&A (crash-safe, resumable) |
| `kindling_status` | Coverage %, sections done/in-progress/remaining |
| `kindling_finish` | Compile: memory-ready facts, hard rules, automation candidates, client brief |
| `kindling_setup_check` | Personalized install inspection + setup plan + researched FAQ |
| `kindling_profiles` | List / delete profiles |

Plus:

- **`/kindling`** slash command — `status · start [name] · client <name> · setup · finish · dismiss`
- **First-session hook** — on a fresh install with no profiles, the agent
  briefly offers the intake once per session. One `no` ends it forever
  (`/kindling dismiss`); it never nags after a profile exists.

## Install

```
hermes plugins install skeptical-agency/kindling --enable
```

Then just say **"let's do the kindling intake"** (or `/kindling start`).

## Disclosure

- Runs entirely on your machine. No network calls, no credentials, no
  accounts, no telemetry, and **no shell command execution** — the plugin
  only reads and writes its own JSON files. Bundled FAQ text quotes official
  troubleshooting docs; it is documentation returned to the agent, never
  executed.
- Stores intake answers as plain JSON under
  `~/.hermes/plugin-data/kindling/` — readable, editable, deletable by you
  (`kindling_profiles action=delete`).
- `kindling_setup_check` reads config file *structure* (key names, counts)
  and never reads or reports secret values.
- The bundled skill instructs the agent to confirm before creating any cron,
  automation, or memory entry from the intake.

Built by [Skeptical Agency](https://skeptical.agency). MIT licensed.
