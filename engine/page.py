# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The living page: the workshop rendered as one self-contained file.

Zero server, zero dependencies, zero external requests — the page is a
local render of local state, every element backed by a live state read, and
it wears its "as of" because a mirror that hides its age is a mirror that
lies. Regenerate on demand: `sandbox page`.
"""
import html
import os

from . import desk, journal, project, provisional


def render(ws):
    events, scars = journal.read(ws)
    projects = project.list_all(ws)
    pile, _ = desk.drafts(ws)
    waiting = provisional.pending(ws)
    on = project.on_list(ws)

    rows = []
    for p in projects:
        mark = " on" if p["dir"] in on else ""
        rows.append("<tr><td>%s%s</td><td>%s</td><td>%s</td></tr>" %
                    (html.escape(p["dir"]), mark, html.escape(p["state"]),
                     html.escape(p["goal"])))
    recent = []
    for e in events[-8:]:
        recent.append("<li><code>%s</code> %s</li>" %
                      (html.escape(e.get("op", "")),
                       html.escape((e.get("body") or "")[:90])))

    needs = []
    if pile:
        needs.append("%d draft(s) wait on your key" % len(pile))
    if waiting:
        needs.append("%d provisional act(s) await your confirm" % len(waiting))
    if scars:
        needs.append("%d torn line(s) on the record — doctor has details" % len(scars))
    needs_line = " · ".join(needs) if needs else "nothing needs you."

    doc = """<!doctype html>
<meta charset="utf-8">
<title>the workshop</title>
<style>
 body { font-family: ui-monospace, monospace; max-width: 44rem; margin: 3rem auto;
        padding: 0 1rem; line-height: 1.5; background: #111; color: #ddd; }
 h1 { font-size: 1.1rem; letter-spacing: .2em; }
 table { border-collapse: collapse; width: 100%%; }
 td { padding: .2rem .6rem .2rem 0; border-bottom: 1px solid #333; }
 .needs { border: 1px solid #555; padding: .6rem 1rem; margin: 1rem 0; }
 .asof { color: #777; font-size: .85rem; }
 code { color: #9c9; }
</style>
<h1>THE WORKSHOP</h1>
<p class="needs">%s</p>
<table>%s</table>
<h2>lately, on the record</h2>
<ul>%s</ul>
<p class="asof">as of %s — a local render of local state; regenerate with: sandbox page</p>
""" % (html.escape(needs_line), "".join(rows), "".join(recent), journal.now())
    out = os.path.join(ws, "page.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(doc)
    return out
