# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""init — open the workshop, place the contract, wire the settings, read back.

Creates what is absent and touches nothing that lives: re-running init over a
living workshop says so and only re-syncs what it places (placement provenance
decides what may refresh). Since 9.0 the plugin carries the hooks, the crew,
the skills and the style, so init has three hand jobs left: place the contract
CLAUDE.md, merge the permissions floor (the record's directory, and the host's
own session transcript) into the workshop's settings, and write the marketplace
+ enabledPlugins entry naming this core's own tree as the marketplace, so the
plugin is read from the tree it ships in and follows it (R14).
Then the file is read back, to prove the wiring took.
"""
import json
import os

from . import journal, placement, project, status

# The deny floor is matched on Edit() alone — Edit(path) covers every
# file-editing tool. A Write()/NotebookEdit() path rule matches nothing and
# Claude Code warns about it at every launch.
DENY_TOOLS = ("Edit",)

# The host writes what a session did into its own transcript. This core ships
# one rule over that file so a session cannot edit the account of itself;
# doctor reads the rule back and turns its `host: transcript rule` row green.
TRANSCRIPT_DENY = "Edit(~/.claude/projects/**/*.jsonl)"

STYLE_FILE = "across-the-desk.md"

# The marketplace this core registers, and the plugin inside it. The pair is
# the key `enabledPlugins` is written under: `<plugin>@<marketplace>`.
MARKETPLACE = "sandbox"
PLUGIN_NAME = "sandbox-os"

# The three skills the plugin ships. A copy of any of them under the owner's
# own ~/.claude/skills shadows the shipped one; init and doctor name them, and
# neither ever deletes a file under the owner's directory.
PLUGIN_SKILLS = ("backlog-sync", "sandbox-workshop", "spec-driven-discovery")


def _repo_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def deny_floor_target(ws):
    """the tail every deny-floor rule shares: the record's directory."""
    state = os.path.join(os.path.abspath(ws), journal.STATE_DIR)
    return "(//%s/**)" % state.lstrip("/")


def deny_floor_rules(ws):
    return ["%s%s" % (tool, deny_floor_target(ws)) for tool in DENY_TOOLS]


def _settings_path(ws):
    return os.path.join(ws, ".claude", "settings.json")


def plugin_key():
    return "%s@%s" % (PLUGIN_NAME, MARKETPLACE)


def marketplace_source():
    """the one source line (R14): this core's own tree, as the marketplace.

    The marketplace is the core's root, which carries `.claude-plugin/
    marketplace.json`, whose one plugin entry is the relative path
    `./vessel/plugin` — resolved against the marketplace, so the plugin
    follows the tree with no second copy of an absolute path anywhere.

    A `command` source was wired here until 9.0 and never loaded: `command`
    is a source a marketplace may give one of its PLUGINS, and a marketplace
    itself takes github, git, url, file, directory or settings — nothing
    else. Two facts came with that reading, and they are why the plugin
    entry is a path rather than a command: a command-sourced plugin loads
    only after the person accepts the exact command string once, in an
    interactive terminal; and in link mode a session started inside the
    printed directory (or below it) does not load the plugin at all.
    """
    return {"source": "directory", "path": _repo_root()}


def plugin_version():
    """the plugin's own version, or None when its manifest will not read."""
    p = os.path.join(_repo_root(), "vessel", "plugin", ".claude-plugin",
                     "plugin.json")
    try:
        with open(p, encoding="utf-8") as f:
            return json.load(f).get("version")
    except (OSError, ValueError):
        return None


def shadowed_skills():
    """the owner's own copies of skills the plugin now ships.

    Named, never removed: `~/.claude` is the owner's directory, and a tool
    that deletes there has taken a custody it was not given.
    """
    base = os.path.expanduser(os.path.join("~", ".claude", "skills"))
    return [n for n in PLUGIN_SKILLS if os.path.isdir(os.path.join(base, n))]


def shipped_payload(ws):
    """everything init places, as {dest: src} — the contract, and no more.

    One source for run(), the reset verb and the layer tests; `vessel.payload()`
    names the same list under `places`, so a hand-typed second list cannot
    drift from it. Everything else a session loads — the hooks, the six briefs,
    the three skills, the style, the two commands — ships in the plugin and is
    read from there.
    """
    from . import vessel
    return {os.path.join(ws, os.path.basename(src)): src
            for src in vessel.payload()["places"]}


def _prune_placed_guard_hooks(pre):
    """every PreToolUse entry that runs a placed guard.py, gone.

    8.x wired the guard from the workshop's own settings at an absolute path
    inside `.sandbox/vessel/`. The plugin wires it now, from its own hooks.json
    at `${CLAUDE_PLUGIN_ROOT}`, so the settings copy is a second wiring of a
    file this core no longer places.
    """
    pruned = 0
    for entry in list(pre):
        if any("guard.py" in hk.get("command", "")
               for hk in entry.get("hooks", []) or ()):
            pre.remove(entry)
            pruned += 1
    return pruned


def wired(ws):
    """true when the workshop's settings already carry this core's wiring.

    The same four facts the read-back proves, asked of a file nobody just
    wrote — so a migration can say "already wired" instead of writing the
    same lines a second time and reporting them twice.
    """
    try:
        with open(_settings_path(ws), encoding="utf-8") as f:
            back = json.load(f)
    except (OSError, ValueError):
        return False
    deny = back.get("permissions", {}).get("deny", [])
    entry = back.get("extraKnownMarketplaces", {}).get(MARKETPLACE, {})
    pre = (back.get("hooks") or {}).get("PreToolUse") or []
    placed_guard = any("guard.py" in hk.get("command", "")
                       for e in pre for hk in e.get("hooks", []) or ())
    return (all(r in deny for r in deny_floor_rules(ws))
            and TRANSCRIPT_DENY in deny
            and back.get("enabledPlugins", {}).get(plugin_key()) is True
            and (entry.get("source") or {}).get("source") == "directory"
            and not placed_guard)


def emit_settings(ws):
    """merge the deny floor and the plugin wiring. Returns (ok, report_lines)."""
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

    hooks = settings.get("hooks") or {}
    pre = hooks.get("PreToolUse") or []
    pruned = _prune_placed_guard_hooks(pre)
    if pruned:
        lines.append("pruned %d hook(s): the plugin wires the guard now" % pruned)
    if hooks:
        if not pre:
            hooks.pop("PreToolUse", None)
        if hooks:
            settings["hooks"] = hooks
        else:
            settings.pop("hooks", None)

    perms = settings.setdefault("permissions", {})
    deny = perms.setdefault("deny", [])

    # Prune rules on the record's directory that name a tool the floor no
    # longer emits — a workshop onboarded under an older floor carries them
    # forever otherwise, and Claude Code warns once per dead name at every
    # launch. Same scar as the hooks above: append-only wiring never heals.
    floor = deny_floor_rules(ws)
    tail = deny_floor_target(ws)
    stale = [r for r in deny if r.endswith(tail) and r not in floor]
    for rule in stale:
        deny.remove(rule)
    if stale:
        lines.append("pruned %d dead deny rule(s) on the record's directory" % len(stale))

    for rule in floor:
        if rule not in deny:
            deny.append(rule)
    lines.append("deny floor: %d rule(s) on the record's directory" % len(floor))

    if TRANSCRIPT_DENY not in deny:
        deny.append(TRANSCRIPT_DENY)
    lines.append("transcript rule: the account of a session is denied to edits")

    # The plugin, through this core's own tree as the marketplace: one entry
    # naming the directory, and one line turning the plugin on. The key this
    # entry is filed under is the one `enabledPlugins` names after the `@`.
    markets = settings.setdefault("extraKnownMarketplaces", {})
    markets[MARKETPLACE] = {"source": marketplace_source()}
    settings.setdefault("enabledPlugins", {})[plugin_key()] = True
    # surface: 7
    lines.append("plugin: %s %s — read from this core's own tree, each session"
                 % (PLUGIN_NAME, plugin_version() or "unread"))

    # The shipped voice, on by default — the owner's own setting always wins:
    # setdefault never touches an existing choice, and settings.local.json
    # (what /config writes) outranks this file anyway. The style itself is
    # shipped once, by the plugin; this names it and places nothing.
    if settings.setdefault("outputStyle", STYLE_FILE[:-3]) == STYLE_FILE[:-3]:
        lines.append("voice: %s is the session style unless you pick another"
                     % STYLE_FILE[:-3])

    with open(sp, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=1)

    # Read-back: every claim above, re-read off the file it was written to.
    with open(sp, encoding="utf-8") as f:
        back = json.load(f)
    back_deny = back.get("permissions", {}).get("deny", [])
    entry = back.get("extraKnownMarketplaces", {}).get(MARKETPLACE, {})
    ok = (all(r in back_deny for r in deny_floor_rules(ws))
          and TRANSCRIPT_DENY in back_deny
          and back.get("enabledPlugins", {}).get(plugin_key()) is True
          and (entry.get("source") or {}).get("source") == "directory"
          and (entry.get("source") or {}).get("path") == _repo_root())
    lines.append("read-back: %s" % ("the wiring took" if ok
                                    else "the wiring did not take"))
    return ok, lines


def run(ws):
    """the whole of init. Returns (ok, text)."""
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

    for line in placement.sync(ws, shipped_payload(ws)):
        lines.append(line)

    ok, wire_lines = emit_settings(ws)
    lines.extend(wire_lines)

    shadowed = shadowed_skills()
    if shadowed:
        lines.append("your own copies of %s shadow the plugin's — retire them "
                     "when you like: rm -r ~/.claude/skills/NAME"
                     % ", ".join(shadowed))

    from . import update
    if alive:
        update.record_version(ws)
    else:
        # born under this core: nothing older to migrate from. the high-water
        # mark starts at the newest migration so a fresh workshop is current.
        update.record_version(ws, migration=max([m[0] for m in update.MIGRATIONS] or [0]))
    if not alive:
        lines.append("ready. nobody's tool.")
    return ok, "\n".join(lines)
