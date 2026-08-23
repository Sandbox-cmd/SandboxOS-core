# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""projects: where the making happens.

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

from . import desk, journal, provisional

DIRNAME = "projects"
CONTRACT = "PROJECT.md"
CANON = "CANON.md"
BRIEFS = ("AGENTS.md", "CLAUDE.md")

# the one line under `## checks`, so an empty section says what belongs in
# it: the alternative is the section a ship finds empty weeks later, and
# "a ship with nothing under it is a costume" is that scar already named.
CHECKS_HINT = "<!-- one command per line; sandbox ship runs them -->"

# the header both canon writers put at the top of a projected page. the
# prohibition carries its reason and its door, so a person who edited the
# page by hand reads what happens to their words and where to put them.
# surface: 8
CANON_HEADER = ("*projected from the record — edits here are "
                "lost on the next rebuild; change the record with sandbox note.*")

# what a project's own root gets when the work lives outside the workshop:
# one page under the two names a session looks for. twelve lines, because a
# page nobody finishes reading is a page that governs nothing.
ROOT_BRIEF = """# %(name)s

this directory is where the %(name)s project's work lives. its contract —
the goal, the state, and the checks a ship runs — is PROJECT.md, under the
workshop at projects/%(name)s/.

the record: `sandbox status` says what waits, `sandbox recall` says what is
already known, and `sandbox note "..."` stages a finding in the owner's own
words. a staged note lands on the owner's key.

this page only says which project you are standing in; the page that governs
a session here is the charter at %(charter)s.
"""


def dirpath(ws, name=None):
    base = os.path.join(ws, DIRNAME)
    return os.path.join(base, name) if name else base


def contract_path(ws, name):
    return os.path.join(dirpath(ws, name), CONTRACT)


def standing_in(ws):
    """the project whose directory the caller is standing in, or None.

    The sh door never cd's, so the working directory is load-bearing: a bare
    verb typed inside projects/NAME/ binds to NAME (scar 07-19, a note landed
    on the wrong project because "the single on-project" was the only rule).
    """
    try:
        here = os.path.realpath(os.getcwd())
    except OSError:
        return None
    base = os.path.realpath(dirpath(ws))
    if not here.startswith(base + os.sep):
        return None
    name = here[len(base) + 1:].split(os.sep)[0]
    return name if os.path.isdir(os.path.join(base, name)) else None


def parse_contract(path):
    """line-tolerant read of PROJECT.md. Unknown lines pass through."""
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
            elif (section == "checks" and line.strip()
                  and not line.startswith(("#", "<!--"))):
                # the hint line under `## checks` is an html comment, and a
                # comment is not a command: a parser that read it would hand
                # `sandbox ship` a line no shell can run.
                out["checks"].append(line.strip())
    return out


def root_of(ws, name):
    """where the work lives: root: if declared, else the project dir."""
    c = parse_contract(contract_path(ws, name))
    if c and c.get("root"):
        return os.path.abspath(os.path.expanduser(c["root"]))
    return dirpath(ws, name)


def _git_birth(path, name):
    """a local history at birth. No remote, ever. Fail-open with a plain line."""
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


def _tilde(p):
    """a path with the owner's home written as `~` — law 13's habit, kept
    for a file that may sit in a repo that travels."""
    home = os.path.expanduser("~")
    if p == home or p.startswith(home + os.sep):
        return "~" + p[len(home):]
    return p


def write_briefs(ws, name, root):
    """AGENTS.md and CLAUDE.md on a project's own root. Returns report lines.

    A root outside the workshop is a directory a stranger — or a model —
    opens with no idea which project it is or where its record lives. Both
    names are written, because both are looked for, and the body is one
    template. A root that already carries one keeps it: a page someone else
    wrote is theirs, and this is not the hand that edits it.
    """
    if os.path.realpath(root) == os.path.realpath(ws):
        return []  # the charter is already here; a second copy of it is noise
    text = ROOT_BRIEF % {"name": name,
                         "charter": _tilde(os.path.join(os.path.abspath(ws),
                                                        "CLAUDE.md"))}
    wrote, kept = [], []
    for fname in BRIEFS:
        p = os.path.join(root, fname)
        if os.path.exists(p):
            kept.append(fname)
            continue
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        wrote.append(fname)
    lines = []
    if wrote:
        # surface: 7
        lines.append("wrote %s on the root — what this project is, and where "
                     "its record lives" % " and ".join(wrote))
    if kept:
        # surface: 3a
        lines.append("%s already lives on that root — left as it is, and "
                     "nothing overwritten" % " and ".join(kept))
    return lines


def new(ws, name, goal="", root=None):
    """create a project. Refuses to overwrite one that lives.

    `root` is where the work actually lives when it is not the project
    directory: the contract carries it as `root:`, and the two briefs are
    written there so the directory says what it belongs to.
    """
    d = dirpath(ws, name)
    if os.path.exists(contract_path(ws, name)):
        return False, "a project named %s already lives here — nothing touched" % name
    root_abs = os.path.abspath(os.path.expanduser(root)) if root else None
    if root_abs and not os.path.isdir(root_abs):
        return False, ("no directory at %s — make it first, then: "
                       "sandbox project new %s --root %s" % (root_abs, name, root))
    os.makedirs(d, exist_ok=True)
    with open(contract_path(ws, name), "w", encoding="utf-8") as f:
        f.write("# %s\ngoal: %s\nstate: active\n" % (name, goal))
        if root_abs:
            f.write("root: %s\n" % root_abs)
        f.write("\n## checks\n%s\n\n## notes\n" % CHECKS_HINT)
    with open(os.path.join(d, CANON), "w", encoding="utf-8") as f:
        f.write("# canon — %s\n\n%s\n" % (name, CANON_HEADER))
    brief_lines = write_briefs(ws, name, root_abs) if root_abs else []
    git_note = _git_birth(d, name)
    desk.mint(ws, {"cls": "project-state", "origin": "machine",
                   "triggered": "session", "project": name,
                   "body": "born: %s" % name,
                   "receipt": contract_path(ws, name)})
    msg = "project %s is born" % name
    if git_note:
        msg += " · " + git_note
    for line in brief_lines:
        msg += "\n" + line
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
    """the session switchboard, folded into the project verb (ruled 2026-07-30)."""
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
    desk.mint(ws, {"cls": "project-state", "origin": "machine",
                   "triggered": "session", "project": name,
                   "body": ("on: %s" if to_on else "off: %s") % name,
                   "receipt": _on_path(ws)})
    return True, ("%s is on — bare verbs land there" % name) if to_on else ("%s is off" % name)


def done(ws, name):
    """closing a project rides the provisional lane: it happens now, and your
    next arrival confirms it (or puts it back with one key)."""
    cpath = contract_path(ws, name)
    c = parse_contract(cpath)
    if c is None:
        return False, "no project named %s" % name
    with open(cpath, encoding="utf-8") as f:
        text = f.read()
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
