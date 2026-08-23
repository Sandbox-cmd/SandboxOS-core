# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""SessionEnd: close the sitting, and say which seats it used.

The counts come off the transcript the host already wrote — one per `Agent`
or `Task` call, keyed by the seat that was asked for — so doctor can say
`crew: 6 seat(s) on the record, 2 used in 30 days` from events rather than
from a guess. `sandbox session close` is the only verb this hook calls, and
it mints the one op a hook is allowed to mint.
"""
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _shell  # noqa: E402

AGENT_TOOLS = ("Agent", "Task")


def agent_counts(rows):
    """{seat: how many times it was called} from the transcript's tool uses."""
    out = {}
    for row in rows:
        content = ((row.get("message") or {}).get("content")
                   if isinstance(row.get("message"), dict) else None)
        for part in content or ():
            if not isinstance(part, dict) or part.get("type") != "tool_use":
                continue
            if part.get("name") not in AGENT_TOOLS:
                continue
            seat = (part.get("input") or {}).get("subagent_type") or "unnamed"
            seat = str(seat).replace(",", " ").replace("=", " ").strip()
            if seat:
                out[seat] = out.get(seat, 0) + 1
    return out


def main():
    ev = _shell.event()
    ws = _shell.workshop(ev)
    key = ev.get("session_id") or ""
    if not key:
        return 0
    args = ["session", "close", "--key", key]
    counts = agent_counts(_shell.transcript(ev))
    if counts:
        args += ["--agents", ",".join("%s=%d" % (k, counts[k])
                                      for k in sorted(counts))]
    _shell.sandbox(args, ws=ws)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
