# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the page: the export's html form, and nothing more (ruled 2026-08-22).

zero server, zero dependencies, zero requests — one local file holding the
same lines `sandbox export` writes, escaped field by field. it stopped being
a second reading of workshop state the day the ruling landed: what a page
shows is the record, and `sandbox status` is where live state is read.

one design rule, and it is age: a line's contrast comes from its place in the
span, newest at full strength and oldest dimmest, so a page's shape says how
old its subject is before a word of it is read.
"""
import html


def render(rows, head, round_trip, footer):
    """the same lines as one self-contained file. returns the html text."""
    span = max(len(rows) - 1, 1)
    body = []
    for i, r in enumerate(rows):
        age = "%.3f" % (i / span)
        hand = " [%s]" % html.escape(r["hand"]) if r.get("hand") else ""
        body.append(
            '<li class="l" style="--age:%s"><code>%s</code> [%s] [%s]%s %s '
            '%s <span class="r">%s</span></li>'
            % (age, html.escape(r["ts"]), html.escape(r["ink"]),
               html.escape(r["origin"]), hand, html.escape(r["kind"]),
               html.escape(r["body"]), html.escape(r["receipt"])))
    title = head[0].lstrip("# ").strip()
    return """<!doctype html>
<meta charset="utf-8">
<title>%s</title>
<style>
 body { font-family: ui-monospace, monospace; max-width: 60rem; margin: 3rem auto;
        padding: 0 1rem; line-height: 1.5; background: #111; color: #ddd; }
 h1 { font-size: 1rem; letter-spacing: .15em; font-weight: normal; }
 ul { list-style: none; padding: 0; }
 .l { opacity: calc(.35 + .65 * var(--age)); overflow-wrap: anywhere; }
 .r { color: #7a8; }
 .foot { border-top: 1px solid #333; padding-top: 1rem; }
</style>
<h1>%s</h1>
<p>%s</p>
<ul>%s</ul>
<div class="foot">
<p>%s</p>
<p>%s</p>
</div>
""" % (html.escape(title), html.escape(title),
       html.escape("\n".join(head[1:]).strip()), "".join(body),
       "</p>\n<p>".join(html.escape(s) for s in round_trip),
       html.escape(footer))
