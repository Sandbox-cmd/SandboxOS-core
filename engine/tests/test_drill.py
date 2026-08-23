# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the continuous drill: one workshop lives a whole life in one test —
boot, build, land, ship, save, share, fetch, install, update. If the shapes
disagree anywhere, this is where it shows."""
import os
import tempfile
import unittest

from engine import (apps, gate, journal, make, notes, onboard, project,
                    share, shelf, ship, status, update)
from engine.tests import elsewhere_home, key, pressing, quiet
from engine.tests.test_app import make_app


class TestTheWholeLife(unittest.TestCase):
    def test_a_workshop_lives(self):
        ws = tempfile.mkdtemp(prefix="sbx8life-")

        # boot
        ok, text = onboard.run(ws)
        self.assertTrue(ok, text)
        with elsewhere_home():
            healthy, lines = status.doctor(ws)
        self.assertTrue(healthy, "\n".join(lines))
        self.assertIn("nothing needs you.", status.status(ws))

        # a project, a build pass, a landed note
        ok, _ = project.new(ws, "geardoor", "the store's data")
        self.assertTrue(ok)
        project.switch(ws, "geardoor", True)
        make.open_session(ws, "geardoor", "add the tax table")
        root = project.root_of(ws, "geardoor")
        with open(os.path.join(root, "tax.json"), "w") as f:
            f.write('{"rate": 0.05}\n')
        ok, msg = make.close_session(ws, "geardoor", "tax table added")
        self.assertTrue(ok)
        notes.note(ws, "the tax rule is 5 percent", target_project="geardoor")
        said = []
        with pressing("k"):
            rc = notes.approve(ws, out=said.append)
        self.assertEqual(rc, 0)
        self.assertTrue(said[-1].startswith("landed 2 (shown "),  # note + summary
                        said[-1])
        self.assertEqual(len(notes.recall(ws, "tax rule")), 1)

        # checks, ratify, ship — then a headless re-ship
        cpath = project.contract_path(ws, "geardoor")
        base = open(cpath).read().split("## checks")[0]
        open(cpath, "w").write(base + "## checks\npython3 -c \"import json; json.load(open('tax.json'))\"\n")
        with pressing():
            ok, msg = ship.ship(ws, "geardoor", quiet)
        self.assertTrue(ok, msg)
        ok, msg = ship.ship(ws, "geardoor", quiet)   # ratified — no key again
        self.assertTrue(ok, msg)

        # save a build, share it, and a second workshop fetches it
        ok, _ = shelf.save(ws, os.path.join(root, "tax.json"), note="the tax table")
        self.assertTrue(ok)
        staging = tempfile.mkdtemp(prefix="sbx8stg-")
        ok, msg = share.share(ws, "tax.json", staging)
        self.assertTrue(ok, msg)
        friend = tempfile.mkdtemp(prefix="sbx8friend-")
        ok, _ = onboard.run(friend)
        self.assertTrue(ok)
        ok, msg = share.fetch(friend, staging, "tax.json", key())
        self.assertTrue(ok, msg)
        self.assertEqual(shelf.card(friend, "tax.json")["origin"], "external")

        # the friend installs an app
        d = make_app(checks=["true"])
        ok, msg = apps.install(friend, d, key())
        self.assertTrue(ok, msg)

        # both workshops take an update pass and still open everything
        for w in (ws, friend):
            ok, text = update.run(w)
            self.assertTrue(ok, text)
            events, scars = journal.read(w)
            self.assertEqual(scars, [])
            with elsewhere_home():
                healthy, lines = status.doctor(w)
            self.assertTrue(healthy, "\n".join(lines))
        self.assertEqual(len(notes.recall(ws, "tax rule")), 1)  # nothing lost


if __name__ == "__main__":
    unittest.main()
