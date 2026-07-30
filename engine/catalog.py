# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The official catalog: a git repo of apps, each pinned by hash.

The catalog is a directory (clone it however you like) holding index.json
and the apps themselves. Every index entry pins its app's payload hash;
`verify` recomputes and compares before anything is called official. A
catalog answer upgrades install's trust label from UNVERIFIED to pinned —
and a catalog whose bytes disagree with its own index is named for what it
is, loudly.
"""
import json
import os

from . import shelf

INDEX = "index.json"


def load(catalog_dir):
    p = os.path.join(catalog_dir, INDEX)
    if not os.path.exists(p):
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def app_hash(app_dir):
    """One hash over the whole app dir (APP.md + payload), manifest-style."""
    return shelf.payload_hash(app_dir)


def verify(catalog_dir, name):
    """Returns (app_dir, ok, message)."""
    idx = load(catalog_dir)
    if idx is None:
        return None, False, "no index.json at %s — not a catalog" % catalog_dir
    entry = (idx.get("apps") or {}).get(name)
    if entry is None:
        return None, False, "the catalog does not list %r" % name
    app_dir = os.path.join(catalog_dir, entry.get("path", os.path.join("apps", name)))
    if not os.path.isdir(app_dir):
        return None, False, "the index lists %r but the directory is missing" % name
    actual = app_hash(app_dir)
    if actual != entry.get("sha256"):
        return app_dir, False, ("the catalog's own bytes disagree with its index for %r "
                                "(%s… vs %s…) — trust neither, tell the catalog's keeper"
                                % (name, actual[:12], (entry.get("sha256") or "")[:12]))
    return app_dir, True, "pinned by the catalog index"


def entry_for(app_dir):
    """What a keeper adds to index.json for this app — printed, never pushed."""
    from . import apps
    m = apps.parse_manifest(app_dir)
    return {m["name"]: {"path": os.path.join("apps", m["name"]),
                        "version": m["version"],
                        "sha256": app_hash(app_dir)}}
