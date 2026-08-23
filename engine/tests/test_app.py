# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""apps: the compat gate refuses honestly, the allowlist has no door,
removal is exact."""
import os
import tempfile
import unittest

from engine import apps, gate, journal

from . import REPO, key


def make_app(name="tuner", version="1.0.0", min_core="8.0.0",
             placements=None, checks=()):
    d = tempfile.mkdtemp(prefix="sbx8app-")
    placements = placements if placements is not None else ["apps/%s/tuner.py" % name]
    with open(os.path.join(d, "APP.md"), "w") as f:
        f.write("# %s\nversion: %s\nmin-core: %s\ndescription: a test app\n" %
                (name, version, min_core))
        f.write("\n## placements\n" + "\n".join(placements) + "\n")
        if checks:
            f.write("\n## checks\n" + "\n".join(checks) + "\n")
    os.makedirs(os.path.join(d, "payload"), exist_ok=True)
    for rel in placements:
        inner = os.path.relpath(rel, os.path.join("apps", name))
        p = os.path.join(d, "payload", inner)
        try:
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w") as f:
                f.write("print('hi')\n")
        except OSError:
            pass  # a bad-on-purpose placement can't build a payload — the
            #       engine must refuse them before ever touching one
    return d


class TestApps(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)

    def test_install_needs_key_then_places_and_runs_checks(self):
        d = make_app(checks=["true"])
        ok, msg = apps.install(self.ws, d, None)
        self.assertFalse(ok)
        self.assertIn("real terminal", msg)
        ok, msg = apps.install(self.ws, d, key())
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.exists(os.path.join(self.ws, "apps", "tuner", "tuner.py")))
        self.assertIn("ok   true", msg)

    def test_compat_gate_refuses_honestly(self):
        d = make_app(min_core="99.0.0")
        ok, msg = apps.install(self.ws, d, key())
        self.assertFalse(ok)
        self.assertIn("needs core 99.0.0", msg)

    def test_placement_allowlist_has_no_door(self):
        for bad in (["/etc/evil"], ["apps/other/file.py"], ["apps/tuner/../../CLAUDE.md"],
                    [".claude/settings.json"]):
            d = make_app(placements=bad)
            ok, msg = apps.install(self.ws, d, key())
            self.assertFalse(ok, bad)
            self.assertIn("refused by code, before your key", msg)

    def test_manifest_naming_uncarried_payload_refused(self):
        d = make_app()
        os.remove(os.path.join(d, "payload", "tuner.py"))
        ok, msg = apps.install(self.ws, d, key())
        self.assertFalse(ok)
        self.assertIn("does not carry it", msg)

    def test_remove_is_exact(self):
        d = make_app()
        apps.install(self.ws, d, key())
        mine = os.path.join(self.ws, "apps", "tuner", "my-notes.md")
        open(mine, "w").write("mine, not the app's\n")
        ok, msg = apps.remove(self.ws, "tuner")
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(os.path.join(self.ws, "apps", "tuner", "tuner.py")))
        self.assertTrue(os.path.exists(mine))  # exactly what install placed, nothing else
        self.assertEqual(apps.list_installed(self.ws), [])

    def test_directory_placement_expands(self):
        d = make_app(name="kit", placements=["apps/kit/"])
        os.makedirs(os.path.join(d, "payload", "sub"), exist_ok=True)
        open(os.path.join(d, "payload", "a.py"), "w").write("a\n")
        open(os.path.join(d, "payload", "sub", "b.py"), "w").write("b\n")
        ok, msg = apps.install(self.ws, d, key())
        self.assertTrue(ok, msg)
        self.assertTrue(os.path.exists(os.path.join(self.ws, "apps", "kit", "a.py")))
        self.assertTrue(os.path.exists(os.path.join(self.ws, "apps", "kit", "sub", "b.py")))
        ok, msg = apps.remove(self.ws, "kit")
        self.assertTrue(ok)
        self.assertFalse(os.path.exists(os.path.join(self.ws, "apps", "kit", "sub", "b.py")))

    def _pinned_source(self):
        """an index-shaped source, the way a keeper writes one."""
        import json
        import shutil as _sh
        d = make_app(name="tuner")
        cat = tempfile.mkdtemp(prefix="sbx8cat-")
        appdir = os.path.join(cat, "apps", "tuner")
        _sh.copytree(d, appdir)
        with open(os.path.join(cat, "index.json"), "w") as f:
            json.dump({"apps": apps.entry_for(appdir)}, f)
        return cat, appdir

    def test_a_pin_upgrades_trust_and_tamper_is_named(self):
        """the catalog reader retired: `engine/catalog.py` is gone and the one
        pin check lives in `shelf.verify_entry`, which serves a build and an
        app alike. --catalog keeps working, through that."""
        cat, appdir = self._pinned_source()
        app_dir, pinned, why = apps.verify_entry(cat, "tuner")
        self.assertTrue(pinned, why)
        ok, msg = apps.install(self.ws, app_dir, key(), source="catalog:tuner")
        self.assertTrue(ok)
        self.assertIn("pinned by its index", msg)
        apps.remove(self.ws, "tuner")
        with open(os.path.join(appdir, "payload", "tuner.py"), "a") as f:
            f.write("# tamper\n")
        app_dir, pinned, why = apps.verify_entry(cat, "tuner")
        self.assertFalse(pinned)
        self.assertIn("disagree", why)

    def test_the_one_reader_is_the_shelf_and_there_is_no_second(self):
        from engine import shelf
        cat, _appdir = self._pinned_source()
        self.assertEqual(apps.verify_entry(cat, "tuner"),
                         shelf.verify_entry(cat, "tuner"))
        self.assertFalse(os.path.exists(
            os.path.join(REPO, "engine", "catalog.py")))

    def test_a_source_that_lists_nothing_says_so(self):
        _dir, pinned, why = apps.verify_entry(
            tempfile.mkdtemp(prefix="sbx8cat-"), "tuner")
        self.assertFalse(pinned)
        self.assertIn("lists", why)

    def test_double_install_refused(self):
        d = make_app()
        apps.install(self.ws, d, key())
        ok, msg = apps.install(self.ws, d, key())
        self.assertFalse(ok)
        self.assertIn("already installed", msg)


if __name__ == "__main__":
    unittest.main()
