# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""init — open the workshop, place the vessel, wire the settings, read back.

Creates what is absent and touches nothing that lives: re-running init over
a living workshop says so and only re-syncs the vessel (placement provenance
decides what may refresh). Exactly two hand jobs live here beside the plugin
payload: placing the contract CLAUDE.md, and merging the permissions deny
floor + hook wiring into the workshop's settings — then reading the file
back to prove the wiring took.
"""
import json
import os

from . import journal, placement, project, status

# The hook matcher is a regex over live tool names. MultiEdit is retired.
WRITE_TOOLS = ("Edit", "Write", "NotebookEdit")

# The deny floor is matched on Edit() alone — Edit(path) covers every
# file-editing tool. A Write()/NotebookEdit() path rule matches nothing and
# Claude Code warns about it at every launch.
DENY_TOOLS = ("Edit",)


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _vessel_src():
    return os.path.join(_repo_root(), "vessel", "claude-code")


def deny_floor_target(ws):
    """The tail every deny-floor rule shares: the record's directory."""
    state = os.path.join(os.path.abspath(ws), journal.STATE_DIR)
    return "(//%s/**)" % state.lstrip("/")


def deny_floor_rules(ws):
    return ["%s%s" % (tool, deny_floor_target(ws)) for tool in DENY_TOOLS]


def _settings_path(ws):
    return os.path.join(ws, ".claude", "settings.json")


STYLE_FILE = "across-the-desk.md"


def shipped_payload(ws):
    """Everything init places, as {dest: src}. One source for run(), the
    reset verb, and the layer tests — a hand-typed second list would drift."""
    src = _vessel_src()
    vdir = os.path.join(ws, journal.STATE_DIR, "vessel")
    payload = {
        os.path.join(ws, "CLAUDE.md"): os.path.join(src, "CLAUDE.md"),
        os.path.join(vdir, "guard.py"): os.path.join(src, "guard.py"),
    }
    agents_src = os.path.join(src, "agents")
    if os.path.isdir(agents_src):
        for name in sorted(os.listdir(agents_src)):
            payload[os.path.join(ws, ".claude", "agents", name)] = \
                os.path.join(agents_src, name)
    style_src = os.path.join(_repo_root(), "vessel", "plugin",
                             "output-styles", STYLE_FILE)
    if os.path.exists(style_src):
        payload[os.path.join(ws, ".claude", "output-styles", STYLE_FILE)] = style_src
    return payload


def emit_settings(ws):
    """Merge hooks + deny floor. Returns (ok, report_lines)."""
    lines = []
    sp = _settings_path(ws)
    os.makedirs(os.path.dirname(sp), exist_ok=True)
    settings = {}
    if os.path.exists(sp):
        try:
            with open(sp, encoding="utf-8") as f:
                settings = json.load(f)
        except ValueError:
            return False, ["settings.json would not parse — fix it by hand, nothing touched"]

    guard_cmd = 'python3 "%s"' % os.path.join(ws, journal.STATE_DIR, "vessel", "guard.py")

    def _wired(entries):
        return any(hk.get("command") == guard_cmd
                   for h in entries for hk in h.get("hooks", []))

    hooks = settings.setdefault("hooks", {})
    pre = hooks.setdefault("PreToolUse", [])

    # Prune hooks whose placed script is gone (a workshop that moved leaves
    # dead absolute paths behind — the seventh body's scar, met again by the
    # eighth on its own migration day).
    import re as _re
    pruned = 0
    for entry in list(pre):
        for hk in entry.get("hooks", []):
            m = _re.search(r'"([^"]*guard\.py)"', hk.get("command", ""))
            if m and not os.path.exists(m.group(1)):
                pre.remove(entry)
                pruned += 1
                break
    if pruned:
        lines.append("pruned %d hook(s) pointing at gone paths" % pruned)

    if not _wired(pre):
        pre.append({"matcher": "|".join(WRITE_TOOLS) + "|Bash",
                    "hooks": [{"type": "command", "command": guard_cmd}]})
        lines.append("wired: the guard on every write tool and bash")

    perms = settings.setdefault("permissions", {})
    deny = perms.setdefault("deny", [])

    # Prune rules on the record's directory that name a tool the floor no
    # longer emits — a workshop onboarded under an older floor carries them
    # forever otherwise, and Claude Code warns once per dead name at every
    # launch. Same scar as the hooks above: append-only wiring never heals.
    floor = deny_floor_rules(ws)
    tail = deny_floor_target(ws)
    stale = [r for r in deny if r.endswith(tail) and r not in floor]
    for rule in stale:
        deny.remove(rule)
    if stale:
        lines.append("pruned %d dead deny rule(s) on the record's directory" % len(stale))

    for rule in floor:
        if rule not in deny:
            deny.append(rule)
    lines.append("deny floor: %d rule(s) on the record's directory" % len(floor))

    # The shipped voice, on by default — the owner's own setting always wins:
    # setdefault never touches an existing choice, and settings.local.json
    # (what /config writes) outranks this file anyway.
    if settings.setdefault("outputStyle", STYLE_FILE[:-3]) == STYLE_FILE[:-3]:
        lines.append("voice: %s is the session style unless you pick another" % STYLE_FILE[:-3])

    with open(sp, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=1)

    # Read-back: the wiring took, or we say READ-BACK FAILED out loud.
    with open(sp, encoding="utf-8") as f:
        back = json.load(f)
    ok = (_wired(back.get("hooks", {}).get("PreToolUse", []))
          and all(r in back.get("permissions", {}).get("deny", [])
                  for r in deny_floor_rules(ws)))
    lines.append("read-back: %s" % ("the wiring took" if ok else "READ-BACK FAILED"))
    return ok, lines


def run(ws):
    """The whole of init. Returns (ok, text)."""
    lines = []
    alive = os.path.exists(journal.path(ws)) and os.path.getsize(journal.path(ws)) > 0
    if alive:
        lines.append("workshop alive at %s — nothing that lives is touched." % ws)
    else:
        os.makedirs(os.path.join(ws, project.DIRNAME), exist_ok=True)
        journal.ensure_genesis(ws)
        status.play(ws)  # the playground exists from birth
        lines.append("opened your workshop at %s" % ws)
        lines.append("day 0. nothing on the record yet.")

    # The vessel: contract at the root, guard beside the record, engine-root pointer.
    vdir = os.path.join(ws, journal.STATE_DIR, "vessel")
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, "engine-root"), "w", encoding="utf-8") as f:
        f.write(_repo_root())
    payload = shipped_payload(ws)
    for line in placement.sync(ws, payload):
        lines.append(line)

    ok, wire_lines = emit_settings(ws)
    lines.extend(wire_lines)
    from . import update
    update.record_version(ws)
    if not alive:
        lines.append("ready. nobody's tool.")
    return ok, "\n".join(lines)
