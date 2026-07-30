# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""share / fetch — builds travel between workshops, honestly.

Share stages a build for the shelf repo: the scrub runs first (person-clean,
deny-list, unscannables named for your ack), the export never carries git
history, and the push is the owner's hand — always. Fetch pulls from a
shelf-shaped source: bytes are hash-verified against the card BEFORE the
keystroke, the source is labeled honestly (a matching hash proves internal
consistency, not authenticity — only a catalog pin proves the source), and
what lands is marked origin: external so provenance never launders.
"""
import os
import shutil

from . import clean, gate, journal, shelf


def share(ws, build_name, staging_root):
    """Scrub + stage one build in shelf shape. Returns (ok, message)."""
    c = shelf.card(ws, build_name)
    if c is None:
        return False, "no build named %s on the shelf" % build_name
    src_dir = os.path.join(ws, shelf.DIRNAME, build_name)
    report = clean.scan(src_dir)
    if report["hits"] or report["denied"]:
        lines = ["the scrub refused — person data would ship:"]
        for rel, needle in report["hits"]:
            lines.append("  %s (%s)" % (rel, needle))
        for rel in report["denied"]:
            lines.append("  %s (deny-listed — never ships)" % rel)
        return False, "\n".join(lines)
    dest = os.path.join(staging_root, "builds", build_name)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    export_report = clean.fresh_export(src_dir, dest)
    lines = ["staged for the shelf: %s" % dest]
    if not report["terms_loaded"]:
        lines.append("note: no private-terms file — only the floor scrub ran; "
                     "set %s to scan for your own terms" % clean.TERMS_ENV)
    if export_report["unscannable"]:
        lines.append("unscannable files (your eyes owe them a look before you push):")
        for rel in export_report["unscannable"]:
            lines.append("  " + rel)
    lines.append("the push is your hand — nothing left this machine.")
    return True, "\n".join(lines)


def list_source(source):
    """Cards available in a shelf-shaped source directory."""
    base = os.path.join(source, "builds")
    if not os.path.isdir(base):
        return []
    out = []
    for name in sorted(os.listdir(base)):
        p = os.path.join(base, name, "BUILD.md")
        if os.path.exists(p):
            out.append(name)
    return out


def fetch(ws, source, name, consent, catalog_verified=False):
    """Pull one build. Hash before keystroke; source labeled honestly."""
    src_dir = os.path.join(source, "builds", name)
    card_path = os.path.join(src_dir, "BUILD.md")
    if not os.path.exists(card_path):
        return False, "no build named %s at %s" % (name, source)
    fields = {}
    for line in open(card_path, encoding="utf-8"):
        for f in ("sha256", "note"):
            if line.startswith(f + ":"):
                fields[f] = line.split(":", 1)[1].strip()
    entries = [e for e in os.listdir(src_dir) if e != "BUILD.md" and not e.startswith(".")]
    if len(entries) != 1:
        return False, "the card at the source is torn — expected one payload, found %d" % len(entries)
    payload = os.path.join(src_dir, entries[0])
    actual = shelf.payload_hash(payload)
    if actual != fields.get("sha256"):
        return False, ("the bytes do not match the card (%s… vs %s…) — nothing fetched"
                       % (actual[:12], (fields.get("sha256") or "")[:12]))
    trust = ("source: the official catalog (pinned)" if catalog_verified
             else "source: UNVERIFIED — the hash proves the card matches its own "
                  "bytes, not who made them")
    if not consent or consent.get("source") != "tty" or consent.get("key") != gate.COMMIT_KEY:
        return False, ("%s\nhash checks out. fetching needs your %r at a real terminal."
                       % (trust, gate.COMMIT_KEY))
    dest = os.path.join(ws, shelf.DIRNAME, name)
    if os.path.exists(dest):
        return False, "a build named %s is already on your shelf" % name
    shutil.copytree(src_dir, dest)
    # The card's origin becomes external here — provenance never launders.
    cpath = os.path.join(dest, "BUILD.md")
    text = open(cpath, encoding="utf-8").read()
    if "origin:" in text:
        text = "\n".join(("origin: external" if l.startswith("origin:") else l)
                         for l in text.splitlines()) + "\n"
    else:
        text += "origin: external\n"
    open(cpath, "w", encoding="utf-8").write(text)
    event = {"op": "assert", "cls": "build-kept", "origin": "external",
             "body": "fetched: %s (%s)" % (name, "catalog" if catalog_verified else "unverified source"),
             "ink": "receipted", "receipt": cpath}
    if consent.get("synthetic"):
        event["hand"] = "synthetic"
    journal.append(ws, event)
    return True, "%s\nfetched %s — on your shelf, origin: external" % (trust, name)
