# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Stop: the sweep — what the turn found, staged before it is forgotten.

It reads the transcript the host already wrote, keeps the lines the assistant
marked itself (`finding:`, `ruling:`, `correction:`) plus any `systemMessage`
the host's own hooks emitted, drops what is already waiting, and stages the
rest through `sandbox note`. Machine origin, so each one waits: the sweep
stages and the owner's key is what lands.

One line out when it staged something, silence when it did not, and never an
exit that stops a turn.
"""
import hashlib
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _shell  # noqa: E402

MARK = re.compile(r"^\s*(finding|ruling|correction)\s*:\s*(.+)$", re.I)
LONGEST = 400


def _digest(body):
    return hashlib.sha256(body.strip().encode("utf-8")).hexdigest()


def _assistant_text(row):
    """the assistant's own words in one transcript row, or ''."""
    if row.get("type") not in (None, "assistant"):
        return ""
    message = row.get("message")
    if not isinstance(message, dict) or message.get("role") != "assistant":
        return ""
    out = []
    content = message.get("content")
    if isinstance(content, str):
        out.append(content)
    for part in content or ():
        if isinstance(part, dict) and part.get("type") == "text":
            out.append(part.get("text") or "")
    return "\n".join(out)


def findings(rows):
    """[(kind, body)] — the marked lines, in the order the turn produced them."""
    out = []
    for row in rows:
        for line in _assistant_text(row).splitlines():
            m = MARK.match(line)
            if m:
                body = m.group(2).strip()
                if body and len(body) <= LONGEST:
                    out.append((m.group(1).lower(), body))
        said = row.get("systemMessage")
        if isinstance(said, str) and said.strip() and len(said.strip()) <= LONGEST:
            out.append(("finding", said.strip()))
    return out


def staged_form(kind, body):
    """the line as it will read on the record — and the thing de-dupe hashes,
    so a second sweep over the same turn compares like with like."""
    return "%s: %s" % (kind, body)


def fresh(found, already):
    """what the pile does not already hold, de-duplicated inside the turn too."""
    seen = {_digest(b) for b in already}
    out = []
    for kind, body in found:
        key = _digest(staged_form(kind, body))
        if key in seen:
            continue
        seen.add(key)
        out.append((kind, body))
    return out


def main():
    ev = _shell.event()
    ws = _shell.workshop(ev)
    found = fresh(findings(_shell.transcript(ev)), _shell.staged_bodies(ws))
    if not found:
        return 0
    name = _shell.project_of(ev.get("cwd") or os.getcwd(), ws)
    staged = 0
    for kind, body in found:
        args = ["note"]
        if kind == "ruling":
            args.append("--ruling")
        if name:
            args += ["--project", name]
        args.append(staged_form(kind, body))
        code, _out = _shell.sandbox(args, ws=ws)
        staged += 1 if code == 0 else 0
    if staged:
        # surfaces row 23: the count, and where they wait.
        print("%d finding%s staged — sandbox drafts"
              % (staged, "" if staged == 1 else "s"))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
