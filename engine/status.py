# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""status / resume / play / doctor — the workshop meeting its owner.

One producer sits under every arrival: `needs(ws)` walks what a running loop
leaves behind — drafts waiting, makes still open, provisional acts, checks
whose text moved, closes with no ship after them — and hands back one row per
waiting thing with its age, oldest first. Three renderers read it and none of
them re-derives it: `status` prints a sentence then the rows then the project
table, `resume` prints the same before the pile it asks a key over, and
`status --line` folds it to the single row a host's status line can hold.

doctor is the other half: three blocks, in order. The checks say what it could
prove about this workshop and the host it sits on; `ready:` names what is
merely waiting to go out and never touches the exit code; the footer carries
the legend, the index counts, and the list of what it could not read. Its
verdicts are three, because a receipt nobody could read is a gap in what
doctor can see rather than a fault in the workshop.

Nothing here writes. Looking is not making (law 12), and a test hashes the
whole workshop before and after to keep that true.
"""
import calendar
import glob
import json
import os
import re
import sys
import time

from . import desk, gate, journal, notes, project, provisional, ship

PLAYGROUND = "playground"

# R16 and R6 share one threshold: an open make, a provisional act and a green
# project with no ship after it all turn from named to LOOK after a week.
WEEK = 7
MONTH = 30
STYLE_FILE = "across-the-desk.md"

# the counting words, so the sentence reads as a sentence up to ten and as a
# number after that — a person triaging never has eleven things and a machine
# that pretends otherwise is guessing.
COUNTS = ("nothing", "one", "two", "three", "four", "five", "six", "seven",
          "eight", "nine", "ten")


# --- the one age -----------------------------------------------------------

def _seconds_since(ts):
    """seconds between a stored stamp and now, in real time, or 0."""
    try:
        then = calendar.timegm(time.strptime(ts, "%Y-%m-%dT%H:%M:%SZ"))
    except (TypeError, ValueError):
        return 0
    return max(0, int(time.time() - then))


def age(ts):
    """the one age formatter: days once there is a day, hours under it."""
    secs = _seconds_since(ts)
    days = secs // 86400
    if days:
        return "%d d" % days
    return "%d h" % (secs // 3600)


def age_days(ts):
    return _seconds_since(ts) // 86400


# --- the needs producer ----------------------------------------------------

class Need(object):
    """one waiting thing: what kind, what it is about, when it started, and
    the verb that ends it. `text` is the rendered row every surface prints.

    `count` is how many of the thing this row stands for — one make, but
    four drafts or nine closes. The status line folds on it rather than
    re-counting off its own second read of the same workshop.
    """

    __slots__ = ("kind", "subject", "ts", "verb", "text", "count")

    def __init__(self, kind, subject, ts, verb, text, count=1):
        self.kind, self.subject, self.ts = kind, subject, ts
        self.verb, self.text, self.count = verb, text, count

    @property
    def age_days(self):
        return age_days(self.ts)

    def __repr__(self):
        return "<need %s %s %s>" % (self.kind, self.subject, age(self.ts))


def open_makes(ws):
    """every make still open: (project, intent, when it opened)."""
    d = os.path.join(ws, journal.STATE_DIR)
    out = []
    if not os.path.isdir(d):
        return out
    for name in sorted(os.listdir(d)):
        if not (name.startswith("make-open-") and name.endswith(".json")):
            continue
        try:
            with open(os.path.join(d, name), encoding="utf-8") as f:
                snap = json.load(f)
        except (OSError, ValueError):
            continue
        out.append((name[len("make-open-"):-len(".json")],
                    snap.get("intent") or "", snap.get("opened") or ""))
    return out


def closes_row(name, n, aged=None):
    """the ship debt, as one row: work wrapped and not yet put on the record.

    R6's nag, and it is written as the count rather than a verdict — what is
    owed here is a ship, and the number is the whole of it. The door rides
    with it, because a count with nothing to do about it is noise.
    """
    # surface: 1
    return ("%d close(s) since the last ship on %s%s — sandbox ship %s"
            % (n, name, (" " + aged) if aged else "", name))


def _closes(ws, events):
    """[(project, count, the ts of the oldest close since its last ship)]."""
    counts, oldest = {}, {}
    for e in events:
        name = e.get("project")
        if not name:
            continue
        if e.get("op") == "ship":
            counts[name] = 0
            oldest.pop(name, None)
        elif e.get("op") == "make" and e.get("phase") == "close":
            counts[name] = counts.get(name, 0) + 1
            oldest.setdefault(name, e.get("ts"))
    return [(n, c, oldest.get(n)) for n, c in sorted(counts.items()) if c]


def _checks_moved(ws, events):
    """projects whose `## checks` text changed after the key that ratified it.

    A ship that has already been paid for reads no key again; a ship whose
    lines moved reads one. Naming it here is the difference between finding
    that out at the arrival and finding it out mid-ceremony.
    """
    ratified, when = ship._ratified(ws), {}
    for e in events:
        if e.get("op") == "ratify" and e.get("project"):
            when[e["project"]] = e.get("ts")
    out = []
    for c in project.list_all(ws):
        name = c["dir"]
        if name not in ratified or not c.get("checks"):
            continue
        if ship.checks_hash(c["checks"]) != ratified[name]:
            out.append((name, when.get(name)))
    return out


def needs(ws):
    """everything waiting on the owner, oldest first — the one producer.

    `status`, `resume` and the status line all read this list and none of
    them re-derives it: three renderers over one truth is how the arrival
    surfaces stopped disagreeing about what was waiting.
    """
    events, _scars = journal.read(ws)
    out = []

    pile, _ = desk.drafts(ws)
    if pile:
        first = min(pile, key=lambda d: d.get("staged_at") or "")
        # surface: 1
        out.append(Need("draft", "%d draft(s)" % len(pile),
                        first.get("staged_at"), "sandbox approve",
                        '%d draft(s) · "%s" %s — sandbox approve'
                        % (len(pile), (first.get("body") or "")[:52],
                           age(first.get("staged_at"))), count=len(pile)))

    for name, intent, opened in open_makes(ws):
        # surface: 1
        out.append(Need("make", name, opened, "sandbox make %s --close" % name,
                        "%s · make %s open %s — sandbox make %s --close"
                        % (name, (intent or "no intent")[:40], age(opened), name)))

    waiting = provisional.pending(ws)
    if waiting:
        oldest = min(a.get("ts") or "" for a in waiting)
        # surface: 1
        out.append(Need("provisional", "%d act(s)" % len(waiting), oldest,
                        "sandbox resume",
                        "%d provisional act(s) waiting %s — sandbox resume"
                        % (len(waiting), age(oldest)), count=len(waiting)))

    for name, when in _checks_moved(ws, events):
        # surface: 1
        out.append(Need("checks", name, when, "sandbox ship %s" % name,
                        "%s · the checks moved since your k %s — sandbox ship %s"
                        % (name, age(when), name)))

    for name, n, when in _closes(ws, events):
        out.append(Need("close", name, when, "sandbox ship %s" % name,
                        closes_row(name, n, age(when)), count=n))

    out.sort(key=lambda n: n.ts or "")
    return out


def sentence(items):
    """the triage line every arrival opens with."""
    if not items:
        # surface: 1
        return "nothing needs you."
    n = len(items)
    word = COUNTS[n] if n < len(COUNTS) else "%d" % n
    # surface: 1
    return "%s thing needs you." % word if n == 1 else "%s things need you." % word


# --- the renderers ---------------------------------------------------------

def status(ws):
    """the sentence, the things, then the workshop's own table."""
    items = needs(ws)
    lines = [sentence(items)]
    lines += ["  " + n.text for n in items]
    projects = project.list_all(ws)
    on = project.on_list(ws)
    active = [p for p in projects if p["state"] == "active"]
    # surface: 1
    lines.append("%d project(s), %d active · on: %s" %
                 (len(projects), len(active), ", ".join(on) if on else "nothing"))
    for p in projects:
        mark = "*" if p["dir"] in on else " "
        lines.append(" %s %-20s %-8s %s" % (mark, p["dir"], p["state"], p["goal"]))
    _pile, scars = desk.drafts(ws)
    if scars:
        # surface: 1
        lines.append("%d unreadable staging line(s) — doctor has details" % len(scars))
    return "\n".join(lines)


def line(ws):
    """the host's status line, in one row: what is on, and what is owed.

    It folds the one `needs()` list, like the other two renderers — it never
    counts the workshop a second way. The ship debt is the ON project's own,
    the project this row names: a sum over five other projects printed beside
    one project's name is a number about somebody else, and the line was
    saying `37 closes since ship` while doctor said 0 for the same project.

    Cheap on purpose and durable on purpose: it writes nothing, it mints
    nothing, and it exits 0 whatever it finds, because a status line that can
    fail a shell is a status line somebody turns off.
    """
    on = project.on_list(ws)
    here = on[0] if on else None
    items = needs(ws)
    drafts = sum(i.count for i in items if i.kind == "draft")
    makes = [i for i in items if i.kind == "make"]
    closes = sum(i.count for i in items
                 if i.kind == "close" and i.subject == here)
    return " · ".join([
        here or "no project",
        ("%d draft%s" % (drafts, "" if drafts == 1 else "s"))
        if drafts else "no drafts",
        ("make %s" % age(min(i.ts or "" for i in makes))) if makes else "no make",
        ("%d close%s since ship" % (closes, "" if closes == 1 else "s"))
        if closes else "shipped",
    ])


def resume(ws, out=print):
    """arrivals: what waits, the fingerprint over it, and the one key that
    lands the drafts and confirms every clean act under that one hash.

    Returns the exit code. A pipe gets the refusal and a 1: the arrivals beat
    is `sandbox status`, which needs no key and writes nothing.
    """
    if not gate.at_a_terminal():
        out(gate.NOT_A_TTY % "resume")
        return 1
    items = needs(ws)
    out(sentence(items))
    for n in items:
        out("  " + n.text)
    events, _ = journal.read(ws)
    recent = [e for e in events[-10:] if e.get("op") in ("ship", "make", "assert")]
    if recent:
        # surface: 22
        out("since you left:")
        for e in recent[-5:]:
            out("  %s %s" % (e.get("op"), (e.get("body") or "")[:70]))
    pile, _ = desk.drafts(ws)
    waiting = provisional.pending(ws)
    clean = [a for a in waiting if provisional.status_of(ws, a) == "clean"]
    moved = [a for a in waiting if provisional.status_of(ws, a) != "clean"]
    for a in moved:
        out("  needs your hand: %s (%s) — the file moved on; revert or confirm it yourself"
            % (a["why"], os.path.basename(a["path"])))
    if not pile and not clean:
        out("nothing waits. the page is quiet.")
        return 0

    rows = [desk.row(d) for d in pile]
    rows += ["[provisional] %s" % a["why"] for a in clean]
    count, digest = gate.show(rows, out)
    gate.ask(count, out)
    consent = gate.mint_consent(shown=digest)
    if consent is None:
        # surface: 2
        out("cancelled — nothing landed")
        return 0
    # surface: 27
    drafts_shown = pile[:min(count, len(pile))]
    acts_shown = clean[:count - len(drafts_shown)]
    landed = 0
    if drafts_shown:
        landed, msg = desk.land_all(ws, consent, shown=drafts_shown)
        if landed is None:
            out(msg)
            return 1
        for p in {d.get("project") for d in drafts_shown}:
            notes.refresh_canon(ws, p)
    for a in acts_shown:
        ok, _why = provisional.confirm(ws, a["id"], consent)
        landed += 1 if ok else 0
    out("landed %d (shown %s)" % (landed, digest[:8]))
    return 0


def play(ws):
    """the free room. Uncounted and uncitable by construction: nothing under
    playground/ is read by canon, recall, or the record."""
    d = os.path.join(ws, PLAYGROUND)
    os.makedirs(d, exist_ok=True)
    charter = os.path.join(d, "CHARTER.md")
    if not os.path.exists(charter):
        with open(charter, "w", encoding="utf-8") as f:
            f.write("# the playground\n\nnothing in here is counted, "
                    "cited, or shipped. try things.\n")
    return "the playground is open: %s — nothing in there touches the record." % d


# --- doctor: what the record and the disk say to each other ----------------

# the actions placement.py itself mints. `place` is a shared op: apps mint
# `app-installed` and `app-removed` on it and keep their own book under
# `.sandbox/apps/`, so the placement book is held only to its own rows.
PLACE_ACTIONS = ("placed", "adopted", "refreshed", "re-baselined", "reset", "removed")


def _place_events(ws, events):
    """the placement book as the `place` events would rebuild it."""
    book = {}
    for e in events:
        if e.get("op") != "place" or not e.get("path"):
            continue
        if e.get("action") not in PLACE_ACTIONS:
            continue
        if e.get("action") == "removed":
            book.pop(e["path"], None)
        else:
            book[e["path"]] = e.get("sha")
    return book


def agreement(ws, events=None):
    """[(side, projection, what)] — where a projection and the record differ.

    Two projections are folded from the record and held beside the file on
    disk: the shelf's cards against the `build-kept` events, and the placement
    book against the `place` events. A difference is never averaged and never
    quietly repaired: the side that is ahead is named, and the rebuild waits
    for the owner's hand.
    """
    from . import placement, shelf
    # surface: 4
    if events is None:
        events, _ = journal.read(ws)
    out = []

    # a struck keep (sandbox invalidate) leaves this reading: the line stays
    # on the record, and the shelf is read as the owner's strike left it.
    struck = {e.get("of") for e in events if e.get("op") == "invalidate"}
    kept = {e.get("build") for e in events
            if e.get("op") == "assert" and e.get("cls") == "build-kept"
            and e.get("build") and e.get("id") not in struck}
    carded = {c["name"] for c in shelf.list_all(ws)}
    for name in sorted(carded - kept):
        out.append(("disk", "shelf", "%s is on the shelf with no build-kept event" % name))
    for name in sorted(kept - carded):
        out.append(("record", "shelf", "%s was kept and has no card on the shelf" % name))

    want = _place_events(ws, events)
    have = placement.book(ws)
    for p in sorted(set(want) - set(have)):
        out.append(("record", "place", "%s was placed and the book forgot it"
                    % os.path.basename(p)))
    for p in sorted(set(have) - set(want)):
        out.append(("disk", "place", "%s is in the book with no place event"
                    % os.path.basename(p)))
    return out


PROJECTION_VERB = {"shelf": "shelf", "place": "place", "canon": "canon"}


def repair_line(side, projection, what):
    """the one sentence a disagreement prints, with the rebuild it needs."""
    # surface: 4
    return ("repair required: the %s is ahead — %s — sandbox update --rebuild %s"
            % (side, what, PROJECTION_VERB.get(projection, projection)))


# --- doctor: the host's settings, as receipts ------------------------------

MANAGED = "/Library/Application Support/ClaudeCode/managed-settings.json"
TRANSCRIPT_MARKS = (".claude/projects", "transcript", ".jsonl")


def transcript_rule():
    """the deny rule this core ships for the host's own transcript, or None.

    doctor holds the host to what the core actually ships and to nothing
    else: while there is no rule here to place, an absent one is a gap in
    what this core can prove rather than a fault on the host's side. The day
    the plugin ships one, this receipt turns from `?` to LOOK by itself.
    """
    from . import onboard
    return getattr(onboard, "TRANSCRIPT_DENY", None)


def _short(path, ws=None):
    """a path as a person would say it: `~` for home, plain for the workshop."""
    if ws and path.startswith(os.path.abspath(ws) + os.sep):
        return os.path.relpath(path, os.path.abspath(ws))
    home = os.path.expanduser("~")
    return "~" + path[len(home):] if path.startswith(home) else path


def settings_files(ws):
    """[(name, parsed)] — the settings a receipt may come out of, in order.

    Managed first because a managed value outranks a chosen one, then the
    host's own file, then the workshop's. A file that will not parse is read
    as unreadable rather than as absent, and doctor's footer says so.
    """
    out = []
    for p in (MANAGED, os.path.expanduser(os.path.join("~", ".claude", "settings.json")),
              os.path.join(ws, ".claude", "settings.json")):
        if not os.path.exists(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                out.append((_short(p, ws), json.load(f)))
        except (OSError, ValueError):
            out.append((_short(p, ws), None))
    return out


def _dig(d, *keys):
    for k in keys:
        if not isinstance(d, dict) or k not in d:
            return None
        d = d[k]
    return d


def settings_receipts(ws, sources=None):
    """[(label, verdict, detail)] — the host's fences, proved or not proved.

    The one reader: the guard asks this function rather than parsing the same
    two files a second way, so a fence the guard fences and a fence doctor
    reports can never be two different fences. A value nobody could read is
    `?`, never `ok` — the 07-31 scar was a fence reported green that nobody
    had ever opened.
    """
    from . import face
    # surface: 4
    sources = settings_files(ws) if sources is None else sources
    readable = [(n, d) for n, d in sources if isinstance(d, dict)]
    out = []

    found = None
    for name, d in readable:
        v = _dig(d, "sandbox", "network", "strictAllowlist")
        if v is not None:
            found = (name, v)
            break
    if found is None:
        out.append(("host: strict allowlist", face.GAP,
                    "no sandbox key in the settings i can read"))
    else:
        out.append(("host: strict allowlist",
                    face.OK if found[1] else face.LOOK,
                    "%s (%s)" % ("on" if found[1] else "off", found[0])))

    rule = None
    for name, d in readable:
        for r in _dig(d, "permissions", "deny") or ():
            if any(m in str(r) for m in TRANSCRIPT_MARKS):
                rule = (name, r)
                break
        if rule:
            break
    shipped = transcript_rule()
    if rule:
        out.append(("host: transcript rule", face.OK,
                    "%s (%s)" % (rule[1], rule[0])))
    elif not readable:
        out.append(("host: transcript rule", face.GAP, "no settings file reads"))
    elif shipped is None:
        out.append(("host: transcript rule", face.GAP,
                    "this core ships no transcript rule to hold them to"))
    else:
        out.append(("host: transcript rule", face.LOOK,
                    "no deny rule covers the transcript — sandbox init writes "
                    "the one this core ships"))

    base = None
    for name, d in readable:
        v = _dig(d, "worktree", "baseRef")
        if v is not None:
            base = (name, v)
            break
    if base:
        out.append(("host: worktree isolation", face.OK,
                    "baseRef %r (%s)" % (base[1], base[0])))
    else:
        out.append(("host: worktree isolation", face.GAP,
                    "no worktree key in the settings i can read"))

    off = None
    for name, d in readable:
        v = d.get("disableAllHooks")
        if v is not None:
            off = (name, v)
            break
    if off is None:
        out.append(("host: hooks on", face.GAP,
                    "no disableAllHooks key in the settings i can read"))
    else:
        out.append(("host: hooks on", face.LOOK if off[1] else face.OK,
                    "%s (%s)" % ("hooks are off" if off[1] else "hooks are on", off[0])))

    # the two lines that decide whether a session loads this core at all: the
    # marketplace entry pointing at this tree, and the plugin turned on under
    # it. init writes both; doctor reads them back off the file, so a workshop
    # whose plugin quietly stopped loading says so instead of looking green.
    from . import onboard
    want = onboard.marketplace_source()
    entry = None
    for name, d in readable:
        v = _dig(d, "extraKnownMarketplaces", onboard.MARKETPLACE, "source")
        if v is not None:
            entry = (name, v)
            break
    if not readable:
        out.append(("host: plugin marketplace", face.GAP, "no settings file reads"))
    elif entry is None:
        out.append(("host: plugin marketplace", face.LOOK,
                    "no %s marketplace in the settings i can read — sandbox init"
                    % onboard.MARKETPLACE))
    elif entry[1] == want:
        from . import clean
        out.append(("host: plugin marketplace", face.OK,
                    "%s at %s (%s)" % (want["source"],
                                       clean.strip_home(want["path"])[0],
                                       entry[0])))
    else:
        out.append(("host: plugin marketplace", face.LOOK,
                    "%r is not this tree — sandbox init" % (entry[1],)))

    on = None
    for name, d in readable:
        v = _dig(d, "enabledPlugins", onboard.plugin_key())
        if v is not None:
            on = (name, v)
            break
    if not readable:
        out.append(("host: plugin on", face.GAP, "no settings file reads"))
    elif on is None:
        out.append(("host: plugin on", face.LOOK,
                    "no %s line in the settings i can read — sandbox init"
                    % onboard.plugin_key()))
    else:
        out.append(("host: plugin on", face.OK if on[1] is True else face.LOOK,
                    "%s (%s)" % ("on" if on[1] is True else
                                 "off — sandbox init", on[0])))
    return out


# an address is anything a person could dial: a url, a host:port, or a domain
# a permission rule already names. doctor lists them and opens none of them
# (law 7) — the plugin is listed as a receipt too and is never read for one.
_URL = re.compile(r"https?://[^\s\"'\\)]+")
_HOSTPORT = re.compile(r"\b(?:\d{1,3}(?:\.\d{1,3}){3}|localhost)(?::[^\s\"'/]+)?")
_DOMAIN_RULE = re.compile(r"domain:([^)\s]+)")


def endpoints(ws, sources=None):
    """[(where, address)] — every address these settings name, unopened."""
    sources = settings_files(ws) if sources is None else sources
    out, seen = [], set()
    for name, d in sources:
        if not isinstance(d, dict):
            continue
        raw = json.dumps(d)
        for rx in (_URL, _HOSTPORT, _DOMAIN_RULE):
            for m in rx.finditer(raw):
                addr = (m.group(1) if rx is _DOMAIN_RULE else m.group(0)).rstrip(",;")
                if addr and (name, addr) not in seen:
                    seen.add((name, addr))
                    out.append((name, addr))
    return sorted(out)


# --- doctor: the vessel's own copies ---------------------------------------

def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def style_source():
    return os.path.join(_repo_root(), "vessel", "plugin", "output-styles", STYLE_FILE)


KNOWN_MARKETPLACES = os.path.join("~", ".claude", "plugins",
                                  "known_marketplaces.json")
ORPHAN_MARK = ".orphaned_at"


def known_marketplaces():
    """the marketplace names the host still holds, or None when unreadable.

    None is not "none": a file that will not read is a gap, and a gap makes
    every cache dir count rather than none of them.
    """
    try:
        with open(os.path.expanduser(KNOWN_MARKETPLACES), encoding="utf-8") as f:
            d = json.load(f)
    except (OSError, ValueError):
        return None
    return set(d) if isinstance(d, dict) else set(d or ())


def _live_cache(path, known):
    """is this plugin-cache copy one `sandbox update` could still reach?

    Two ways a cache dir stops being ours to update: the host marked it
    orphaned (`.orphaned_at`, written when a marketplace is removed), or its
    marketplace is no longer in `known_marketplaces.json`. Either way the
    row would have prescribed `sandbox update` for a directory update never
    walks — a door that does nothing is worse than no door.
    """
    # …/cache/<marketplace>/<plugin>/<version>/output-styles/<file>
    version = os.path.dirname(os.path.dirname(path))
    plugin = os.path.dirname(version)
    market = os.path.dirname(plugin)
    for d in (version, plugin, market):
        if os.path.exists(os.path.join(d, ORPHAN_MARK)):
            return False
    return known is None or os.path.basename(market) in known


def style_copies(ws):
    """[(where, matches)] — every copy of the style this machine can see.

    Orphaned plugin caches are left out: doctor names a stale copy with the
    verb that fixes it, so a copy no verb here can touch is not a row.
    """
    out = []
    src = style_source()
    if not os.path.exists(src):
        return out
    with open(src, "rb") as f:
        want = f.read()
    seen = [os.path.join(ws, ".claude", "output-styles", STYLE_FILE),
            os.path.expanduser(os.path.join("~", ".claude", "output-styles", STYLE_FILE))]
    known = known_marketplaces()
    seen += [c for c in sorted(glob.glob(os.path.expanduser(os.path.join(
        "~", ".claude", "plugins", "cache", "*", "*", "*", "output-styles",
        STYLE_FILE)))) if _live_cache(c, known)]
    for p in seen:
        if not os.path.exists(p) or os.path.abspath(p) == os.path.abspath(src):
            continue
        try:
            with open(p, "rb") as f:
                out.append((_short(p), f.read() == want))
        except OSError:
            continue
    return out


def plugin_version():
    """the plugin's own version string, or None when it cannot be read."""
    p = os.path.join(_repo_root(), "vessel", "plugin", ".claude-plugin", "plugin.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("version")
    except (OSError, ValueError):
        return None


def voice_hit(ws, texts):
    """the first placed file that says a word the soul cut, or None.

    The bytes read are the placed copy's; the exemptions read are the source
    file's, so a brief that quotes the cut list to teach it is still allowed
    to quote it after it is placed.
    """
    from . import onboard, voicelint
    payload = onboard.shipped_payload(ws)
    phrases = voicelint.forbidden_phrases()
    for dest in texts:
        src = payload.get(dest)
        rel = voicelint._rel(src) if src else ""
        try:
            with open(dest, encoding="utf-8") as f:
                text = f.read()
        except (OSError, UnicodeDecodeError):
            continue
        hits = voicelint.phrase_hits(voicelint.blanked(text, rel, "forbidden"),
                                     phrases)
        if hits:
            return _short(dest, ws), hits[0][1]
    return None


def placed_texts(ws):
    """the placed files whose words a person reads: the contract, the style,
    the briefs — what the lint is pointed at when doctor asks about voice."""
    from . import onboard
    return sorted(d for d in onboard.shipped_payload(ws) if d.endswith(".md")
                  and os.path.exists(d))


# --- doctor -----------------------------------------------------------------

def _checks_block(ws, events, scars, missing, unread):
    """block a: what doctor could prove about this workshop and this host."""
    from . import face, onboard, placement, update
    # surface: 4
    rows = []

    v = sys.version_info
    rows.append(("python 3.9 or newer", v >= (3, 9), "%d.%d" % (v[0], v[1])))

    import shutil
    rows.append(("git on the path", shutil.which("git") is not None,
                 "" if shutil.which("git") else "not found — projects stand without history"))

    if missing:
        rows.append(("a workshop here", False, "none yet — sandbox init"))
    else:
        rows.append(("the record reads", True, "%d event(s)" % len(events)))
        rows.append(("no torn lines", not scars, "; ".join(scars) if scars else ""))

    bad = []
    for p in project.list_all(ws):
        if p["state"] not in ("active", "parked", "done"):
            bad.append("%s: state %r" % (p["dir"], p["state"]))
    rows.append(("project contracts parse", not bad, "; ".join(bad)))

    for name, intent, opened in open_makes(ws):
        # R16 names an open make at any age and turns it LOOK past a week.
        # LOOK rather than False on purpose (A#9): a make left open is work
        # in progress, not a workshop out of agreement with itself, and the
        # exit belongs to the repair rows alone.
        stale_make = age_days(opened) > WEEK
        rows.append(("open makes", face.LOOK if stale_make else face.OK,
                     "%s %r open %s — sandbox make %s --close"
                     % (name, (intent or "no intent")[:40], age(opened), name)))

    stale = provisional.oldest_age_days(ws)
    rows.append(("provisional acts fresh", stale <= WEEK,
                 "oldest act is %d day(s) old — resume and rule on it" % stale
                 if stale > WEEK else ""))

    s = update.skew(ws)
    rows.append(("core and workshop agree", s is None, s or ""))

    disagree = agreement(ws, events)
    rows.append(("journal and disk agree", not disagree,
                 repair_line(*disagree[0]) if disagree else ""))
    for row in disagree[1:]:
        rows.append(("journal and disk agree", False, repair_line(*row)))

    div = placement.diverged(ws)
    rows.append(("placed files current", not div,
                 "updates are skipping your edited copies: %s — sandbox reset PATH re-baselines"
                 % ", ".join(os.path.basename(d) for d in div) if div else ""))

    drift = placement.unrecorded_drift(ws, onboard.shipped_payload(ws))
    rows.append(("kept files match what ships", not drift,
                 "never-recorded copies differ from this core: %s — restore on your word: sandbox reset NAME"
                 % ", ".join(os.path.basename(d) for d in drift) if drift else ""))

    sources = settings_files(ws)
    for name, d in sources:
        if d is None:
            unread.append("%s (would not parse)" % name)
    rows.extend(settings_receipts(ws, sources))

    addrs = endpoints(ws, sources)
    rows.append(("endpoints", face.OK if addrs else face.GAP,
                 "%d address(es) in %d source(s) — listed, never opened"
                 % (len(addrs), len({n for n, _ in addrs}))
                 if addrs else "no address in the settings i can read"))
    for where, addr in addrs[:12]:
        rows.append(("", None, "       %-46s %s" % (addr[:46], where)))

    core = update.core_version()
    pv = plugin_version()
    if pv is None:
        rows.append(("plugin version", face.GAP, "plugin.json would not read"))
    else:
        rows.append(("plugin version", pv == core,
                     "%s" % pv if pv == core
                     else "plugin.json %s, core %s — sandbox update" % (pv, core)))

    texts = placed_texts(ws)
    stalest = [w for w, same in style_copies(ws) if not same]
    said = voice_hit(ws, texts)
    if not texts:
        rows.append(("voice", face.GAP, "no placed file to read"))
    else:
        if said:
            where, phrase = said
            rows.append(("voice", False, "%s says %r — sandbox reset NAME"
                         % (where, phrase)))
        elif stalest:
            rows.append(("voice", False, "%s is not the style this core ships "
                         "— sandbox update" % stalest[0]))
        else:
            from . import vessel
            ships = vessel.payload()
            copies = style_copies(ws)
            rows.append(("voice", True,
                         "%d placed file(s), %d in the plugin%s"
                         % (len(texts), len(ships["ships"]),
                            (", %d style copy(s) match" % len(copies))
                            if copies else "")))
    return rows


def _ready_block(ws, events):
    """block b: opportunities. it never touches the exit code."""
    from . import shelf
    out = []
    for name, n, when in _closes(ws, events):
        if age_days(when) > WEEK:
            # surface: 4
            out.append("%s — %d close(s) and no ship after them, %s — sandbox ship %s"
                       % (name, n, age(when), name))
    shared = {e.get("build") for e in events
              if e.get("op") == "assert" and e.get("cls") == "build-shared"}
    for c in shelf.list_all(ws):
        if c["name"] not in shared:
            # surface: 4
            out.append("%s — a build that has never left this machine — "
                       "sandbox share %s --to DIR" % (c["name"], c["name"]))
    if not any(e.get("op") == "export" or e.get("cls") == "export" for e in events):
        # surface: 4
        out.append("export: never run")
    from . import onboard
    for name in onboard.shadowed_skills():
        # surface: 4
        out.append("%s — shadowed by the plugin — retire: rm -r "
                   "~/.claude/skills/%s" % (name, name))
    seats, used = {}, {}
    for e in events:
        for seat, n in (e.get("agents") or {}).items():
            seats[seat] = seats.get(seat, 0) + n
            if age_days(e.get("ts")) <= MONTH:
                used[seat] = used.get(seat, 0) + n
    if seats:
        # surface: 4
        out.append("crew: %d seat(s) on the record, %d used in %d days"
                   % (len(seats), len(used), MONTH))
    return out


# the rows whose LOOK is a repair: the workshop disagreeing with its own
# record, or with the core it was placed from. These decide the exit; every
# other LOOK is a thing that needs the owner and says so.
REPAIR_ROWS = ("journal and disk agree", "placed files current",
               "kept files match what ships", "core and workshop agree")


def doctor(ws):
    """health, one honest line each. Returns (all_ok, lines).

    Three blocks in one order. The checks decide the exit code; `ready:` names
    what is merely waiting and never does; the footer says what was read, what
    the marks mean, and what could not be read at all. A `?` is a gap in the
    reading, so it leaves the exit alone (settled at design altitude).
    """
    from . import face, registry
    unread = []
    missing = not os.path.exists(journal.path(ws))
    events, scars = ([], []) if missing else journal.read(ws)
    if missing:
        unread.append("the record (absent)")

    rows = _checks_block(ws, events, scars, missing, unread)

    lines = []
    for label, verdict, note_ in rows:
        if verdict is None:
            lines.append(note_)
            continue
        lines.append((" %-4s %-28s %s"
                      % (face.mark(verdict).strip(), label, note_)).rstrip())

    ready = _ready_block(ws, events)
    if ready:
        # surface: 4
        lines.append("ready:")
        lines += ["  " + r for r in ready]

    # surface: 29
    lines.append("ok = proved · LOOK = needs you · ? = could not read")
    idx = registry.index(ws, write=False)
    # surface: 4
    lines.append("index: journal %s of %s · folded in %d ms"
                 % ("{:,}".format(idx["events"]),
                    "{:,}".format(registry.INDEX_AT_EVENTS), idx["built_ms"]))
    for label, verdict, note_ in rows:
        if verdict == face.GAP and label:
            unread.append(label)
    if unread:
        # surface: 4
        lines.append("could not read: %s" % " · ".join(unread))

    # R24 and A#9: the exit is the repair block's alone. A row counts when
    # its verdict is False, and a LOOK counts only when it names a repair —
    # the record and the disk disagreeing, a placed or kept file drifted, a
    # core and a workshop on different versions. An open make (R16), a host
    # row and every row under `ready:` are named and never the exit: a
    # three-week-old make used to keep doctor red, which taught the owner to
    # stop reading the exit code.
    ok = all(v is not False and (v != face.LOOK or _l not in REPAIR_ROWS)
             for _l, v, _n in rows
             if v is not None and not (_l or "").startswith("host:"))
    return ok, lines
