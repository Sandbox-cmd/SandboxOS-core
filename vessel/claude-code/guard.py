# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The guard: the workshop's wall, spoken before the desk ever has to.

A PreToolUse hook, self-contained (no engine import — it runs wherever init
placed it). Four fences, each with a door named in its refusal:

1. The record (`.sandbox/`) — no write touches it, and no shell command may
   even NAME it. Substring matching is deliberate and documented: permission
   rules cannot match Bash command content, so this hook is the one
   mechanism that can hold this line.
2. Auto-memory — durable memory lands on the owner's key, so a direct write
   to the harness's memory directory is turned back to the staged-note path
   (this IS the routing the ruling asked for).
3. Cross-project — a session standing in one project does not write into
   another's directory.
4. The core tree — sessions in the workshop don't edit the engine; tool work
   happens in the tool's own repo with its own covenant.

Always exits 0; malformed input passes (fail-open, honest about being a
fence, not a wall).
"""
import json
import os
import sys

STATE = ".sandbox"
WRITE_TOOLS = ("Write", "Edit", "MultiEdit", "NotebookEdit")


def _engine_root():
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "engine-root")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            return f.read().strip()
    return None


def _deny(reason):
    return {"hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def _project_of(path, ws):
    """projects/<name>/... → name, else None."""
    if not ws:
        return None
    pdir = os.path.join(ws, "projects") + os.sep
    ap = os.path.abspath(path)
    if ap.startswith(pdir):
        rest = ap[len(pdir):]
        return rest.split(os.sep, 1)[0] or None
    return None


def decide(event, ws=None, cwd=None):
    tool = event.get("tool_name", "")
    args = event.get("tool_input") or {}
    ws = ws or os.environ.get("SANDBOX_HOME") or os.path.join(os.path.expanduser("~"), "Sandbox")
    cwd = cwd or event.get("cwd") or os.getcwd()

    if tool in WRITE_TOOLS:
        path = args.get("file_path") or args.get("notebook_path") or ""
        parts = os.path.abspath(path).split(os.sep)
        if STATE in parts:
            return _deny("the wall held — your record is the desk's pen. propose it: sandbox note")
        ap = os.path.abspath(path)
        if (os.sep + ".claude" + os.sep) in ap and (os.sep + "memory" + os.sep) in ap:
            return _deny("durable memory lands on the owner's key — stage it instead: sandbox note")
        target_proj = _project_of(ap, ws)
        cwd_proj = _project_of(cwd, ws)
        if target_proj and cwd_proj and target_proj != cwd_proj:
            return _deny("you are standing in %s — %s is another project's room. "
                         "switch projects or say why on the record" % (cwd_proj, target_proj))
        root = _engine_root()
        if root and ap.startswith(os.path.abspath(root) + os.sep):
            return _deny("the engine is edited in its own repo with its own covenant — "
                         "not from a workshop session")

    if tool == "Bash":
        command = args.get("command", "")
        if STATE in command:
            return _deny("the wall held — that command names the record. propose it: sandbox note")

    return {}


def main():
    try:
        event = json.load(sys.stdin)
    except Exception:
        print("{}")
        return 0
    try:
        out = decide(event)
    except Exception:
        out = {}
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
