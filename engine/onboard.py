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

WRITE_TOOLS = ("Edit", "Write", "MultiEdit", "NotebookEdit")


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _vessel_src():
    return os.path.join(_repo_root(), "vessel", "claude-code")


def deny_floor_rules(ws):
    state = os.path.join(os.path.abspath(ws), journal.STATE_DIR)
    return ["%s(//%s/**)" % (tool, state.lstrip("/")) for tool in WRITE_TOOLS]


def _settings_path(ws):
    return os.path.join(ws, ".claude", "settings.json")


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
    if not _wired(pre):
        pre.append({"matcher": "|".join(WRITE_TOOLS) + "|Bash",
                    "hooks": [{"type": "command", "command": guard_cmd}]})
        lines.append("wired: the guard on every write tool and bash")

    perms = settings.setdefault("permissions", {})
    deny = perms.setdefault("deny", [])
    for rule in deny_floor_rules(ws):
        if rule not in deny:
            deny.append(rule)
    lines.append("deny floor: %d rule(s) on the record's directory" % len(deny_floor_rules(ws)))

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
    src = _vessel_src()
    vdir = os.path.join(ws, journal.STATE_DIR, "vessel")
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, "engine-root"), "w", encoding="utf-8") as f:
        f.write(_repo_root())
    payload = {
        os.path.join(ws, "CLAUDE.md"): os.path.join(src, "CLAUDE.md"),
        os.path.join(vdir, "guard.py"): os.path.join(src, "guard.py"),
    }
    for line in placement.sync(ws, payload):
        lines.append(line)

    ok, wire_lines = emit_settings(ws)
    lines.extend(wire_lines)
    if not alive:
        lines.append("ready. nobody's tool.")
    return ok, "\n".join(lines)
