"""Tool handlers — thin JSON wrappers over engine + setup_advisor."""

import json

from . import engine, setup_advisor


def _ok(payload):
    return json.dumps(payload, default=str)


def _fail(exc):
    return _ok({"error": str(exc)[:600]})


def start(args, ctx=None):
    try:
        name = str(args.get("name") or "").strip()
        kind = args.get("kind") or "personal"
        depth = args.get("depth") or "standard"
        res = engine.start_profile(name, kind, depth)
        if res.get("resumed"):
            res["note"] = "Profile already exists — resuming. Use onboard_next for the current section."
        else:
            res["note"] = ("Profile created. Read the bundled onboard-me skill for interview "
                           "doctrine, then call onboard_next and start the CONVERSATION — "
                           "warm, one question at a time, follow up before moving on.")
        return _ok(res)
    except Exception as exc:  # noqa: BLE001
        return _fail(exc)


def next_section(args, ctx=None):
    try:
        return _ok(engine.next_section(str(args.get("profile") or "")))
    except Exception as exc:  # noqa: BLE001
        return _fail(exc)


def save(args, ctx=None):
    try:
        qa = args.get("qa")
        if not isinstance(qa, list):
            return _ok({"error": "qa must be a list of {q, a} pairs"})
        return _ok(engine.save_qa(str(args.get("profile") or ""),
                                   str(args.get("section") or ""),
                                   qa,
                                   str(args.get("notes") or ""),
                                   bool(args.get("complete"))))
    except Exception as exc:  # noqa: BLE001
        return _fail(exc)


def status(args, ctx=None):
    try:
        return _ok(engine.status(str(args.get("profile") or "")))
    except Exception as exc:  # noqa: BLE001
        return _fail(exc)


def finish(args, ctx=None):
    try:
        return _ok(engine.compile_profile(str(args.get("profile") or "")))
    except Exception as exc:  # noqa: BLE001
        return _fail(exc)


def setup_check(args, ctx=None):
    try:
        return _ok(setup_advisor.check())
    except Exception as exc:  # noqa: BLE001
        return _fail(exc)


def profiles(args, ctx=None):
    try:
        action = args.get("action") or "list"
        if action == "list":
            return _ok({"profiles": engine.list_profiles(),
                        "data_dir": str(engine._data_dir())})
        if action == "delete":
            name = str(args.get("name") or "")
            if not name:
                return _ok({"error": "delete requires 'name'"})
            return _ok(engine.delete_profile(name))
        return _ok({"error": f"unknown action {action!r}"})
    except Exception as exc:  # noqa: BLE001
        return _fail(exc)


HANDLERS = {
    "onboard_start": start,
    "onboard_next": next_section,
    "onboard_save": save,
    "onboard_status": status,
    "onboard_finish": finish,
    "onboard_setup_check": setup_check,
    "onboard_profiles": profiles,
}
