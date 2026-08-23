# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""apps: big add-ons that install honestly and remove exactly.

An app is a directory with APP.md (name, semver version, min core version,
description, declared placements, checks) and a payload. Install: compat
gate first (refuse honestly on skew), hashes verified, placements checked
against the allowlist IN CODE (the seam has no door — challenge #3), the
manifest shown, the keystroke taken, placements executed and recorded, and
the app's own checks run with the results shown. Remove consumes the
placement record and removes exactly that. Identity is source/name — no
app claims a bare official name.
"""
import json
import os
import shutil

from . import gate, journal, shelf


def verify_entry(source, name):
    """the pin check an app install runs, which is the shelf's own.

    An app and a build are pinned the same way by the same hash, so the index
    reader that used to sit beside `--catalog` retired into `shelf`: one
    function answers for every door, and there is no second implementation to
    disagree with it.
    """
    return shelf.verify_entry(source, name)


def resolve_install(given, catalog=None):
    """where an install reads from: (app_dir, source, refusal).

    A bare path is its own answer and lands as `local`. With `--catalog` the
    name is looked up in the index and its payload hash must match the pin
    before the directory is handed back — one door, one check.
    """
    if not catalog:
        return given, "local", None
    app_dir, pinned, why = verify_entry(catalog, given)
    if not pinned:
        return None, None, why
    return app_dir, "catalog:%s" % given, None


def entry_for(app_dir):
    """what a keeper adds to an index for this app — printed, never pushed."""
    m = parse_manifest(app_dir)
    return {m["name"]: {"path": os.path.join("apps", m["name"]),
                        "version": m["version"],
                        "sha256": shelf.payload_hash(app_dir)}}


def _book_dir(ws):
    return os.path.join(ws, journal.STATE_DIR, "apps")


def _apps_dir(ws):
    return os.path.join(ws, "apps")


def parse_manifest(app_dir):
    p = os.path.join(app_dir, "APP.md")
    if not os.path.exists(p):
        return None
    out = {"name": None, "version": None, "min_core": None, "description": "",
           "placements": [], "checks": []}
    section = None
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("# "):
                out["name"] = line[2:].strip()
            elif line.startswith("version:"):
                out["version"] = line.split(":", 1)[1].strip()
            elif line.startswith("min-core:"):
                out["min_core"] = line.split(":", 1)[1].strip()
            elif line.startswith("description:"):
                out["description"] = line.split(":", 1)[1].strip()
            elif line.startswith("## "):
                section = line[3:].strip().lower()
            elif section in ("placements", "checks") and line.strip() \
                    and not line.startswith("#"):
                out[section].append(line.strip())
    return out


def _semver(v):
    try:
        return tuple(int(x) for x in (v or "0.0.0").split("."))
    except ValueError:
        return None


def placement_allowed(ws, app_name, rel):
    """the allowlist, in code. Only the app's own room and nothing clever.
    A line ending in '/' places that whole payload subtree."""
    if os.path.isabs(rel) or rel.startswith("~"):
        return False, "absolute paths never place"
    parts = [p for p in rel.replace("\\", "/").split("/") if p]
    if ".." in parts:
        return False, "'..' never places"
    if parts[0] != "apps" or len(parts) < 2 or parts[1] != app_name:
        return False, "an app places only under apps/%s/" % app_name
    return True, ""


def _expand(app_dir, name, placements):
    """directory placements ('.../') expand to their payload files.
    Returns (files, error) where files are rel placement paths."""
    out = []
    for rel in placements:
        inner = os.path.relpath(rel.rstrip("/"), os.path.join("apps", name))
        src = os.path.join(app_dir, "payload", inner)
        if rel.endswith("/"):
            if not os.path.isdir(src):
                return None, "the manifest names %r but the payload does not carry it" % rel
            for dirpath, dirnames, filenames in os.walk(src):
                dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
                for n in filenames:
                    out.append(os.path.join(
                        rel.rstrip("/"),
                        os.path.relpath(os.path.join(dirpath, n), src)))
        else:
            if not os.path.exists(src):
                return None, "the manifest names %r but the payload does not carry it" % rel
            out.append(rel)
    return out, None


def install(ws, app_dir, consent, source="local"):
    from . import update
    m = parse_manifest(app_dir)
    if m is None:
        return False, "no APP.md at %s — not an app" % app_dir
    name = m["name"]
    if not name or not _semver(m["version"]):
        return False, "the manifest needs a name and a semver version"
    core = _semver(update.core_version())
    need = _semver(m["min_core"] or "0.0.0")
    if need is None or core < need:
        return False, ("%s needs core %s or newer — this is %s. update first, then install."
                       % (name, m["min_core"], update.core_version()))
    if not m["placements"]:
        return False, "the manifest declares no placements — nothing to install"
    for rel in m["placements"]:
        ok, why = placement_allowed(ws, name, rel)
        if not ok:
            return False, "placement refused by code, before your key: %r — %s" % (rel, why)
    files, err = _expand(app_dir, name, m["placements"])
    if err:
        return False, err
    if os.path.exists(os.path.join(_book_dir(ws), name + ".json")):
        return False, "an app named %s is already installed — remove it first" % name

    if source.startswith("catalog:"):
        trust = "source: the official catalog — pinned by its index"
    else:
        # surface: 26
        trust = ("source: UNVERIFIED — %s is not the catalog. the hash proves "
                 "the bytes are the same bytes, not who wrote them." % source)
    face = ["%s %s — %s" % (name, m["version"], m["description"]),
            trust,
            "places %d file(s), all under apps/%s/" % (len(files), name)]
    if not consent or consent.get("source") != "tty" or consent.get("key") != gate.COMMIT_KEY:
        return False, "\n".join(face + ["installing needs your %r at a real terminal" % gate.COMMIT_KEY])

    placed = []
    for rel in files:
        inner = os.path.relpath(rel, os.path.join("apps", name))
        src = os.path.join(app_dir, "payload", inner)
        dest = os.path.join(ws, rel)
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        placed.append(dest)
    os.makedirs(_book_dir(ws), exist_ok=True)
    with open(os.path.join(_book_dir(ws), name + ".json"), "w", encoding="utf-8") as f:
        json.dump({"name": name, "version": m["version"], "source": source,
                   "placed": placed}, f, indent=1)
    journal.append(ws, {"op": "place", "action": "app-installed", "path": name,
                        "origin": "external" if source != "local" else "machine",
                        "body": "%s %s from %s" % (name, m["version"], source)})

    lines = face + ["installed."]
    if m["checks"]:
        import subprocess
        lines.append("the app's own checks:")
        for check in m["checks"]:
            r = subprocess.run(check, shell=True, cwd=os.path.join(ws, "apps", name),
                               capture_output=True, text=True, timeout=60)
            lines.append("  %s %s" % ("ok  " if r.returncode == 0 else "FAIL", check))
    return True, "\n".join(lines)


def remove(ws, name):
    """exactly what was placed, nothing else."""
    book = os.path.join(_book_dir(ws), name + ".json")
    if not os.path.exists(book):
        return False, "no app named %s is installed" % name
    with open(book, encoding="utf-8") as f:
        rec = json.load(f)
    gone = 0
    for path in rec["placed"]:
        if os.path.exists(path):
            os.remove(path)
            gone += 1
    appdir = os.path.join(_apps_dir(ws), name)
    if os.path.isdir(appdir) and not any(files for _, _, files in os.walk(appdir)):
        shutil.rmtree(appdir)
    os.remove(book)
    journal.append(ws, {"op": "place", "action": "app-removed", "path": name,
                        "origin": "machine", "body": "removed %s (%d file(s))" % (name, gone)})
    return True, "removed %s — %d file(s), exactly the ones its install placed" % (name, gone)


def list_installed(ws):
    d = _book_dir(ws)
    if not os.path.isdir(d):
        return []
    out = []
    for n in sorted(os.listdir(d)):
        with open(os.path.join(d, n), encoding="utf-8") as f:
            out.append(json.load(f))
    return out
