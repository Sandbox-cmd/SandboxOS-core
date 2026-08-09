# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""make: the co-builder verb — AI hands on a project, honestly bookkept.

`make "intent"` opens the session, runs the builder (the claude command, or
whatever SANDBOX_CLAUDE_CMD names), and closes with a code-computed diff.
Without a builder installed, make still works: it writes the full prompt to
the project and tells you where — your hands, your way. `--open`/`--close`
are the same bookkeeping for building with your own hands: open snapshots
the file listing so close can COMPUTE what changed — the diff is code's
word, never the builder's. The summary stages behind the owner's key: what
happened is fact (event), what it meant is a claim (staged note).
"""
import hashlib
import json
import os
import shutil
import subprocess

from . import desk, journal, project

SKIP = {".git", "__pycache__", ".DS_Store", ".make"}
CLAUDE_ENV = "SANDBOX_CLAUDE_CMD"
TIMEOUT_ENV = "SANDBOX_MAKE_TIMEOUT"


def _listing(root):
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP]
        for name in filenames:
            p = os.path.join(dirpath, name)
            rel = os.path.relpath(p, root)
            try:
                with open(p, "rb") as f:
                    out[rel] = hashlib.sha256(f.read()).hexdigest()
            except OSError:
                continue
    return out


def _open_path(ws, name):
    return os.path.join(ws, journal.STATE_DIR, "make-open-%s.json" % name)


def open_session(ws, name, intent):
    if not os.path.exists(project.contract_path(ws, name)):
        return False, "no project named %s" % name
    p = _open_path(ws, name)
    if os.path.exists(p):
        return False, "a make session is already open on %s — close it first" % name
    root = project.root_of(ws, name)
    snap = {"intent": intent, "root": root, "listing": _listing(root),
            "opened": journal.now()}
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(snap, f)
    journal.append(ws, {"op": "make", "phase": "open", "project": name,
                        "body": intent, "origin": "machine",
                        "triggered": "session"})
    return True, "session open on %s — %s" % (name, intent)


def _prompt(ws, name, intent):
    c = project.parse_contract(project.contract_path(ws, name))
    canon_path = os.path.join(project.dirpath(ws, name), "CANON.md")
    canon = open(canon_path, encoding="utf-8").read() if os.path.exists(canon_path) else ""
    return ("You are building on the project %r (goal: %s).\n"
            "The intent for this session: %s\n\n"
            "What the record already knows about this project:\n%s\n"
            "Work in the current directory. When done, print four lines: what "
            "you made, what changed, what to check next, one risk you see."
            % (name, c["goal"] if c else "", intent, canon))


def build(ws, name, intent):
    """The full verb: open → run the builder → close. Honest without one."""
    ok, msg = open_session(ws, name, intent)
    if not ok:
        return False, msg
    root = project.root_of(ws, name)
    env_cmd = os.environ.get(CLAUDE_ENV, "").strip()
    if env_cmd == "none":
        cmd = None  # the explicit no-builder switch, for tests and preference
    else:
        cmd = env_cmd or ("claude" if shutil.which("claude") else None)
    prompt = _prompt(ws, name, intent)
    if cmd is None:
        out = os.path.join(root, "PROMPT.md")
        with open(out, "w", encoding="utf-8") as f:
            f.write(prompt + "\n")
        close_session(ws, name)  # nothing built; the diff says so honestly
        return True, ("no builder installed — the full prompt is at %s; run it "
                      "your way, then: sandbox make --close --summary \"...\"" % out)
    timeout = int(os.environ.get(TIMEOUT_ENV, "1800"))
    try:
        r = subprocess.run([cmd, "-p", prompt], cwd=root, capture_output=True,
                           text=True, timeout=timeout)
        tail = (r.stdout or "").strip()[-2000:]
    except subprocess.TimeoutExpired:
        close_session(ws, name, "builder timed out after %ds" % timeout)
        return False, "the builder ran past %ds and was stopped — the diff is on the record" % timeout
    ok2, close_msg = close_session(ws, name, tail[-400:] if tail else "")
    verdict = "the builder finished" if r.returncode == 0 else \
              "the builder exited %d — read its words before trusting the diff" % r.returncode
    return r.returncode == 0, "%s\n%s\n%s" % (verdict, tail, close_msg)


def close_session(ws, name, summary=""):
    p = _open_path(ws, name)
    if not os.path.exists(p):
        return False, "no make session open on %s" % name
    with open(p, encoding="utf-8") as f:
        snap = json.load(f)
    now_listing = _listing(snap["root"])
    before = snap["listing"]
    added = sorted(set(now_listing) - set(before))
    removed = sorted(set(before) - set(now_listing))
    changed = sorted(k for k in now_listing if k in before and now_listing[k] != before[k])
    diff = {"added": added, "removed": removed, "changed": changed}
    event = journal.append(ws, {
        "op": "make", "phase": "close", "project": name,
        "body": snap["intent"], "origin": "machine", "triggered": "session",
        "diff": diff})
    os.remove(p)
    n = len(added) + len(removed) + len(changed)
    if summary:
        desk.submit(ws, {"body": "make: %s: %s" % (name, summary),
                         "cls": "make-summary", "origin": "machine",
                         "project": name, "receipt": "journal:%s" % event["id"]})
    # "confirmed" is earned by a real diff; an empty one says "attempted" —
    # the word must not grade itself generously in exactly the place this
    # system claims it does not.
    if n:
        lines = ["confirmed — %d file(s) changed on %s" % (n, name)]
    else:
        lines = ["attempted — nothing changed on %s (the diff is empty, and says so)" % name]
    for rel in (added + changed + removed)[:20]:
        lines.append("  " + rel)
    if summary:
        lines.append("1 summary staged, waiting on your keypress. approve it:  sandbox approve")
    return True, "\n".join(lines)
