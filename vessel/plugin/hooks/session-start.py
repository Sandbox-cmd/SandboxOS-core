# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""SessionStart: one sentence about what waits, then the sitting opens.

Two things happen and no more. The needs sentence is folded from `sandbox
status` — one producer, and this is the one-line renderer of it — with every
door cut off, because the session shows and the verb lands (experience §4.1).
Then `sandbox session open --key <the host's session id>` puts the sitting on
the record, which is the only op a hook may mint.

The host's own fences are doctor's to report, never this line's; a person
asks for them with `sandbox doctor`.
"""
import json
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _shell  # noqa: E402


def sentence(text):
    """`sandbox status`'s sentence and rows, folded into one line.

    The rows carry their door (`— sandbox approve`); the sentence drops it,
    because a hook that names a verb it could run itself is inviting the one
    thing it may never do.
    """
    lines = [l.rstrip() for l in (text or "").splitlines() if l.strip()]
    if not lines:
        return ""
    head, rows = lines[0], []
    for line in lines[1:]:
        if not line.startswith("  "):
            break
        rows.append(line.strip().split(" — sandbox ")[0])
    if not rows:
        return head
    return "%s — %s" % (head.rstrip("."), " · ".join(rows))


def main():
    ev = _shell.event()
    ws = _shell.workshop(ev)
    _code, out = _shell.sandbox(["status"], ws=ws)
    line = sentence(out)
    key = ev.get("session_id") or ""
    if key:
        _shell.sandbox(["session", "open", "--key", key], ws=ws)
    if line:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "SessionStart", "additionalContext": line}}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # a fence that crashes a session is worse than a fence that says
        # nothing: fail open, exactly as the guard does (R7).
        sys.exit(0)
