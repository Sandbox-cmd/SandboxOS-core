# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the vessel: what the plugin ships, and the crew rendered from one source.

The plugin under `vessel/plugin/` is the whole of what a Claude Code session
loads — the four hooks, six briefs, three skills, the style, two commands.
Two jobs live here. `payload()` is the manifest: every file that ships, where
each hook command resolves, and the one file init still places by hand — read
by doctor and by onboard so no second list can drift from it. `render_crew()`
writes the six briefs from `crew.json` plus one `crew-tail.md`, so the tail a
seat shares with five others is written once instead of six times; a brief
edited by hand is a red check rather than a quiet drift.

Runnable: `python3 -m engine.vessel --build` rewrites the briefs.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN = os.path.join(ROOT, "vessel", "plugin")
CHARTER = os.path.join(ROOT, "vessel", "claude-code", "CLAUDE.md")

BLOCK = "<!-- block: "


# --- the manifest -----------------------------------------------------------

def hook_commands():
    """[(event, matcher, command)] — every wiring in the plugin's hooks.json.

    The 07-31 scar is a path: a hook one directory above the plugin root read
    as a block and denied every write. So the commands are read here from the
    file itself, and the test that walks them resolves each one inside the
    root rather than trusting the shape.
    """
    p = os.path.join(PLUGIN, "hooks", "hooks.json")
    try:
        with open(p, encoding="utf-8") as f:
            wiring = json.load(f).get("hooks", {})
    except (OSError, ValueError):
        return []
    out = []
    for event in sorted(wiring):
        for entry in wiring[event] or ():
            for hook in entry.get("hooks", []) or ():
                out.append((event, entry.get("matcher"), hook.get("command", "")))
    return out


def plugin_files():
    """every file under vessel/plugin/, workshop-relative, sorted."""
    out = []
    for dirpath, dirnames, filenames in os.walk(PLUGIN):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for name in filenames:
            full = os.path.join(dirpath, name)
            out.append(os.path.relpath(full, PLUGIN).replace(os.sep, "/"))
    return sorted(out)


def payload():
    """the manifest of what ships and where — one source for doctor and init.

    `ships` is what the host loads out of the plugin directory; `places` is
    the short list init still copies into the workshop by hand, and since 9.0
    that list is one file: the contract. The hooks, the six briefs, the three
    skills, the style and the two commands are loaded from the plugin, so
    nothing here is a second list — both sides are read off the tree that ships.
    """
    return {"root": PLUGIN,
            "ships": plugin_files(),
            "places": [CHARTER],
            "hooks": hook_commands()}


def agents_dir():
    return os.path.join(PLUGIN, "agents")


# --- the crew, rendered -----------------------------------------------------

def _crew():
    with open(os.path.join(PLUGIN, "crew.json"), encoding="utf-8") as f:
        return json.load(f)


def _tail():
    """crew-tail.md split into its named blocks."""
    with open(os.path.join(PLUGIN, "crew-tail.md"), encoding="utf-8") as f:
        text = f.read()
    blocks, name, held = {}, None, []
    for line in text.splitlines():
        if line.startswith(BLOCK):
            if name:
                blocks[name] = "\n".join(held).strip("\n")
            name = line[len(BLOCK):].split("-->")[0].strip()
            held = []
            continue
        if line.startswith("<!--"):
            continue
        if name is not None:
            held.append(line)
    if name:
        blocks[name] = "\n".join(held).strip("\n")
    return blocks


WIDTH = 79


def _wrapped(text, first, rest):
    """one entry, wrapped to the width the briefs are written at."""
    import textwrap
    return textwrap.wrap(text, width=WIDTH, initial_indent=first,
                         subsequent_indent=rest, break_long_words=False,
                         break_on_hyphens=False)


def _listed(rows):
    out = []
    for entry in rows:
        out += _wrapped(entry, "- ", "  ")
    return out


def _indented(rows):
    return ["    " + line if line else "" for line in rows]


def render_seat(seat, tail):
    """one brief, whole. the frontmatter the host reads, then the seat, then
    the tail every seat shares."""
    out = ["---",
           "name: %s" % seat["seat"],
           "description: %s. %s." % (seat["is"], seat["when"]),
           "tools: %s" % ", ".join(seat["tools"]),
           "model: %s" % seat["model"],
           "effort: %s" % seat["effort"],
           "---", ""]
    for block in seat["sections"]:
        out.append("## " + block["heading"])
        out += block["lines"]
        out.append("")
    out.append("## outside this seat, and why")
    out += _listed(seat["outside"])
    out.append("")
    answer = seat["answer"]
    out.append("## how you answer")
    out.append("")
    out += _indented(answer["shape"])
    if answer.get("note"):
        out.append("")
        out += answer["note"]
    out.append("")
    # surface: 19
    out.append("filled, so the shape reads as a report rather than a slot list:")
    out.append("")
    out += _indented(answer["example"])
    out.append("")
    out.append("## the two convictions you carry")
    for c in seat["convictions"]:
        out += _wrapped("**%s.** %s" % (c["name"], c["text"]), "- ", "  ")
    out.append("")
    out.append("## check your answer before you send it")
    out += _listed(seat["before_send"])
    out.append("")
    out.append(tail["report"])
    out.append("")
    out.append(tail[seat["records"]])
    return "\n".join(out).rstrip("\n") + "\n"


def render_crew():
    """{filename: text} for all six briefs — computed, never read off disk."""
    tail = _tail()
    return {"%s.md" % s["seat"]: render_seat(s, tail) for s in _crew()["seats"]}


def write_crew():
    """rewrite the briefs on disk. Returns the files it wrote."""
    adir = agents_dir()
    os.makedirs(adir, exist_ok=True)
    written = []
    for name, text in sorted(render_crew().items()):
        p = os.path.join(adir, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        written.append(p)
    return written


def hand_edited():
    """the briefs on disk that differ from what crew.json renders."""
    adir = agents_dir()
    out = []
    for name, text in sorted(render_crew().items()):
        p = os.path.join(adir, name)
        try:
            with open(p, encoding="utf-8") as f:
                same = f.read() == text
        except OSError:
            same = False
        if not same:
            out.append(name)
    return out


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--build" in argv:
        for p in write_crew():
            print("wrote: %s" % os.path.relpath(p, ROOT))
        return 0
    drifted = hand_edited()
    # surface: 24
    for name in drifted:
        print("hand-edited: %s — rebuild it: python3 -m engine.vessel --build"
              % name)
    print("plugin: %d file(s), %d hook command(s), %d brief(s) generated"
          % (len(plugin_files()), len(hook_commands()), len(render_crew())))
    return 1 if drifted else 0


if __name__ == "__main__":
    sys.exit(main())
