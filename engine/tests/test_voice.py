# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the voice lint, run from the suite: one list, read from the soul.

`engine/voicelint.py` holds the mechanism; this file says which of its
findings gate and which print. the split is the rule from lint.md: a check
that measures shape gates, a proxy for meaning reports.

three debts are pinned here as exact numbers rather than hidden behind a
loosened check. each names the pull that clears it. a debt that grows fails
this file the day it grows, and a debt that shrinks fails it too — which is
how the pin moves in the same commit as the words.
"""
import os
import re
import unittest

from engine import voicelint
from engine.tests import REPO, pins

FLOOR = 23  # today's tuple minus the ruled removal of `empower` (repair S3)


def _read(rel):
    with open(os.path.join(REPO, rel), encoding="utf-8") as fh:
        return fh.read()


class TestTheList(unittest.TestCase):
    """check A's parse: the list lives in the soul, with a reason per phrase."""

    def test_the_table_parses_with_a_reason_per_phrase(self):
        phrases = voicelint.forbidden_phrases()
        allscope = [p for p in phrases if p.scope == "all"]
        self.assertGreaterEqual(
            len(allscope), FLOOR,
            "the all-scope list is %d phrases; the floor is %d — a re-derive "
            "lost one by accident" % (len(allscope), FLOOR))
        for p in phrases:
            self.assertTrue(p.why.strip(), "%r reaches the list with no reason"
                            % p.phrase)
            self.assertIn(p.cls, ("hype", "filler", "mush", "service", "error",
                                  "emoji"), p.phrase)
            self.assertIn(p.scope, ("all", "error"), p.phrase)

    def test_a_phrase_with_no_reason_is_refused(self):
        """the parser fires: a row with an empty why raises, quoting the row."""
        import tempfile
        bad = os.path.join(tempfile.mkdtemp(prefix="voice-"), "voice.md")
        open(bad, "w", encoding="utf-8").write(
            "# x\n\n%s\n\n| phrase | class | scope | why |\n|---|---|---|---|\n"
            "| `zesty` | hype | all |  |\n" % voicelint.TABLE_HEADING)
        with self.assertRaises(ValueError):
            voicelint.forbidden_phrases(bad)

    def test_no_second_copy_of_the_list_in_the_tests(self):
        """the hard-coded CUT tuple is gone; every reader parses the soul."""
        for name in sorted(os.listdir(os.path.join(REPO, "engine", "tests"))):
            if not name.endswith(".py"):
                continue
            text = _read("engine/tests/" + name)
            needle = "CUT" + " = ("      # built here, so this file passes too
            self.assertNotIn(needle, text,
                             "%s carries a second cut-list" % name)

    def test_one_cut_list(self):
        """the style and the voicer brief may quote examples; they may not
        disagree. every phrase they name is a phrase the soul's table names."""
        known = set()
        for p in voicelint.forbidden_phrases():
            known.add(p.phrase.lower())
        for rel in ("vessel/plugin/output-styles/across-the-desk.md",
                    "vessel/plugin/agents/voicer.md"):
            text = _read(rel)
            quoted = []
            for ex in voicelint.exemptions_for(rel, "forbidden"):
                for n in sorted(voicelint.exempt_lines(rel, text, "forbidden")):
                    quoted.append(text.splitlines()[n - 1])
            named = set()
            for line in quoted:
                for word in re.findall(r"[a-z][a-z'-]{4,}", line.lower()):
                    if word in known:
                        named.add(word)
            self.assertTrue(named, "%s names no example at all" % rel)
            self.assertEqual(named - known, set(),
                             "%s names a phrase the soul's table does not: %s"
                             % (rel, sorted(named - known)))
            print("one list: %s quotes %d of the soul's %d phrases"
                  % (os.path.basename(rel), len(named), len(known)))


class TestForbiddenPhrases(unittest.TestCase):
    def test_no_forbidden_phrase_in_any_text(self):
        rep = voicelint.run()
        self.assertEqual(
            [("%s %r" % (w, p)) for w, p, _ in rep.forbidden], [],
            "a forbidden phrase reached a page a person reads")

    def test_the_lint_fires_on_the_fixture(self):
        text = _read("engine/tests/voice_fixtures/forbidden.fail.md")
        self.assertTrue(voicelint.phrase_hits(text))
        clean = _read("engine/tests/voice_fixtures/forbidden.pass.md")
        self.assertEqual(voicelint.phrase_hits(clean), [])


class TestNegation(unittest.TestCase):
    """check B. density prints; stacked and naked gate."""

    # what C7 rewrites: the charter, the style, the six briefs, README, OPEN.
    # the number is the count of sentences, per file, that the gate names today.
    # X4–X6 cleared README.md (1) and docs/OPEN.md (2 stacked, 2 naked) when the
    # four stranger pages were re-derived for 9.0; the tables are empty now, and
    # a new entry is a regression rather than a debt.
    STACKED_DEBT = {}
    NAKED_DEBT = {}

    def setUp(self):
        self.rep = voicelint.run()

    def _counts(self, rows):
        out = {}
        for rel, _ in rows:
            out[rel] = out.get(rel, 0) + 1
        return out

    def test_negation_density_reported(self):
        """prints, never fails: density counts "not a manager" the same as
        "never X", so it is a proxy, and a proxy reports."""
        over = 0
        for rel, d, words in sorted(self.rep.density):
            if d > voicelint.CEILING:
                over += 1
                print("smell: %s %.2f per 100 words (ceiling %.1f)"
                      % (rel, d, voicelint.CEILING))
        total_words = sum(w for _, _, w in self.rep.density)
        neg = sum(d * w / 100.0 for _, d, w in self.rep.density)
        print("negation: %.2f per 100 words over %d words; %d of %d file(s) "
              "over the ceiling" % (100.0 * neg / max(1, total_words),
                                    total_words, over, len(self.rep.density)))

    def test_no_stacked_prohibition(self):
        self.assertEqual(
            self._counts(self.rep.stacked), self.STACKED_DEBT,
            "stacked prohibitions moved. a new one fails here; a fixed one "
            "moves its number in the same commit (C7 clears this table)")

    def test_every_prohibition_carries_its_reason(self):
        self.assertEqual(
            self._counts(self.rep.naked), self.NAKED_DEBT,
            "an unpaired prohibition moved. C7 clears this table")

    def test_the_soul_pages_carry_neither(self):
        """the pages C1 landed are held hard: the debt above is C7's, not theirs."""
        for rel, _ in self.rep.stacked + self.rep.naked:
            self.assertFalse(rel.startswith("soul/"), "%s is a soul page" % rel)

    def test_the_surfaces_table_is_read_by_column(self):
        """row 21's `avoid — and why` cell is a forbidden move written as one;
        counting it measures the table's shape rather than the page's prose."""
        text = _read("soul/surfaces.md")
        with_cols = voicelint.density(text, "soul/surfaces.md", columns=())[0]
        without = voicelint.density(text, "soul/surfaces.md")[0]
        self.assertGreater(with_cols, voicelint.CEILING)
        self.assertLess(without, voicelint.CEILING)
        print("surfaces.md: %.2f per 100 words with every column, %.2f with the "
              "two shape columns skipped" % (with_cols, without))

    def test_the_gates_fire_on_their_fixtures(self):
        for name, fn in (("stacked", voicelint.stacked), ("naked", voicelint.naked)):
            bad = _read("engine/tests/voice_fixtures/%s.fail.md" % name)
            good = _read("engine/tests/voice_fixtures/%s.pass.md" % name)
            self.assertTrue(fn(bad), "%s.fail.md passed" % name)
            self.assertEqual(fn(good), [], "%s.pass.md failed" % name)
        hot = _read("engine/tests/voice_fixtures/density.fail.md")
        cool = _read("engine/tests/voice_fixtures/density.pass.md")
        self.assertGreater(voicelint.density(hot)[0], voicelint.CEILING)
        self.assertLess(voicelint.density(cool)[0], voicelint.CEILING)


class TestLintString(unittest.TestCase):
    """check C: every printed literal held to a row of soul/surfaces.md."""

    # empty since X9. a line that moves moves its pin here in the same change
    # — that is what keeps the set a debt and never a floor. the guard's three
    # left the set at V2: its six refusals were rewritten as "i" and the file
    # moved into the plugin. X2 took the three the release check spoke and X1
    # took succession's. X9 took the last three — the desk's two ("an
    # assertion needs a body", "a claim never marks its own ink") and the
    # registry's one — in the same change as the words that replaced them. a
    # new entry here is a regression, never a debt.
    SPEC_WORD_DEBT = set()
    # every printed line opens the way the rest of them open now: the one
    # capital left was succession's, and X1 re-voiced the line it sat on.
    CASE_DEBT = set()

    def setUp(self):
        self.rep = voicelint.run()

    def test_the_coverage_line_prints(self):
        print(self.rep.line())
        self.assertGreater(len(self.rep.literals), 200)
        for lit in self.rep.unmapped:
            print("unmapped: %s %r" % (lit.where, lit.text[:60]))

    def test_nothing_printed_is_unmapped(self):
        """item X9 took the list to zero: every literal the engine prints answers
        to a row, and the seven the registry keeps as schema say `# surface:
        none` out loud. a new emitter names its row before it ships."""
        self.assertEqual(["%s %r" % (l.where, l.text[:40])
                          for l in self.rep.unmapped], [])
        self.assertTrue(self.rep.not_printed, "the `none` marker went unused")

    def test_the_unmapped_list_is_real(self):
        """empty today; the check stays, so the day one comes back it names a
        literal that exists rather than a stale line number."""
        for lit in self.rep.unmapped:
            source = _read(lit.path).splitlines()[lit.lineno - 1]
            self.assertIn(lit.text.splitlines()[0][:20], source, lit.where)
            self.assertIsNone(voicelint.row_for(
                lit, voicelint.surface_markers(os.path.join(REPO, lit.path))))

    def test_every_mapped_row_is_a_row_of_the_page(self):
        rows = voicelint.surface_rows()
        for key, row_id in voicelint.SURFACE.items():
            self.assertIn(row_id, rows, "%s maps to row %r, which the page "
                          "does not carry" % (key, row_id))

    def test_no_forbidden_phrase_in_a_printed_literal(self):
        hits = [(w, p) for w, p, _ in self.rep.forbidden if ".py:" in w]
        self.assertEqual(hits, [])

    def test_printed_literals_open_lowercase(self):
        self.assertEqual({w for w, _ in self.rep.case}, self.CASE_DEBT,
                         "a printed line changed its opening case (C4)")

    def test_no_word_for_a_part_of_the_machine(self):
        """experience.md principle 7: a stranger meets the thing, not the part."""
        self.assertEqual({(w, word) for w, word, _ in self.rep.spec_words},
                         self.SPEC_WORD_DEBT,
                         "the spec-only words moved (C4 clears this set)")

    # the usage placeholders (`NAME`, `PATH`, `DIR`, `ID`, and R26's `WHO`
    # and `BUILD`) left this list at X9 by exemption, not by lowering — the
    # manual and the README spell them the same way.
    # R23 (owner, 2026-08-23): UNVERIFIED is the fourth signal word.
    CAPS_DEBT = set()

    def test_the_caps_debt_is_empty(self):
        self.assertEqual(set(self.rep.caps), self.CAPS_DEBT,
                         "a caps token moved; the ruling is FAIL, LOOK, "
                         "DRAFTS, UNVERIFIED")

    # empty since 9.0.1: row 29's budget was 10 while its own exemplar — the
    # shipped legend line, pinned word for word by `test_start_here` — ran to
    # 14. the row moved to 14, and no printed literal is over its row now.
    BUDGET_DEBT = set()

    def test_the_budget_debt_is_the_one_row_that_disagrees_with_itself(self):
        self.assertEqual({(w, r) for w, r, _, _ in self.rep.budget},
                         self.BUDGET_DEBT)

    def test_caps_outside_the_ruled_words_are_reported(self):
        by_token = {}
        for _, t in self.rep.caps:
            by_token[t] = by_token.get(t, 0) + 1
        print("caps: %d token(s) outside %s — %s"
              % (len(self.rep.caps), ", ".join(voicelint.CAPS_ALLOWED),
                 ", ".join("%s×%d" % (t, n) for t, n in sorted(by_token.items()))))

    def test_the_three_ruled_caps_words_are_where_the_ruling_put_them(self):
        """repair B1: FAIL is the one signal word, and its two exemptions are
        doctor's accent and the statusline's die-cut pill."""
        self.assertIn('accent("LOOK")', _read("engine/face.py"))
        rows = voicelint.surface_rows()
        self.assertIn("DRAFTS", rows["21"]["exemplar"])
        self.assertIn("DRAFTS", rows["21"]["case"])
        self.assertIn("LOOK", rows["4"]["case"])
        self.assertIn("FAIL", _read("engine/integrity.py"))

    def test_a_refusal_offers_a_door_instead_of_an_apology(self):
        """gov.uk's rule, the mechanical half: "please" implies a choice,
        "sorry" fixes nothing, "invalid" blames the field."""
        self.assertEqual([(w, m) for w, m, _ in self.rep.moves], [])

    def test_word_budgets_reported(self):
        for where, row, n, ceiling in self.rep.budget:
            print("smell: %s is %d words on a row-%s budget of %d"
                  % (where, n, row, ceiling))
        print("budget: %d of %d literal(s) over their row's count"
              % (len(self.rep.budget), len(self.rep.literals)))

    def test_the_string_checks_fire_on_their_fixtures(self):
        d = os.path.join(REPO, "engine", "tests", "voice_fixtures")
        cases = (("case", lambda l: voicelint.opens_lowercase(l.text)),
                 ("caps", lambda l: not voicelint.caps_tokens(l.text)),
                 ("specword", lambda l: not voicelint.spec_word_hits(l.text)))
        for name, ok in cases:
            for kind, want in (("fail", False), ("pass", True)):
                path = os.path.join(d, "%s.%s.py" % (name, kind))
                lits = voicelint.literals(path)
                self.assertTrue(lits, path)
                self.assertEqual(all(ok(l) for l in lits), want,
                                 "%s.%s.py" % (name, kind))

    def test_the_surface_marker_overrides_the_map(self):
        """repair B5: a `# surface:` comment is how a module-level literal and
        a function that emits several kinds get classified."""
        d = os.path.join(REPO, "engine", "tests", "voice_fixtures")
        bad = os.path.join(d, "surface.fail.py")
        good = os.path.join(d, "surface.pass.py")
        for lit in voicelint.literals(bad):
            self.assertIsNone(voicelint.row_for(lit, voicelint.surface_markers(bad)))
        marked = voicelint.surface_markers(good)
        rows = [voicelint.row_for(l, marked) for l in voicelint.literals(good)]
        self.assertEqual(rows, ["3a"])
        self.assertIn("engine/voicelint.py",
                      [k[0] for k in voicelint.SURFACE])  # the map is real too

    def test_the_marker_is_used_in_the_engine(self):
        """the mechanism is proved on a real file, never only on a fixture."""
        marked = voicelint.surface_markers(
            os.path.join(REPO, "engine", "voicelint.py"))
        self.assertTrue(marked, "no `# surface:` marker in the engine")


class TestDocstrings(unittest.TestCase):
    """check D: a docstring opens the way every other line opens."""

    def setUp(self):
        self.rep = voicelint.run()

    def test_module_docstrings_open_lowercase(self):
        bad = ["%s %s" % (w, first) for kind, w, first in self.rep.doc_case
               if kind == "module"]
        self.assertEqual(bad, [], "a module docstring opens with a capital")

    # X9 took the 151 function and class docstrings that opened with a
    # capital, so the check that printed them is a gate now, at zero. the
    # 23 that opened with a record id (`R17:`, `S1,`, `C10 (`) kept the id
    # and gained a plain word in front of it — an id wears the record's case,
    # and lowering it would name a different item.
    INNER_DEBT = []

    def test_inner_docstrings_open_lowercase(self):
        inner = ["%s %s" % (w, first) for kind, w, first in self.rep.doc_case
                 if kind != "module"]
        self.assertEqual(inner, self.INNER_DEBT,
                         "a function or class docstring opens with a capital")
        print("docstrings: %d read, %d open uppercase"
              % (self.rep.docstrings, len(inner)))

    def test_the_case_check_fires_on_its_fixture(self):
        d = os.path.join(REPO, "engine", "tests", "voice_fixtures")
        for kind, want in (("fail", False), ("pass", True)):
            path = os.path.join(d, "case.%s.py" % kind)
            got = all(voicelint.opens_lowercase(t)
                      for _, _, _, t in voicelint.docstrings(path))
            self.assertEqual(got, want, path)


class TestFlatFixtures(unittest.TestCase):
    """repair S7: every check measures a removal, so nothing here sees flat."""

    def test_flat_fixtures_pass_every_regex(self):
        d = os.path.join(REPO, "engine", "tests", "voice_fixtures", "flat")
        rows = sorted(n for n in os.listdir(d) if n.startswith("row-"))
        self.assertGreaterEqual(len(rows), 16, "eight pairs, one per family")
        for name in rows:
            text = _read("engine/tests/voice_fixtures/flat/" + name)
            self.assertEqual(voicelint.phrase_hits(text), [], name)
            self.assertEqual(voicelint.stacked(text), [], name)
            self.assertEqual(voicelint.naked(text), [], name)
            self.assertEqual(voicelint.caps_tokens(text), [], name)
        print("flat: %d line(s) pass every check; %d of them read as a manual "
              "— the owner's eye is the check" % (len(rows), len(rows) // 2))


class TestPinMap(unittest.TestCase):
    """repair S4: the pin map reads both forms, so no form goes invisible."""

    def test_both_pin_forms_are_found(self):
        rows = pins.pins()
        forms = {}
        for _, _, _, form in rows:
            forms[form] = forms.get(form, 0) + 1
        self.assertGreaterEqual(forms.get("assertIn", 0), 90)
        self.assertGreaterEqual(
            forms.get("assertTrue-any", 0), 10,
            "the assertTrue(any(… in …)) form went invisible again")
        print("pins: %d, by form %s" % (len(rows), sorted(forms.items())))

    def test_every_pin_resolves_or_is_named_test_data(self):
        loose = pins.unresolved()
        # the ceiling counts pins on a line the source builds from a format
        # string — `21 d` out of `%d d`, a repair sentence out of four fields.
        # it moved from 30 to 48 with the doctor and status-line pulls, to 49
        # with the plugin's, and to 56 at V2/V3. X1 and X2 add 34 of their
        # own: the export's rendered lines are assembled field by field, the
        # release check's rows carry a tag and a commit subject, and a dozen
        # are absence pins for words that must never appear. it moves again
        # only beside the tests that add them.
        self.assertLessEqual(
            len(loose), 92,
            "pins carried by no source line: %s" % loose[:5])
        print("pins: %d carried by no source line (a version string, a "
              "workshop path, or a name a test made up)" % len(loose))


if __name__ == "__main__":
    unittest.main()
