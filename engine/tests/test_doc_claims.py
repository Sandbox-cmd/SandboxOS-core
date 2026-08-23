# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the doc lint: generated blocks match the source; no hand-carried facts.

this is the one pin file. other parts name the row they need; the row is
written here, so a claim that goes false fails in one place and names one page
and one string. J25.
"""
import json
import os
import re
import unittest

from engine import selfmap, verbs, voicelint
from engine.tests import REPO, pressing

README = os.path.join(REPO, "README.md")
SITTING = ("<!-- sitting:begin", "<!-- sitting:end -->")
# the number words the pages spell out, and what `ls` has to agree with.
WORDS = {"five": 5, "six": 6, "seven": 7, "fourteen": 14, "fifteen": 15}


def _read(*parts):
    with open(os.path.join(REPO, *parts), encoding="utf-8") as fh:
        return fh.read()


def _without_the_sitting(text):
    """the page minus its transcript block — a paste is not prose."""
    lines, out, inside = text.splitlines(), [], False
    for line in lines:
        if line.startswith(SITTING[0]):
            inside = True
        if not inside:
            out.append(line)
        if line.startswith(SITTING[1]):
            inside = False
    return "\n".join(out)


def _table_rows(text, heading):
    """the body rows of the first table under `heading`."""
    rows, seen = [], False
    for line in text.splitlines():
        if line.startswith("## "):
            if seen:
                break
            seen = line.strip() == heading
            continue
        if seen and line.startswith("|"):
            # a command cell may carry an escaped pipe: `echo k \| sandbox …`
            cells = [c.strip().replace("\\|", "|")
                     for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]
            if set("".join(cells)) <= set("-: ") or cells[0] == "the claim":
                continue
            rows.append(cells)
    return rows


class TestDocClaims(unittest.TestCase):
    def test_manual_verb_block_matches_the_source(self):
        self.assertEqual(selfmap.current_block(), selfmap.render_verbs().strip(),
                         "MANUAL.md's verb table drifted — run: python3 -m engine.selfmap --write")

    def test_the_manual_block_carries_a_blurb_for_every_verb(self):
        """four columns, one row per verb, and no empty middle — the MANUAL
        and `sandbox help` render the same blurb from the same field."""
        rows = [l for l in selfmap.render_verbs().splitlines() if l.startswith("| `")]
        self.assertEqual(len(rows), len(verbs.TABLE))
        self.assertIn("| verb | what it does | gate | writes |",
                      selfmap.render_verbs().splitlines()[0])
        for row in rows:
            cells = [c.strip() for c in row.strip("|").split("|")]
            self.assertEqual(len(cells), 4, row)
            self.assertTrue(cells[1], "a verb reaches the page with no blurb: %s" % row)

    def test_verb_help_is_generated_from_the_same_field(self):
        for name in verbs.TABLE:
            text = selfmap.render_verb_help(name)
            self.assertTrue(text.startswith(verbs.DECLARATIONS[name]["blurb"]), name)
            self.assertIn("the page: docs/MANUAL.md", text)

    def test_every_verb_appears_in_the_manual(self):
        with open(selfmap.manual_path(), encoding="utf-8") as fh:
            text = fh.read()
        for name in verbs.TABLE:
            self.assertIn("`%s`" % name, text, name)

    def test_docs_speak_no_cut_words(self):
        """the list is soul/voice.md's table, parsed — never a tuple here."""
        phrases = voicelint.forbidden_phrases()
        pages = [os.path.join(REPO, "docs", n)
                 for n in os.listdir(os.path.join(REPO, "docs"))]
        pages.append(os.path.join(REPO, "README.md"))  # root-level, same voice
        pages.append(os.path.join(REPO, "CHANGELOG.md"))  # the release notes
        for path in pages:
            rel = os.path.relpath(path, REPO).replace(os.sep, "/")
            with open(path, encoding="utf-8") as fh:
                text = voicelint.blanked(fh.read(), rel, "forbidden")
            for lineno, phrase, _ in voicelint.phrase_hits(text, phrases):
                self.fail("%s:%d says %r" % (rel, lineno, phrase))

    def test_version_is_read_not_written(self):
        """the version appears in VERSION and CHANGELOG (its birthplace) and
        OPEN.md's header — nowhere else in prose.

        The README's sitting block is a transcript, so the version inside it
        was printed rather than typed; `test_readme_sitting` re-runs it and
        fails the day it stops matching this build.
        """
        version = _read("VERSION").strip()
        allowed = {"CHANGELOG.md", "VERSION", "manifest.json"}
        for name in ("README.md",) + tuple(
                os.path.join("docs", n) for n in os.listdir(os.path.join(REPO, "docs"))):
            if os.path.basename(name) in allowed or os.path.basename(name) == "OPEN.md":
                continue
            text = _read(name)
            text = _without_the_sitting(text)
            self.assertNotIn(version, text,
                             "%s hand-carries the version — name the command instead" % name)

    def test_readme_points_at_the_real_repo(self):
        text = _read("README.md")
        self.assertIn("Sandbox-cmd/SandboxOS-core", text)

    def test_readme_line_citations_resolve(self):
        """the page cites source by file and line; the cited line must say it.

        A README that points at `engine/ship.py`, line 45 is making a claim a
        stranger will check. When the source moves, this fails here instead of
        lying there.

        The line must carry the sentence the page quotes, not merely be a
        `return`: the page pointed at `desk.py` line 160 for months while the
        refusal a piped `approve` actually meets is `gate.NOT_A_TTY`, and a
        shape check was green over the wrong file the whole time.
        """
        text = _read("README.md")
        flat = " ".join(text.split())
        cites = re.findall(r"`(engine/[a-z_]+\.py)`, line (\d+)", text)
        self.assertTrue(cites, "no line citations found — did the page stop citing source?")
        for rel, lineno in cites:
            lines = _read(rel).splitlines()
            n = int(lineno)
            self.assertLessEqual(n, len(lines), "%s has no line %d" % (rel, n))
            said = re.findall(r'"([^"]{12,})"', lines[n - 1])
            self.assertTrue(said, "%s:%d carries no sentence to quote" % (rel, n))
            # the literal may take a runtime tail (`— run: sandbox %s`); the
            # head of it is what the page prints and what is held here.
            head = said[0].split("%s")[0].strip()
            self.assertIn(head, flat,
                          "%s:%d is not the refusal the README quotes" % (rel, n))

    def test_readme_loud_line_is_true(self):
        """the page's one loud line: nothing lands that you were not shown.

        Cited behaviour, not cited words — R12 sets the sentence and R17 sets
        its scope, and both halves are checked here: no key, nothing lands;
        a key over a pile that moved lands nothing either.
        """
        import hashlib
        import tempfile

        from engine import desk, gate, journal
        text = _read("README.md")
        self.assertIn("NOTHING LANDS THAT YOU WERE NOT SHOWN.", text,
                      "the loud line changed — re-point this pin at whatever replaced it")
        for consent in (None, {}, {"source": "pipe", "key": "k"}, {"source": "tty", "key": "x"}):
            n, msg = desk.land_all(REPO, consent)
            self.assertEqual(0, n, "land_all landed %d without a real key" % n)
            self.assertIn("real terminal", msg)
        # the shown half: a key is a key over one exact pile, and no other.
        ws = tempfile.mkdtemp(prefix="sbx9-shown-")
        journal.ensure_genesis(ws)
        desk.submit(ws, {"cls": "note", "body": "one thing waiting"})
        with open(desk.staging_path(ws), "rb") as fh:
            raws = fh.read().splitlines()
        moved = [json.loads(r.decode("utf-8")) for r in raws if r.strip()]
        moved[0]["body"] = "something else entirely"
        with pressing("k"):
            consent = gate.mint_consent(shown=hashlib.sha256(b"x").hexdigest())
        n, msg = desk.land_all(ws, consent, shown=moved)
        self.assertFalse(n, "a pile that moved under the key still landed")
        self.assertIn("staging moved under you — nothing landed", msg)

    def test_the_loud_line_is_the_only_shout_on_the_page(self):
        """voice.md position 8: loudness is spent once, or the page is quiet."""
        text = _read("README.md")
        shouts = [l for l in text.splitlines()
                  if re.search(r"[A-Z]{4,}", l) and not l.strip().startswith("export ")]
        self.assertEqual(
            ["> ### NOTHING LANDS THAT YOU WERE NOT SHOWN."],
            [l for l in shouts if l.startswith(">")],
            "a second loud line halves the first")

    def test_the_loud_lines_scope_is_written_beneath_it(self):
        """rule R17: the line is about claims; receipts are events, and ship prints
        its digest on every run. the paragraph under the shout says so."""
        text = _read("README.md")
        below = text.split("NOTHING LANDS THAT YOU WERE NOT SHOWN.", 1)[1]
        head = below.split("## ", 1)[0]
        self.assertIn("digest", head, "the loud line lost its scope paragraph")
        self.assertIn("sandbox ship", head, "R17's ship half went missing")
        self.assertIn("engine/gate.py", head,
                      "the pipe refusal stopped naming where it lives")

    def test_readme_install_block_obeys_its_three_laws(self):
        """the install gate: the bill is named before the clone, and the block
        ends in the health check. The website byte-locks this block, so drift
        here breaks two surfaces."""
        lines = _read("README.md").splitlines()
        clones = [i for i, l in enumerate(lines) if l.startswith("git clone")]
        self.assertEqual(1, len(clones),
                         "one install block, for the owner and the stranger alike")
        clone = clones[0]
        self.assertIn("~/Sandbox/system", lines[clone],
                      "the clone lands anywhere but the one home")
        caveat = next((i for i, l in enumerate(lines) if "claude" in l.lower()), None)
        self.assertIsNotNone(caveat, "the README never names the one paid command")
        self.assertLess(caveat, clone,
                        "the paid-command caveat sits below the clone line — "
                        "a stranger types before they learn the bill")
        block = lines[clone:next(i for i, l in enumerate(lines[clone:], clone)
                                 if l.startswith("```"))]
        self.assertTrue(any("sandbox init" in l for l in block),
                        "the install block never opens a workshop")
        self.assertIn("sandbox doctor", block[-1],
                      "the install block must end in the health check")

    def test_the_export_and_the_page_carry_the_same_foot(self):
        """the R8 claim, as a check rather than a memory: both forms say what the
        file is, in one string, written in one place."""
        import tempfile
        from engine import export, journal, page
        said = "this is a file — opening it leaves nothing on the record"
        self.assertEqual(export.FOOTER, said)
        ws = tempfile.mkdtemp(prefix="sbx9-claims-")
        journal.ensure_genesis(ws)
        for form in ("md", "html"):
            path, _ = export.write(ws, form=form)
            with open(path, encoding="utf-8") as fh:
                self.assertIn(said, fh.read(), form)
        with open(os.path.join(REPO, "engine", "page.py"), encoding="utf-8") as fh:
            source = fh.read()
        for dropped in ("every rendered element backed by a live state",
                        "every element backed by a live state read"):
            self.assertNotIn(dropped, source, dropped)
        self.assertIn("render", dir(page))

    # ------------------------------------------------ the first screen (J11, J12)

    def test_the_first_screen_is_the_frame_then_the_sitting_then_the_bill(self):
        """order, as a fact (owner, 2026-08-23): a stranger meets why this
        exists and what it is, then a real run, then the bill, then the
        claims. the frame is written from the principles, never the tech."""
        text = _read("README.md")
        why = text.index("## why this exists")
        what = text.index("## what it is")
        principles = text.index("## the principles, and what each one refuses")
        sitting = text.index(SITTING[0])
        cost = text.index("only `make`\ncosts money")
        table = text.index("## open any of it")
        self.assertLess(why, what)
        self.assertLess(what, principles)
        self.assertLess(principles, sitting, "the sitting sits above the frame")
        self.assertLess(sitting, cost, "the cost line sits above the sitting")
        self.assertLess(cost, table, "the cost line sits below the claims table")
        head = text[:why]
        self.assertFalse(re.search(r"^## ", head, re.M),
                         "a heading landed above 'why this exists'")
        for word in ("own the tools you think with", "afford to experiment",
                     "grades its own homework", "built by one maker"):
            self.assertIn(word, text[:sitting], "the frame dropped %r" % word)

    def test_the_cost_line_names_its_prerequisites(self):
        text = _read("README.md")
        for part in ("macOS/Linux", "python 3.9+", "a terminal",
                     "Claude Code installed",
                     "it runs on the Claude plan you already pay for"):
            self.assertIn(part, text, "the cost line dropped %r" % part)

    # ------------------------------------------------------ the claims table

    def test_the_claims_table_carries_seven_rows_that_each_open(self):
        rows = _table_rows(_read("README.md"), "## open any of it")
        self.assertEqual(7, len(rows), "the claims table is not seven rows")
        for claim, opens, says in rows:
            self.assertTrue(claim, "a row with no claim")
            self.assertTrue(re.search(r"`[^`]+`", opens),
                            "%r opens with no command" % claim)
            self.assertTrue(says.strip(),
                            "%r names no line a reader should see" % claim)

    def test_the_loud_line_rides_the_table_as_a_row(self):
        """the R12 sentence is a claim in the table before it is a shout."""
        rows = _table_rows(_read("README.md"), "## open any of it")
        claims = [c for c, _, _ in rows]
        self.assertIn("nothing lands that you were not shown", claims)

    def test_the_law_and_soul_counts_on_the_page_are_the_counts_on_disk(self):
        """the docs own this wording, so the docs' own pin holds it."""
        text = _read("README.md")
        for tree, phrase in (("law", "holds fifteen laws"),
                             ("soul", "holds the six pages")):
            self.assertIn(phrase, text, "%s's count left the page" % tree)
            word = re.search(r"holds (?:the )?(\w+)", phrase).group(1)
            self.assertEqual(
                WORDS[word], len(os.listdir(os.path.join(REPO, tree))),
                "the page says %s %s and the tree disagrees" % (word, tree))
            self.assertIn("ls %s | wc -l" % tree, text,
                          "the %s count is a claim with no command" % tree)

    def test_the_import_count_matches_the_grep_the_page_prints(self):
        rows = _table_rows(_read("README.md"), "## open any of it")
        row = next(r for r in rows if "python's own library" in r[0])
        names = set()
        for name in sorted(os.listdir(os.path.join(REPO, "engine"))):
            if not name.endswith(".py"):
                continue
            for line in _read("engine", name).splitlines():
                m = re.match(r"^import ([a-z_]+)$", line)
                if m:
                    names.add(m.group(1))
        word = re.search(r"(\w+) names", row[2]).group(1)
        self.assertEqual(WORDS[word], len(names),
                         "the page counts %r imports, the grep finds %d"
                         % (word, len(names)))

    # ----------------------------------------------------- the word a stranger meets

    def test_amana_is_glossed_where_a_stranger_first_meets_it(self):
        """rule R20: `law/` keeps its own vocabulary; the plain sentence lives on
        the page where the word is first read."""
        text = _read("README.md")
        i = text.lower().find("amana")
        self.assertGreater(i, 0, "the README stopped naming the word law 03 carries")
        around = text[i:i + 400]
        self.assertIn("handed to", around, "amana appears with no gloss")
        for page in ("README.md", os.path.join("docs", "START-HERE.md")):
            body = _read(page)
            if "amana" in body.lower():
                self.assertIn("law 03", body,
                              "%s names the word without naming its law" % page)

    # ------------------------------------------------------------ OPEN.md (behavior 7)

    def test_every_named_debt_names_who_closes_it_and_its_job_row(self):
        """an OPEN.md entry with no owner is a shrug rather than an item."""
        text = _read("docs", "OPEN.md")
        block = text.split("## named debts", 1)[1].split("\n## ", 1)[0]
        bullets = [b for b in re.split(r"\n- ", block)[1:]]
        self.assertGreaterEqual(len(bullets), 3, "the register emptied out")
        self.assertEqual(len(bullets), text.count("closes:"),
                         "a debt with no `closes:` line, or a `closes:` with no debt")
        for b in bullets:
            self.assertTrue(re.search(r"\bJ\d+\b", b),
                            "a debt with no job row: %s" % b.split(".")[0])

    def test_open_says_the_law_tree_was_left_alone(self):
        text = _read("docs", "OPEN.md")
        self.assertIn("`law/` is untouched by this release", text)
        self.assertIn("fifteen laws", text)

    def test_the_four_stranger_pages_pass_the_voice_lint(self):
        """stacked and naked gate; density is the ceiling this run holds to."""
        pages = [README] + [os.path.join(REPO, "docs", n)
                            for n in sorted(os.listdir(os.path.join(REPO, "docs")))
                            if n.endswith(".md")]
        rep = voicelint.run(pages)
        self.assertEqual([], rep.stacked, "a stacked prohibition landed on a doc")
        self.assertEqual([], rep.naked, "a prohibition with no reason landed on a doc")
        for rel, d, _ in rep.density:
            self.assertLessEqual(d, voicelint.CEILING,
                                 "%s is at %.2f negators per 100 words" % (rel, d))

    def test_the_lint_fires(self):
        self.assertNotEqual("stale block", selfmap.render_verbs().strip())


if __name__ == "__main__":
    unittest.main()
