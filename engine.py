"""Kindling engine — profile storage, progress, and compilation.

State lives in plugin_data_dir('kindling'):
  profiles/<slug>.json   one per person/client intake
  state.json             hook bookkeeping (greeted sessions, dismissed flag)

Profiles are plain JSON, human-readable, and belong to the user — the README
documents exactly where they live. Nothing here talks to the network.
"""

import json
import re
import time
from pathlib import Path

from .questions import DEPTH, get_section, sections_for


def _data_dir() -> Path:
    try:
        from plugins.plugin_storage import plugin_data_dir  # documented public API
        return Path(plugin_data_dir("kindling"))
    except Exception:
        p = Path.home() / ".hermes" / "plugin-data" / "kindling"
        p.mkdir(parents=True, exist_ok=True)
        return p


def _slug(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return s[:48] or "me"


def _profiles_dir() -> Path:
    d = _data_dir() / "profiles"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _path(slug: str) -> Path:
    return _profiles_dir() / f"{slug}.json"


def _load(slug: str):
    p = _path(slug)
    if not p.exists():
        return None
    return json.loads(p.read_text())


def _save(prof: dict):
    p = _path(prof["slug"])
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(prof, indent=1))
    tmp.replace(p)


def _active_slug() -> str:
    st = _load_state()
    return st.get("active_profile", "")


def _load_state() -> dict:
    p = _data_dir() / "state.json"
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            return {}
    return {}


def _save_state(st: dict):
    p = _data_dir() / "state.json"
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, indent=1))
    tmp.replace(p)


def resolve_profile(name: str = "") -> str:
    """Profile name arg -> slug. Empty string resolves to the active profile."""
    if name:
        slug = _slug(name)
        if not _path(slug).exists():
            # try prefix match over existing profiles
            cands = [p.stem for p in _profiles_dir().glob("*.json") if p.stem.startswith(slug)]
            if len(cands) == 1:
                return cands[0]
        return slug
    return _active_slug() or "me"


def start_profile(name: str, kind: str, depth: str) -> dict:
    slug = _slug(name) if name else "me"
    if _path(slug).exists():
        prof = _load(slug)
        return {"resumed": True, **status(slug)}
    if depth not in DEPTH:
        depth = "standard"
    if kind not in ("personal", "client"):
        kind = "personal"
    secs = sections_for(kind)
    prof = {
        "slug": slug,
        "name": name or "me",
        "kind": kind,
        "depth": depth,
        "created": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "updated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "sections": {s["id"]: {"status": "todo", "qa": [], "notes": ""} for s in secs},
        "finished_at": None,
    }
    _save(prof)
    st = _load_state()
    st["active_profile"] = slug
    _save_state(st)
    return {"resumed": False, **status(slug)}


def status(slug: str = "") -> dict:
    slug = resolve_profile(slug)
    prof = _load(slug)
    if not prof:
        return {"error": f"no profile '{slug}'. Start one with kindling_start.",
                "existing": list_profiles()}
    secs = prof["sections"]
    done = [k for k, v in secs.items() if v["status"] == "done"]
    doing = [k for k, v in secs.items() if v["status"] == "doing"]
    todo = [k for k, v in secs.items() if v["status"] == "todo"]
    total = len(secs)
    cov = round(100 * (len(done) + 0.5 * len(doing)) / total) if total else 0
    qa_count = sum(len(v["qa"]) for v in secs.values())
    return {
        "profile": slug, "name": prof["name"], "kind": prof["kind"], "depth": prof["depth"],
        "coverage_pct": cov, "qa_pairs": qa_count,
        "sections_done": done, "section_in_progress": doing[0] if doing else None,
        "sections_remaining": todo,
        "finished": bool(prof.get("finished_at")),
        "updated": prof["updated"],
    }


def next_section(slug: str = "") -> dict:
    slug = resolve_profile(slug)
    prof = _load(slug)
    if not prof:
        return {"error": f"no profile '{slug}'. Start one with kindling_start."}
    order = [s["id"] for s in sections_for(prof["kind"])]
    sec = None
    for sid in order:
        if prof["sections"][sid]["status"] in ("doing", "todo"):
            sec = get_section(prof["kind"], sid)
            break
    if sec is None:
        return {"all_sections_complete": True,
                "next": "Run kindling_finish to compile the profile into memory entries, "
                        "setup recommendations, and (for clients) a handoff brief."}
    prof["sections"][sec["id"]]["status"] = "doing"
    prof["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _save(prof)
    depth = DEPTH[prof["depth"]]
    done = sum(1 for v in prof["sections"].values() if v["status"] == "done")
    return {
        "profile": slug,
        "section": sec["id"],
        "title": sec["title"],
        "why": sec["why"],
        "progress": f"{done}/{len(order)} sections complete",
        "opener_guidance": sec["opener"],
        "questions": sec["questions"][: depth["max_questions_per_section"]],
        "followups": sec["followups"],
        "care": sec["care"],
        "depth_note": depth["note"],
        "sensitive": sec["sensitive"],
        "instruction": "Have the CONVERSATION — one question at a time, react and follow up "
                       "before moving on. When the section is covered, call kindling_save with "
                       "the Q&A pairs and complete=true.",
    }


def save_qa(slug: str, section: str, qa: list, notes: str = "", complete: bool = False) -> dict:
    slug = resolve_profile(slug)
    prof = _load(slug)
    if not prof:
        return {"error": f"no profile '{slug}'"}
    sec = get_section(prof["kind"], section)
    if sec is None:
        return {"error": f"unknown section '{section}' for {prof['kind']} profile. "
                         f"Valid: {[s['id'] for s in sections_for(prof['kind'])]}"}
    entry = prof["sections"][section]
    for item in qa or []:
        if isinstance(item, dict) and item.get("a"):
            entry["qa"].append({"q": str(item.get("q", ""))[:300],
                                 "a": str(item["a"])[:2000],
                                 "ts": time.strftime("%Y-%m-%dT%H:%M:%S")})
    if notes:
        entry["notes"] = (entry["notes"] + "\n" + notes).strip()[:4000]
    if complete:
        entry["status"] = "done"
    elif entry["qa"]:
        entry["status"] = "doing"
    prof["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _save(prof)
    st = status(slug)
    return {"saved": len(qa or []), "section_status": entry["status"],
            "coverage_pct": st["coverage_pct"], "sections_remaining": st["sections_remaining"]}


def compile_profile(slug: str = "") -> dict:
    slug = resolve_profile(slug)
    prof = _load(slug)
    if not prof:
        return {"error": f"no profile '{slug}'"}
    kind = prof["kind"]
    order = [s["id"] for s in sections_for(kind)]

    # 1) memory-ready declarative facts (the agent stores these via the memory tool / USER.md)
    facts = []
    for sid in order:
        sec = get_section(kind, sid)
        entry = prof["sections"][sid]
        for item in entry["qa"]:
            a = item["a"].strip()
            if not a:
                continue
            q = item["q"].strip().rstrip("?")
            if q:
                facts.append(f"[{sec['title']}] {q}: {a}")
            else:
                facts.append(f"[{sec['title']}] {a}")

    # 2) boundaries deserve their own hard-rules block
    hard_rules = []
    b = prof["sections"].get("boundaries", {})
    for item in b.get("qa", []):
        hard_rules.append(item["a"].strip())

    # 3) automation candidates harvested from rhythms/work notes
    candidates = []
    for sid in ("work", "rhythms", "goals"):
        entry = prof["sections"].get(sid, {})
        for item in entry.get("qa", []):
            a = item["a"].lower()
            if any(k in a for k in ("forget", "every week", "every day", "daily", "weekly",
                                     "recurring", "remind", "always forget")):
                candidates.append(f"[{sid}] {item['a'].strip()[:200]}")

    done = [k for k in order if prof["sections"][k]["status"] == "done"]
    out = {
        "profile": slug, "name": prof["name"], "kind": kind,
        "coverage_pct": status(slug)["coverage_pct"],
        "sections_complete": done,
        "sections_missing": [k for k in order if k not in done],
        "memory_ready_facts": facts,
        "hard_rules": hard_rules,
        "automation_candidates": candidates,
        "instruction": (
            "Review memory_ready_facts with the user, distill them into concise declarative "
            "entries and save the durable ones with the memory tool (target=user for personal "
            "facts). hard_rules go into memory VERBATIM — they are the never-do list. "
            "automation_candidates: propose at most 2 as first builds and ask before creating "
            "any cron. Then run kindling_setup_check and walk the resulting plan top to bottom."
        ),
    }

    if kind == "client":
        eng = prof["sections"].get("engagement", {}).get("qa", [])
        out["client_brief"] = {
            "engagement_qa": eng,
            "note": ("This profile belongs to the CLIENT. The agent caters to them, not to the "
                     "operator. When handing off: export this compile output, review it with the "
                     "client, and store the facts in the client's own Hermes memory/profile."),
        }

    prof["finished_at"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    _save(prof)
    return out


def list_profiles() -> list:
    out = []
    for p in sorted(_profiles_dir().glob("*.json")):
        try:
            prof = json.loads(p.read_text())
            out.append({"slug": prof.get("slug", p.stem), "name": prof.get("name"),
                        "kind": prof.get("kind"), "coverage_pct": status(p.stem)["coverage_pct"],
                        "finished": bool(prof.get("finished_at")), "updated": prof.get("updated")})
        except Exception:
            out.append({"slug": p.stem, "error": "unreadable"})
    return out


def delete_profile(name: str) -> dict:
    slug = resolve_profile(name)
    p = _path(slug)
    if not p.exists():
        return {"error": f"no profile '{slug}'"}
    p.unlink()
    st = _load_state()
    if st.get("active_profile") == slug:
        st.pop("active_profile", None)
        _save_state(st)
    return {"deleted": slug}


# ------------------------------------------------------------- hook state

def greet_decision(session_id: str, platform: str) -> str:
    """pre_llm_call hook helper: 'greet' | 'silent'."""
    st = _load_state()
    if st.get("dismissed"):
        return "silent"
    if session_id in st.get("greeted", []):
        return "silent"
    if platform in ("cron", "hook", "automation"):
        return "silent"
    if list(_profiles_dir().glob("*.json")):
        return "silent"  # user already did an intake; never nag
    greeted = (st.get("greeted") or [])[-50:]
    greeted.append(session_id)
    st["greeted"] = greeted
    _save_state(st)
    return "greet"


def dismiss():
    st = _load_state()
    st["dismissed"] = True
    _save_state(st)


def undismss():
    st = _load_state()
    st.pop("dismissed", None)
    _save_state(st)
