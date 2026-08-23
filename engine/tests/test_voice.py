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


class TestProse(unittest.TestCase):
    """check E: soul/voice.md position 9, over every page a person reads.

    three gates (the em dash, the four contrast constructions, a flat run of
    three sentences) and three counts that print (the rule of three, the pace,
    the fillers). the rule is real from the day it lands, so the pages that
    fail it are frozen below by exact count instead of the check being loosened.
    """

    # page -> the ceiling it owes (em dash, contrast, monotony) on the day
    # check E landed. R27 (owner, 2026-08-23) orders every page a person reads
    # rebuilt to position 9. the row is a ceiling on the page's total, so a
    # rebuild that trades em dashes for a flat run still ratchets the number
    # down; a page over its total is a regression, a page missing from the
    # table is a page the check forgot, and (0, 0, 0) is a page already
    # rebuilt. a rebuild lowers its row in the same commit as the words, and
    # `test_the_cleared_rows_print` names the rows that are ready to drop.
    # the voicer and the challenger quote `return, not perfection`, conviction
    # 4's own name in soul/values.md. both answer for it the way soul/voice.md
    # does, with a `<!-- voice: contrast ok: … -->` marker; crew.json carries
    # the marker at the head of that conviction's text, so it renders on the
    # line the name sits on and the rule is exempted where the name is quoted.
    PROSE_DEBT = {
        'CHANGELOG.md': (0, 0, 0),
        'README.md': (0, 0, 0),
        'docs/MANUAL.md': (0, 0, 0),
        'docs/OPEN.md': (0, 0, 0),
        'docs/START-HERE.md': (0, 0, 0),
        'soul/ground-truth.md': (0, 0, 0),
        'soul/lineage.md': (0, 0, 0),
        'soul/partner.md': (0, 0, 0),
        'soul/surfaces.md': (0, 0, 0),
        'soul/values.md': (0, 0, 0),
        'soul/voice.md': (0, 0, 0),
        'vessel/claude-code/CLAUDE.md': (0, 0, 0),
        'vessel/plugin/agents/challenger.md': (0, 0, 0),
        'vessel/plugin/agents/checker.md': (0, 0, 0),
        'vessel/plugin/agents/keeper.md': (0, 0, 0),
        'vessel/plugin/agents/producer.md': (0, 0, 0),
        'vessel/plugin/agents/surveyor.md': (0, 0, 0),
        'vessel/plugin/agents/voicer.md': (0, 0, 0),
        'vessel/plugin/commands/make.md': (0, 0, 0),
        'vessel/plugin/commands/sandbox.md': (0, 0, 0),
        'vessel/plugin/output-styles/across-the-desk.md': (0, 0, 0),
        'vessel/plugin/skills/backlog-sync/SKILL.md': (0, 0, 0),
        'vessel/plugin/skills/sandbox-workshop/SKILL.md': (0, 0, 0),
        'vessel/plugin/skills/spec-driven-discovery/SKILL.md': (0, 0, 0),
    }

    # the pages rebuilt to position 9. they are held at zero by name, so a
    # later edit cannot quietly spend the headroom a ceiling row would give it.
    CLEAN = ("soul/voice.md",
             "vessel/claude-code/CLAUDE.md",
             "vessel/plugin/agents/challenger.md",
             "vessel/plugin/agents/checker.md",
             "vessel/plugin/agents/keeper.md",
             "vessel/plugin/agents/producer.md",
             "vessel/plugin/agents/surveyor.md",
             "vessel/plugin/agents/voicer.md",
             "vessel/plugin/commands/make.md",
             "vessel/plugin/commands/sandbox.md",
             "vessel/plugin/output-styles/across-the-desk.md")

    def setUp(self):
        self.rep = voicelint.run()

    def _counts(self):
        out = {voicelint._rel(p): [0, 0, 0] for p in voicelint.prose_files()}
        for where, _ in self.rep.em_dash:
            out[where.rsplit(":", 1)[0]][0] += 1
        for where, _, _ in self.rep.contrast:
            out[where.rsplit(":", 1)[0]][1] += 1
        for where, _ in self.rep.monotony:
            out[where.rsplit(":", 1)[0]][2] += 1
        return {k: tuple(v) for k, v in out.items()}

    def test_no_page_is_over_the_ceiling_it_owes(self):
        """the ceiling is the page's total. a rebuild that trades 77 em dashes
        for two flat runs is progress, and a per-column pin would call it a
        regression; the tuple stays because it says what the page owed."""
        counts = self._counts()
        over = ["%s owes %d and reads %d %s"
                % (rel, sum(self.PROSE_DEBT[rel]), sum(got), tuple(got))
                for rel, got in sorted(counts.items())
                if rel in self.PROSE_DEBT
                and sum(got) > sum(self.PROSE_DEBT[rel])]
        self.assertEqual(over, [], "a prose page got worse under position 9")

    def test_every_prose_page_has_a_row(self):
        """a page the table forgot is a page the ceiling never held."""
        rels = sorted(voicelint._rel(p) for p in voicelint.prose_files())
        self.assertEqual(rels, sorted(self.PROSE_DEBT),
                         "the prose set and the debt table disagree")

    def test_the_pages_written_to_position_9_stay_at_zero(self):
        counts = self._counts()
        for rel in self.CLEAN:
            self.assertEqual(counts.get(rel, (0, 0, 0)), (0, 0, 0),
                             "%s picked up a prose gate" % rel)

    def test_the_cleared_rows_print(self):
        """what the next rebuild commit can lower, said out loud."""
        counts = self._counts()
        drop = [rel for rel, owed in sorted(self.PROSE_DEBT.items())
                if sum(owed) and sum(counts.get(rel, (0, 0, 0))) < sum(owed)]
        for rel in drop:
            print("cleared: %s owes %s and reads %s"
                  % (rel, self.PROSE_DEBT[rel], counts.get(rel, (0, 0, 0))))
        print("prose debt: %d of %d page(s) still owe the gate, %d row(s) "
              "ready to drop"
              % (len([r for r, v in counts.items() if any(v)]),
                 len(self.PROSE_DEBT), len(drop)))

    def test_the_soul_page_passes_its_own_position(self):
        """position 9 is written on a page that obeys it: no gate, no smell."""
        text = _read("soul/voice.md")
        rel = "soul/voice.md"
        self.assertEqual(voicelint.em_dash_hits(text, rel), [])
        self.assertEqual(voicelint.contrast_hits(text, rel), [])
        self.assertEqual(voicelint.monotony_hits(text, rel), [])
        self.assertLessEqual(len(voicelint.three_hits(text, rel)),
                             voicelint.THREE_CEILING)
        mean, sd, n = voicelint.pace(text, rel)
        self.assertGreaterEqual(n, 10)
        self.assertTrue(voicelint.PACE_LOW <= mean <= voicelint.PACE_HIGH,
                        "mean sentence %.1f words" % mean)
        self.assertGreaterEqual(sd, voicelint.PACE_SD)
        print("voice.md: mean %.1f words, deviation %.1f over %d sentence(s)"
              % (mean, sd, n))

    def test_the_page_names_where_position_9_stops(self):
        """the engine's own line keeps the em dash, and the page says so."""
        text = _read("soul/voice.md")
        self.assertIn("written like a person, for a person", text)
        for token in ("field separator", "check E", "framework.md"):
            self.assertIn(token, text, token)

    def test_the_projections_carry_the_rules_in_their_own_words(self):
        """read with the line breaks flattened: a page rewrapped by hand still
        carries the same sentences, and the rule is the sentence."""
        flat = lambda rel: re.sub(r"\s+", " ", _read(rel))
        style = flat("vessel/plugin/output-styles/across-the-desk.md")
        for token in ("vary sentence length hard", "so is the em dash",
                      "contrast reflex", "rule of three", "fillers per reply"):
            self.assertIn(token, style, token)
        voicer = flat("vessel/plugin/agents/voicer.md")
        for token in ("the shape", "the six settings", "word stock", "pace:",
                      "assumed context", "relationship"):
            self.assertIn(token, voicer, token)

    def test_the_prose_gates_fire_on_their_fixtures(self):
        d = "engine/tests/voice_fixtures/"
        for name, fn in (("emdash", voicelint.em_dash_hits),
                         ("contrast", voicelint.contrast_hits),
                         ("monotony", voicelint.monotony_hits)):
            self.assertTrue(fn(_read(d + name + ".fail.md")),
                            "%s.fail.md passed" % name)
            self.assertEqual(fn(_read(d + name + ".pass.md")), [],
                             "%s.pass.md failed" % name)

    def test_the_changelog_is_read_down_to_its_history(self):
        """check E holds the section being written and leaves the releases
        under it standing: a shipped section is what that release said."""
        d = "engine/tests/voice_fixtures/"
        rel = "CHANGELOG.md"
        bad, good = _read(d + "changelog.fail.md"), _read(d + "changelog.pass.md")
        self.assertTrue(voicelint.em_dash_hits(bad, rel), "changelog.fail.md passed")
        self.assertTrue(voicelint.contrast_hits(bad, rel), "changelog.fail.md passed")
        self.assertEqual(voicelint.em_dash_hits(good, rel), [])
        self.assertEqual(voicelint.contrast_hits(good, rel), [])
        # the same page with nothing blanked: the marks are down in the history,
        # which is where the rule leaves them.
        self.assertTrue(voicelint.em_dash_hits(good))
        self.assertNotIn(3, voicelint.changelog_history(good), "the open heading")
        # the other half of the rule: with no `in progress` section, the one
        # `VERSION` names is the section being written.
        lines = good.replace("9.9.9 — in progress",
                             "9.9.9 — shipped (2026-01-02)").splitlines()
        history = voicelint.changelog_history("\n".join(lines), "9.9.9")
        self.assertEqual(min(history),
                         1 + next(i for i, l in enumerate(lines)
                                  if l.startswith("## 9.9.8 ")))
        print("changelog: %d of %d line(s) read as history"
              % (len(voicelint.changelog_history(good)),
                 len(good.splitlines())))

    def test_the_prose_smells_fire_on_their_fixtures(self):
        d = "engine/tests/voice_fixtures/"
        self.assertGreater(len(voicelint.three_hits(_read(d + "three.fail.md"))),
                           voicelint.THREE_CEILING)
        self.assertEqual(voicelint.three_hits(_read(d + "three.pass.md")), [])
        hot, cool = voicelint.pace(_read(d + "pace.fail.md")), \
            voicelint.pace(_read(d + "pace.pass.md"))
        self.assertLess(hot[0], voicelint.PACE_LOW)
        self.assertLess(hot[1], voicelint.PACE_SD)
        self.assertTrue(voicelint.PACE_LOW <= cool[0] <= voicelint.PACE_HIGH)
        self.assertGreaterEqual(cool[1], voicelint.PACE_SD)
        for name, over in (("filler.fail.md", True), ("filler.pass.md", False)):
            hits, words = voicelint.filler_count(_read(d + name))
            self.assertEqual(hits > voicelint.filler_ceiling(words), over, name)

    def test_an_exemption_marker_carries_a_reason_or_it_rules_nothing(self):
        """the EXEMPTIONS rule, in a comment: a skip with no reason is a hole."""
        d = "engine/tests/voice_fixtures/"
        bad = _read(d + "mark.fail.md")
        self.assertTrue(voicelint.prose_mark_errors(bad))
        self.assertTrue(voicelint.contrast_hits(bad),
                        "a marker with no reason exempted the line anyway")
        good = _read(d + "mark.pass.md")
        self.assertEqual(voicelint.prose_mark_errors(good), [])
        self.assertEqual(voicelint.contrast_hits(good), [])

    def test_the_marker_is_used_on_a_real_page(self):
        """the mechanism is proved on the tree, never only on a fixture."""
        text = _read("soul/voice.md")
        marks = voicelint.prose_marks(text)
        self.assertTrue(marks, "no voice marker in soul/voice.md")
        self.assertEqual(voicelint.prose_mark_errors(text), [])
        self.assertEqual([w for w, _ in self.rep.bad_marks], [])

    def test_the_prose_set_is_every_page_a_person_reads(self):
        rels = {voicelint._rel(p) for p in voicelint.prose_files()}
        for rel in ("README.md", "CHANGELOG.md", "docs/MANUAL.md",
                    "docs/START-HERE.md", "docs/OPEN.md", "soul/voice.md",
                    "vessel/claude-code/CLAUDE.md",
                    "vessel/plugin/output-styles/across-the-desk.md",
                    "vessel/plugin/agents/voicer.md",
                    "vessel/plugin/commands/sandbox.md",
                    "vessel/plugin/skills/sandbox-workshop/SKILL.md"):
            self.assertIn(rel, rels, rel)
        for rel in rels:
            self.assertTrue(rel.endswith(".md"), rel)
        self.assertEqual(len(rels), len(self.rep.prose))

    def test_the_pace_of_every_page_prints(self):
        for rel, mean, sd, n in sorted(self.rep.pace):
            print("smell: %s mean %.1f words, deviation %.1f over %d sentence(s)"
                  % (rel, mean, sd, n))
        owed = sum(sum(v) for v in self.PROSE_DEBT.values())
        print("prose: %d page(s) read, %d gate(s) owed at the ceiling, "
              "%d off the pace" % (len(self.rep.prose), owed,
                                   len(self.rep.pace)))


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
