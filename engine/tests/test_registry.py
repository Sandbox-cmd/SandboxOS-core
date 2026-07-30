# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The registry: typed, projection-only, and its schema keeps its promises."""
import os
import tempfile
import unittest

from engine import journal, registry


class TestSchema(unittest.TestCase):
    def test_every_declared_type_present(self):
        for t in ("project", "build", "app", "note", "ruling", "check",
                  "session", "event"):
            self.assertIn(t, registry.TYPES)
            self.assertTrue(registry.TYPES[t]["description"])

    def test_links_reference_declared_types(self):
        names = set(registry.TYPES) | {"workshop", "any"}
        for frm, link, to, rev in registry.LINKS:
            self.assertIn(frm, names, link)
            self.assertIn(to, names, link)
            self.assertTrue(rev, link)

    def test_ruling_carries_stratum_and_supersession(self):
        self.assertIn("stratum", registry.TYPES["ruling"]["fields"])
        self.assertIn("supersedes", registry.TYPES["ruling"]["fields"])
        self.assertEqual(registry.STRATA, ("law", "taste"))

    def test_fact_shape_refuses_unknown_status(self):
        f = registry.fact("x", "human", "checked", receipt="journal:eid-1")
        self.assertEqual(f["ink"], "checked")
        with self.assertRaises(ValueError):
            registry.fact("x", "vibes", "checked")
        with self.assertRaises(ValueError):
            registry.fact("x", "human", "definitely-true")


class TestProjection(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)

    def test_projection_only_no_second_store(self):
        """Projecting writes nothing; two runs answer identically."""
        journal.append(self.ws, {"op": "assert", "cls": "note", "body": "a fact"})
        state_dir = os.path.join(self.ws, journal.STATE_DIR)
        before = sorted(os.listdir(state_dir))
        first = registry.project(self.ws)
        second = registry.project(self.ws)
        self.assertEqual(before, sorted(os.listdir(state_dir)))
        self.assertEqual(first, second)

    def test_rulings_project_with_stratum(self):
        journal.append(self.ws, {"op": "assert", "cls": "ruling",
                                 "body": "plain first", "stratum": "law"})
        journal.append(self.ws, {"op": "assert", "cls": "ruling",
                                 "body": "teal accents"})  # stratum defaults taste
        world = registry.project(self.ws)
        strata = {r["body"]: r["stratum"] for r in world["ruling"]}
        self.assertEqual(strata["plain first"], "law")
        self.assertEqual(strata["teal accents"], "taste")

    def test_newest_word_wins_chronology_kept(self):
        old = journal.append(self.ws, {"op": "assert", "cls": "ruling",
                                       "body": "curses stays"})
        journal.append(self.ws, {"op": "assert", "cls": "ruling",
                                 "body": "textual now", "supersedes": old["id"]})
        world = registry.project(self.ws)
        standing = registry.newest_word(world)
        self.assertEqual([r["body"] for r in standing], ["textual now"])
        self.assertEqual(len(world["ruling"]), 2)  # chronology never deleted

    def test_sessions_are_nameable(self):
        journal.append(self.ws, {"op": "session", "phase": "open",
                                 "key": "s1", "project": "geardoor"})
        journal.append(self.ws, {"op": "session", "phase": "close", "key": "s1"})
        world = registry.project(self.ws)
        self.assertEqual(len(world["session"]), 1)
        self.assertIsNotNone(world["session"][0]["closed"])

    def test_scars_surface_never_hide(self):
        with open(journal.path(self.ws), "a", encoding="utf-8") as f:
            f.write('{"op": "assert", "torn')
        world = registry.project(self.ws)
        self.assertEqual(len(world["_scars"]), 1)


if __name__ == "__main__":
    unittest.main()
