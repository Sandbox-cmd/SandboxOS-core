# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Projects: where the making happens.

One directory per project under the workshop's projects/. The contract file
(PROJECT.md) holds the goal, the state, an optional root: (where the work
actually lives, when not here), and the checks a ship rests on. Every
project is born with a local git history — no remote, ever, on machine
initiative (law 7). Lifecycle moves are code-minted events that say so on
their own face; `done` walks the provisional lane so the owner's next
arrival confirms it.
"""
import os
import shutil
import subprocess

from . import journal, provisional

DIRNAME = "projects"
CONTRACT = "PROJECT.md"
CANON = "CANON.md"


def dirpath(ws, name=None):
    base = os.path.join(ws, DIRNAME)
    return os.path.join(base, name) if name else base


def contract_path(ws, name):
    return os.path.join(dirpath(ws, name), CONTRACT)


def parse_contract(path):
    """Line-tolerant read of PROJECT.md. Unknown lines pass through."""
    out = {"name": None, "goal": "", "state": "active", "root": None, "checks": []}
    if not os.path.exists(path):
        return None
    section = None
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("# "):
                out["name"] = line[2:].strip()
            elif line.startswith("goal:"):
                out["goal"] = line[5:].strip()
            elif line.startswith("state:"):
                out["state"] = line[6:].strip()
            elif line.startswith("root:"):
                out["root"] = line[5:].strip() or None
            elif line.startswith("## "):
                section = line[3:].strip().lower()
            elif section == "checks" and line.strip() and not line.startswith("#"):
                out["checks"].append(line.strip())
    return out


def root_of(ws, name):
    """Where the work lives: root: if declared, else the project dir."""
    c = parse_contract(contract_path(ws, name))
    if c and c.get("root"):
        return os.path.abspath(os.path.expanduser(c["root"]))
    return dirpath(ws, name)


def _git_birth(path, name):
    """A local history at birth. No remote, ever. Fail-open with a plain line."""
    if shutil.which("git") is None:
        return "no git on this machine — the project stands without a history"
    subprocess.run(["git", "init", "--quiet", path], check=False)
    gi = os.path.join(path, ".gitignore")
    if not os.path.exists(gi):
        with open(gi, "w", encoding="utf-8") as f:
            f.write("__pycache__/\n.DS_Store\n")
    subprocess.run(["git", "-C", path, "add", "-A"], check=False)
    r = subprocess.run(["git", "-C", path, "commit", "--quiet", "-m", "born: %s" % name],
                       check=False, capture_output=True)
    return None if r.returncode == 0 else "git present but the birth commit failed — history starts at your first commit"


def new(ws, name, goal=""):
    """Create a project. Refuses to overwrite one that lives."""
    d = dirpath(ws, name)
    if os.path.exists(contract_path(ws, name)):
        return False, "a project named %s already lives here — nothing touched" % name
    os.makedirs(d, exist_ok=True)
    with open(contract_path(ws, name), "w", encoding="utf-8") as f:
        f.write("# %s\ngoal: %s\nstate: active\n\n## checks\n\n## notes\n" % (name, goal))
    with open(os.path.join(d, CANON), "w", encoding="utf-8") as f:
        f.write("# canon — %s\n\n*projected from the record; do not edit by hand.*\n" % name)
    git_note = _git_birth(d, name)
    journal.append(ws, {"op": "assert", "cls": "project-state", "origin": "machine",
                        "triggered": "session", "project": name,
                        "body": "born: %s" % name, "ink": "receipted",
                        "receipt": contract_path(ws, name)})
    msg = "project %s is born" % name
    if git_note:
        msg += " · " + git_note
    return True, msg


def _on_path(ws):
    return os.path.join(ws, journal.STATE_DIR, "on.json")


def on_list(ws):
    import json
    p = _on_path(ws)
    if not os.path.exists(p):
        return []
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def switch(ws, name, to_on):
    """The session switchboard, folded into the project verb (ruled 2026-07-30)."""
    import json
    if not os.path.exists(contract_path(ws, name)):
        return False, "no project named %s" % name
    cur = on_list(ws)
    if to_on and name not in cur:
        cur.append(name)
    if not to_on and name in cur:
        cur.remove(name)
    os.makedirs(os.path.dirname(_on_path(ws)), exist_ok=True)
    with open(_on_path(ws), "w", encoding="utf-8") as f:
        json.dump(cur, f)
    journal.append(ws, {"op": "assert", "cls": "project-state", "origin": "machine",
                        "triggered": "session", "project": name,
                        "body": ("on: %s" if to_on else "off: %s") % name,
                        "ink": "receipted", "receipt": _on_path(ws)})
    return True, ("%s is on — bare verbs land there" % name) if to_on else ("%s is off" % name)


def done(ws, name):
    """Closing a project rides the provisional lane: it happens now, and your
    next arrival confirms it (or puts it back with one key)."""
    cpath = contract_path(ws, name)
    c = parse_contract(cpath)
    if c is None:
        return False, "no project named %s" % name
    text = open(cpath, encoding="utf-8").read()
    new_text = text.replace("state: %s" % c["state"], "state: done", 1)
    provisional.act(ws, cpath, new_text, "project done: %s" % name, project=name)
    return True, "%s is done — provisional until your next arrival confirms it" % name


def list_all(ws):
    base = dirpath(ws)
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base)):
        c = parse_contract(contract_path(ws, name))
        if c:
            c["name"] = c["name"] or name
            c["dir"] = name
            out.append(c)
    return out
