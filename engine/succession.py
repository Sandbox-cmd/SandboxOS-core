# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""import — succession in one honest verb (law 2).

A past body's workshop comes in whole: the journal moves VERBATIM (the
record is the self; it is never rewritten, and the old genesis stays the
genesis — one continuous record across bodies), a path-map rides beside it
so every old receipt opens at its new address, chosen projects arrive live
with their local git histories, saved builds keep their cards, the owner's
own agents come along, and every carried ratification is voided OUT LOUD —
each project's checks await one fresh keystroke, listed in one place.

What does not come is said plainly: staged drafts die with the old staging
file (land them there first), and everything not chosen stays where it was
— the old workshop is the cold store, kept until the owner deletes it by
hand.
"""
import os
import shutil

from . import journal, project, update

OLD_PROJECT_DIRS = ("channels", "projects")
OLD_SHELF_DIRS = ("rack", "shelf")
OLD_CONTRACTS = ("CHANNEL.md", "BENCH.md", "PROJECT.md")
OLD_CARDS = ("CART.md", "PART.md", "BUILD.md")


def _old_projects_dir(old):
    for d in OLD_PROJECT_DIRS:
        p = os.path.join(old, d)
        if os.path.isdir(p):
            return p
    return None


def _record_of(old):
    """the record inside a past workshop, or inside a leaving directory.

    a workshop keeps it under its state directory; `export --portable` writes
    it at the leaving directory's own root. one reader finds either, so the
    thing export writes is the thing import takes, with no second verb.
    """
    for p in (os.path.join(old, journal.STATE_DIR, "journal.jsonl"),
              os.path.join(old, "journal.jsonl")):
        if os.path.exists(p):
            return p
    return None


def _carried_map(old, ws):
    """the addresses a leaving directory brought with it: the workshop it left
    maps onto the one it arrives in, so an old receipt opens here."""
    p = os.path.join(old, "path-map.json")
    if not os.path.exists(p):
        return []
    import json
    try:
        with open(p, encoding="utf-8") as f:
            pairs = json.load(f)
    except (OSError, ValueError):
        return []
    return [(o, ws if n == "." else n) for o, n in pairs if o]


def _old_contract(pdir):
    for name in OLD_CONTRACTS:
        p = os.path.join(pdir, name)
        if os.path.exists(p):
            return p
    return None


def list_old(old_root):
    """what the old workshop offers: (name, state, goal, root) per project."""
    base = _old_projects_dir(old_root)
    if base is None:
        return []
    out = []
    for name in sorted(os.listdir(base)):
        cpath = _old_contract(os.path.join(base, name))
        if cpath is None:
            continue
        c = project.parse_contract(cpath)
        out.append({"name": name, "state": c["state"], "goal": c["goal"],
                    "root": c["root"]})
    return out


def _relocate(rootp, old_root):
    """a root recorded before the old workshop moved: find its suffix under
    the old workshop's new address. Returns a real dir or None."""
    if os.path.isdir(rootp):
        return rootp
    parts = [p for p in rootp.split(os.sep) if p]
    for i in range(len(parts)):
        cand = os.path.join(old_root, *parts[i:])
        if os.path.isdir(cand):
            return cand
    return None


def _copy_tree(src, dest):
    shutil.copytree(src, dest, symlinks=True,
                    ignore=shutil.ignore_patterns("__pycache__", ".DS_Store"))


def run(ws, old_root, take_projects):
    """the import. `ws` must not already carry a landed record of its own.

    Returns (ok, report_text).
    """
    old_root = os.path.abspath(os.path.expanduser(old_root))
    old_journal = _record_of(old_root)
    if old_journal is None:
        return False, "no record at %s — is that really a workshop?" % old_root
    new_journal = journal.path(ws)
    if os.path.exists(new_journal):
        events, _ = journal.read(ws)
        if any(e.get("op") == "assert" for e in events):
            return False, ("this workshop already has a record — import fills "
                           "an empty one and never merges selves")
    lines = []

    # 1 · the record, verbatim. The old genesis stays the genesis.
    os.makedirs(os.path.dirname(new_journal), exist_ok=True)
    shutil.copy2(old_journal, new_journal)
    old_events, old_scars = journal.read(ws)
    lines.append("the record came whole: %d event(s), continuous since its genesis"
                 % len(old_events))
    if old_scars:
        lines.append("%d torn line(s) rode along, scarred as they were — nothing hidden"
                     % len(old_scars))

    # 2 · the path-map: old receipts open at new addresses.
    old_projects = _old_projects_dir(old_root) or os.path.join(old_root, "channels")
    update.set_path_map(ws, _carried_map(old_root, ws) + [
        (old_projects, os.path.join(ws, project.DIRNAME)),
        (old_root, ws),
    ])
    lines.append("path-map written: old receipts open at their new addresses")

    # 3 · chosen projects arrive live, histories and all.
    carried, skipped = [], []
    for name in take_projects:
        src = os.path.join(old_projects, name)
        cpath = _old_contract(src)
        if cpath is None:
            skipped.append("%s (no contract found)" % name)
            continue
        c = project.parse_contract(cpath)
        dest = project.dirpath(ws, name)
        if os.path.exists(dest):
            skipped.append("%s (already lives here)" % name)
            continue
        root = c.get("root")
        keep_root = None
        if root:
            asis = os.path.abspath(os.path.expanduser(root))
            if os.path.isdir(asis) and not asis.startswith(old_root + os.sep):
                # The root lives OUTSIDE the old workshop (its own repo, its
                # own life) — the project directory comes, the root: line
                # stays, and nothing external is moved in.
                keep_root = asis
                _copy_tree(src, dest)
            else:
                rootp = _relocate(asis, old_root)
                if rootp:
                    # The work moves IN: the project directory becomes the work.
                    _copy_tree(rootp, dest)
                else:
                    skipped.append("%s (its root %s is gone)" % (name, root))
                    continue
        else:
            _copy_tree(src, dest)
        # A fresh contract in the new shape; checks carried, ratification void.
        with open(project.contract_path(ws, name), "w", encoding="utf-8") as f:
            f.write("# %s\ngoal: %s\nstate: %s\n" % (name, c["goal"], c["state"]))
            if keep_root:
                f.write("root: %s\n" % keep_root)
            f.write("\n## checks\n%s\n%s\n\n## notes\n"
                    % (project.CHECKS_HINT, "\n".join(c["checks"])))
        if keep_root:
            # the root came with the project and kept its own life; the two
            # briefs say which project this directory belongs to, and neither
            # is written over a page that is already there.
            lines.extend(project.write_briefs(ws, name, keep_root))
        carried.append(name)
    if carried:
        lines.append("live projects: %s" % ", ".join(carried))
    for s in skipped:
        lines.append("skipped: %s" % s)

    # 4 · saved builds keep their cards.
    for shelf_dir in OLD_SHELF_DIRS:
        src_base = os.path.join(old_root, shelf_dir)
        if not os.path.isdir(src_base):
            continue
        for name in sorted(os.listdir(src_base)):
            src = os.path.join(src_base, name)
            card = next((c for c in OLD_CARDS
                         if os.path.exists(os.path.join(src, c))), None)
            if card is None:
                continue
            dest = os.path.join(ws, "shelf", name)
            if os.path.exists(dest):
                continue
            _copy_tree(src, dest)
            if card != "BUILD.md":
                os.rename(os.path.join(dest, card), os.path.join(dest, "BUILD.md"))
            lines.append("build on the shelf: %s" % name)

    # 5 · the owner's own agents come along (never placed by the system, so
    #     updates will never touch them).
    old_agents = os.path.join(old_root, ".claude", "agents")
    if os.path.isdir(old_agents):
        dest = os.path.join(ws, ".claude", "agents")
        os.makedirs(dest, exist_ok=True)
        n = 0
        for name in sorted(os.listdir(old_agents)):
            s, d = os.path.join(old_agents, name), os.path.join(dest, name)
            if os.path.isfile(s) and not os.path.exists(d):
                shutil.copy2(s, d)
                n += 1
        if n:
            lines.append("your agents came along: %d" % n)

    # 6 · ratifications void, out loud.
    lines.append(update.void_ratifications(ws, "the move into this workshop")
                 if os.path.exists(os.path.join(ws, journal.STATE_DIR, "ratified.json"))
                 else "no carried ratifications — each project's checks await your first k here")

    # 7 · what did not come, said plainly.
    old_staging = os.path.join(old_root, journal.STATE_DIR, "staging.jsonl")
    if os.path.exists(old_staging) and os.path.getsize(old_staging) > 0:
        lines.append("the old workshop still holds staged drafts, and they stayed "
                     "there — land them at the old one, or they die with it")
    lines.append("everything not chosen stays in %s — the cold store, yours to keep or delete"
                 % old_root)
    return True, "\n".join(lines)
