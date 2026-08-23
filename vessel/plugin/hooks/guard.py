# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the guard: four fences a session meets before a tool ever runs.

a PreToolUse hook, stdlib only and self-contained — it runs from wherever the
host loaded the plugin, so it imports no engine module. four fences, each
refusal naming the door out of it:

1. the record (`.sandbox/`) — it takes writes through a verb and a key, so a
   write into it is turned back to `sandbox note`.
2. durable memory — `~/.claude/**/memory/**` and `.claude/agent-memory`: what
   a session wants to remember lands on the owner's k, or it is a second
   record nobody reads.
3. cross-project — a session sitting in one project does not write into
   another's directory.
4. the system tree — the tool is edited in its own repo, on a branch, with
   its own checks; it is derived from `${CLAUDE_PLUGIN_ROOT}/../..` and never
   from a pointer file a workshop could carry stale.

the Bash branch reads write INTENT, never a bare mention: `cat`, `grep`,
`ls`, `head`, `tail`, `wc` and `git log` over the record all pass, and only a
command carrying a write form (`>`, `tee`, `sed -i`, `rm`, `mv`, `cp`,
`truncate`, `mkdir`, `touch`, `chmod`, a python heredoc) over a fenced path
is turned back. the 8.2.3 scar is that fence's opposite: a substring match
blocked reading the record at all.

on a deny it prints the host's block decision on stdout and exits 2 with the
refusal on stderr — both shapes, so whichever the host honors, it holds. any
exception at all exits 0 and allows: fail-open is the ruling (R7), and the
honest posture for a fence that is not a wall.
"""
import json
import os
import re
import sys

STATE = ".sandbox"
WRITE_TOOLS = ("Write", "Edit", "NotebookEdit")
AGENT_MEMORY = os.sep + ".claude" + os.sep + "agent-memory"

# surface: 3c
# the six refusals. each opens differently, says what stopped, and names the
# one door out — a reader mid-mistake reads the first clause and the last.
RECORD_WRITE = ("i keep the record for the verbs that write it. "
                "stage this instead: sandbox note")
MEMORY_WRITE = ("memory lands on your k, so i turned that write back. "
                "stage it instead: sandbox note")
AGENT_MEMORY_WRITE = ("agent memory is a second record no one audits — i stopped "
                      "that write. put it in your report, or stage it: sandbox note")
CROSS_PROJECT = ("you are sitting in %s, so i left that write in %s alone. "
                 "switch first: sandbox project")
SYSTEM_TREE = ("the system tree keeps its own repo and checks, and i hold you "
               "to them — edit it in ~/Sandbox/system on a branch")
RECORD_COMMAND = ("that command writes the record, and i keep it for the verbs — "
                  "reading is free; change it with: sandbox note")

# a write form: the shapes a shell command takes when it means to change a
# file. a redirect is read after `->`, `=>`, `>=` and `2>&1` are taken out, so
# a comparison or an arrow in a message is not read as one.
_ARROWS = re.compile(r"->|=>|>=|2>&1")
WRITE_FORMS = (
    re.compile(r"\btee\b"),
    re.compile(r"\bsed\b[^|;&]*\s-{1,2}i(?:\b|\s|')"),
    re.compile(r"\b(rm|mv|cp|install|ln|dd|truncate|mkdir|touch|chmod|chown)\b"),
    re.compile(r"\bpython3?\b[^|;&]*<<"),
    re.compile(r"\b(cat|printf|echo)\b[^|;&]*<<"),
)


def _system_tree(root=None):
    """the tree this plugin ships inside: two directories above the root.

    the host hands the plugin its own directory, so the answer is derived and
    cannot go stale; with the variable absent, this file's own path says the
    same thing.
    """
    root = root or os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))
    return os.path.dirname(os.path.dirname(os.path.abspath(root)))


def _deny(reason):
    """both shapes of a block, in one object: the decision the host reads on
    stdout, and the reason `main` writes to stderr under exit 2."""
    return {"decision": "block",
            "reason": reason,
            "hookSpecificOutput": {"hookEventName": "PreToolUse",
                                   "permissionDecision": "deny",
                                   "permissionDecisionReason": reason}}


def _project_of(path, ws):
    """projects/<name>/… → name, else None."""
    if not ws:
        return None
    pdir = os.path.join(os.path.abspath(ws), "projects") + os.sep
    ap = os.path.abspath(path)
    if ap.startswith(pdir):
        rest = ap[len(pdir):]
        return rest.split(os.sep, 1)[0] or None
    return None


def writes(command):
    """true when a shell command carries a form that changes a file."""
    stripped = _ARROWS.sub(" ", command or "")
    if ">" in stripped:
        return True
    return any(rx.search(stripped) for rx in WRITE_FORMS)


def names_the_record(command):
    return STATE in (command or "")


def names_agent_memory(command):
    text = (command or "").replace("\\", "/")
    return ".claude/agent-memory" in text or "/agent-memory/" in text


def decide(event, ws=None, cwd=None, root=None):
    tool = event.get("tool_name", "")
    args = event.get("tool_input") or {}
    ws = ws or os.environ.get("SANDBOX_HOME") or os.path.join(
        os.path.expanduser("~"), "Sandbox")
    cwd = cwd or event.get("cwd") or os.getcwd()

    if tool in WRITE_TOOLS:
        path = args.get("file_path") or args.get("notebook_path") or ""
        ap = os.path.abspath(path)
        if STATE in ap.split(os.sep):
            return _deny(RECORD_WRITE)
        if (os.sep + ".claude" + os.sep) in ap and (os.sep + "memory" + os.sep) in ap:
            return _deny(MEMORY_WRITE)
        if AGENT_MEMORY in ap:
            return _deny(AGENT_MEMORY_WRITE)
        here = _project_of(cwd, ws)
        there = _project_of(ap, ws)
        if here and there and here != there:
            return _deny(CROSS_PROJECT % (here, there))
        tree = _system_tree(root)
        if tree and ap.startswith(os.path.abspath(tree) + os.sep):
            return _deny(SYSTEM_TREE)

    if tool == "Bash":
        command = args.get("command", "")
        if writes(command):
            if names_agent_memory(command):
                return _deny(AGENT_MEMORY_WRITE)
            if names_the_record(command):
                return _deny(RECORD_COMMAND)

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
    reason = out.get("reason")
    if reason:
        sys.stderr.write(reason + "\n")
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
