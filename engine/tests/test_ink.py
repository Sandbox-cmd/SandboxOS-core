# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the three rungs: claimed, receipted, checked — and who is allowed to say so.

Nothing writes its own rung. Two of the three are computed at landing from
what can be opened; the third is reached by a run and raised at the read, so
a landed line is never rewritten and the record can still tell you that a
year-old claim has since been proved.
"""
import ast
import os
import tempfile
import unittest

from engine import check, desk, journal, notes, project, registry

from . import REPO, pressing


class TestTheRaise(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")

    def landed(self, body):
        notes.note(self.ws, body, target_project="geardoor")
        with pressing("k"):
            notes.approve(self.ws, out=lambda *_: None)
        events, _ = journal.read(self.ws)
        return [e for e in events if e.get("body") == body][0]

    def seen(self, eid):
        world = registry.project(self.ws)
        return next(x for x in world["note"] if x["id"] == eid)

    def stored(self, eid):
        events, _ = journal.read(self.ws)
        return next(e for e in events if e.get("id") == eid)

    def test_checked_is_only_ever_raised_by_a_check_event(self):
        fact = self.landed("the tax rule is 5 percent")
        self.assertEqual(self.seen(fact["id"])["ink"], "claimed")
        run = journal.append(self.ws, {"op": "check", "project": "geardoor",
                                       "green": 1, "proves": [fact["id"]],
                                       "hash": "abc"})
        raised = self.seen(fact["id"])
        self.assertEqual(raised["ink"], "checked")
        self.assertEqual(raised["proved_by"], run["id"])
        # the stored line is untouched: the rung lives in the read.
        self.assertEqual(raised["ink_landed"], "claimed")
        self.assertEqual(self.stored(fact["id"])["ink"], "claimed")

    def test_a_red_run_raises_nothing(self):
        fact = self.landed("a claim nobody has run")
        journal.append(self.ws, {"op": "check", "project": "geardoor",
                                 "green": 0, "proves": [], "hash": "abc"})
        self.assertEqual(self.seen(fact["id"])["ink"], "claimed")

    def test_recall_and_canon_both_read_the_raised_rung(self):
        fact = self.landed("the prefix is per brand")
        journal.append(self.ws, {"op": "check", "project": "geardoor", "green": 1,
                                 "proves": [fact["id"]], "hash": "abc"})
        notes.refresh_canon(self.ws, "geardoor")
        self.assertIn("[checked] [machine] the prefix is per brand",
                      notes.recall(self.ws, "prefix")[0])
        with open(os.path.join(project.dirpath(self.ws, "geardoor"), "CANON.md"),
                  encoding="utf-8") as f:
            self.assertIn("- [checked] [machine] the prefix is per brand", f.read())

    def test_the_record_refuses_a_line_that_marks_itself_checked(self):
        with self.assertRaises(ValueError):
            journal.append(self.ws, {"op": "assert", "body": "i am checked",
                                     "ink": "checked"})
        with self.assertRaises(ValueError):
            desk.mint(self.ws, {"body": "so am i", "ink": "checked"})
        disp, msg = desk.submit(self.ws, {"body": "and me", "ink": "checked"})
        self.assertEqual(disp, "refused")

    def test_a_run_end_to_end_moves_the_rung_and_leaves_the_line_alone(self):
        with open(project.contract_path(self.ws, "geardoor"), "a", encoding="utf-8") as f:
            f.write("\n## checks\ntrue\n")
        fact = self.landed("the door closes on its own")
        with open(journal.path(self.ws), "rb") as fh:
            before = fh.read()
        ok, _ = check.run(self.ws, "geardoor")
        self.assertTrue(ok)
        self.assertEqual(self.seen(fact["id"])["ink"], "checked")
        with open(journal.path(self.ws), "rb") as fh:
            after = fh.read()
        self.assertTrue(after.startswith(before), "a landed line was rewritten")


class TestTheStrike(unittest.TestCase):
    """an invalidate is a second thought, not an eraser."""

    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor")
        notes.note(self.ws, "the count is 12", target_project="geardoor")
        with pressing("k"):
            notes.approve(self.ws, out=lambda *_: None)
        events, _ = journal.read(self.ws)
        self.fact = [e for e in events if e.get("body") == "the count is 12"][0]

    def strike(self, why="the count was wrong"):
        notes.strike(self.ws, self.fact["id"], why)
        with pressing("k"):
            notes.approve(self.ws, out=lambda *_: None)

    def test_recall_shows_struck_and_canon_leaves_it_out(self):
        self.strike()
        self.assertEqual(notes.recall(self.ws, "the count")[0],
                         "[struck] [machine] the count is 12")
        notes.refresh_canon(self.ws, "geardoor")
        with open(os.path.join(project.dirpath(self.ws, "geardoor"), "CANON.md"),
                  encoding="utf-8") as f:
            self.assertNotIn("the count is 12", f.read())

    def test_the_original_line_is_never_deleted(self):
        with open(journal.path(self.ws), "rb") as fh:
            before = fh.read()
        self.strike()
        with open(journal.path(self.ws), "rb") as fh:
            after = fh.read()
        self.assertTrue(after.startswith(before))
        events, _ = journal.read(self.ws)
        self.assertEqual(
            len([e for e in events if e.get("id") == self.fact["id"]]), 1)

    def test_the_strike_names_who_and_why(self):
        self.strike("the count was wrong")
        world = registry.project(self.ws)
        seen = next(x for x in world["note"] if x["id"] == self.fact["id"])
        self.assertEqual(seen["invalidated_why"], "the count was wrong")
        events, _ = journal.read(self.ws)
        mark = [e for e in events if e.get("op") == "invalidate"][0]
        self.assertEqual(mark["of"], self.fact["id"])
        self.assertEqual(seen["invalidated_by"], mark["id"])

    def test_a_strike_needs_the_key_like_everything_else(self):
        notes.strike(self.ws, self.fact["id"], "not yet approved")
        events, _ = journal.read(self.ws)
        self.assertEqual([e for e in events if e.get("op") == "invalidate"], [])
        self.assertEqual(len(desk.drafts(self.ws)[0]), 1)

    def test_a_line_nobody_can_find_is_refused(self):
        target, msg = notes.strike(self.ws, "eid-nosuchline", "why")
        self.assertIsNone(target)
        self.assertIn("nothing on the record carries that id", msg)

    def test_a_struck_ruling_stops_standing(self):
        journal.append(self.ws, {"op": "assert", "cls": "ruling", "project": "geardoor",
                                 "body": "teal accents", "stratum": "taste"})
        events, _ = journal.read(self.ws)
        ruling = [e for e in events if e.get("cls") == "ruling"][0]
        self.assertEqual(len(notes.rulings(self.ws, "geardoor")), 1)
        journal.append(self.ws, {"op": "invalidate", "of": ruling["id"],
                                 "body": "never ruled"})
        self.assertEqual(notes.rulings(self.ws, "geardoor"), [])


class TestOneFunctionComputesIt(unittest.TestCase):
    """every rung in the engine comes out of `desk.compute_ink`."""

    def _engine_sources(self):
        engine = os.path.join(REPO, "engine")
        for name in sorted(os.listdir(engine)):
            if name.endswith(".py"):
                path = os.path.join(engine, name)
                with open(path, encoding="utf-8") as fh:
                    yield name, fh.read()

    # the needle is assembled, not written, so this file passes its own grep.
    NEEDLE = '"ink"' + ': ' + '"checked"'

    def test_no_source_line_writes_the_third_rung(self):
        """the experience spec's grep, run as a check: nothing outside the
        suite's own fixtures puts the third rung on a line."""
        for name, text in self._engine_sources():
            for lineno, line in enumerate(text.splitlines(), 1):
                self.assertTrue(self.NEEDLE not in line,
                                "engine/%s:%d writes the rung" % (name, lineno))

    def test_no_organ_hands_a_rung_to_the_record(self):
        """a mint carries a receipt and lets one function read it; an organ
        that names its own rung is the pattern this closes."""
        for name, text in self._engine_sources():
            if name in ("desk.py", "registry.py"):
                continue  # the one writer, and the read over it
            tree = ast.parse(text, name)
            for node in ast.walk(tree):
                if not (isinstance(node, ast.Call)
                        and isinstance(node.func, ast.Attribute)):
                    continue
                fn = node.func
                if not (isinstance(fn.value, ast.Name)
                        and (fn.value.id, fn.attr) in (("journal", "append"),
                                                       ("desk", "mint"))):
                    continue
                for a in node.args:
                    if isinstance(a, ast.Dict):
                        keys = [k.value for k in a.keys
                                if isinstance(k, ast.Constant)]
                        self.assertNotIn("ink", keys,
                                         "engine/%s names its own rung" % name)


if __name__ == "__main__":
    unittest.main()
