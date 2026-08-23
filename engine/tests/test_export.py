# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""export: the record leaves as one file, and the file says what it is.

the pins here are the ones a person could check by hand — the line grammar,
the receipt on every line, the numbering that keeps an export from replacing
the one before it, the counts matching the scrub, and the two facts the file
states about itself: running it lands one line on the record, and opening it
lands none.
"""
import contextlib
import hashlib
import io
import json
import os
import tempfile
import unittest

from engine import clean, export, journal, notes, project, verbs

from . import pressing


def _run(ws, verb, argv):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = verbs.dispatch(ws, verb, argv)
    return rc, buf.getvalue()


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class Workshop(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-export-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor", "the store")

    def land(self, body, **kw):
        with pressing("k"):
            notes.note(self.ws, body, **kw)
            notes.approve(self.ws, out=lambda *a: None)


class TestTheFileShape(Workshop):
    def test_every_line_carries_a_receipt_and_the_lines_run_in_time_order(self):
        self.land("the tax rule is 5 percent", target_project="geardoor")
        rows = export.lines(self.ws)
        self.assertGreaterEqual(len(rows), 3)
        stamps = [r["ts"] for r in rows if r["ts"]]
        self.assertEqual(stamps, sorted(stamps))
        for r in rows:
            if not r["scar"]:
                self.assertTrue(r["receipt"], r)

    def test_the_header_names_the_workshop_the_span_and_the_counts(self):
        self.land("a landed fact", target_project="geardoor")
        path, report = export.write(self.ws)
        text = _read(path)
        self.assertIn("# record — this workshop, ", text)
        self.assertIn("line(s) · ", text)
        self.assertIn(" → ", text)

    def test_the_header_names_a_workshop_that_named_itself(self):
        with open(os.path.join(self.ws, journal.STATE_DIR, "workshop-id"),
                  "w", encoding="utf-8") as f:
            f.write("the eighth workshop\n")
        path, _ = export.write(self.ws)
        self.assertIn("# record — the eighth workshop, ",
                      _read(path))

    def test_the_footer_is_on_the_file_verbatim(self):
        path, _ = export.write(self.ws)
        text = _read(path)
        self.assertIn("this is a file — opening it leaves nothing on the record", text)
        self.assertIn("what comes back through import", text)
        self.assertIn("what stays behind", text)

    def test_a_synthetic_hand_is_worn_exactly_where_it_was_stamped(self):
        self.land("pressed by the rig", target_project="geardoor")
        rows = [r for r in export.lines(self.ws) if r["body"] == "pressed by the rig"]
        self.assertEqual([r["hand"] for r in rows], ["synthetic"])
        line = export.render_line(rows[0])
        self.assertIn("[synthetic]", line)
        genesis = [r for r in export.lines(self.ws) if r["kind"] == "genesis"][0]
        self.assertNotIn("[synthetic]", export.render_line(genesis))

    def test_a_ruling_wears_its_stratum_and_names_what_it_replaced(self):
        self.land("the count is 11", target_project="geardoor", stratum="taste")
        events, _ = journal.read(self.ws)
        first = [e for e in events if e.get("cls") == "ruling"][0]
        self.land("the count is 12", target_project="geardoor", stratum="taste",
                  supersedes=first["id"])
        text = export.render_md(self.ws, export.lines(self.ws))
        self.assertIn("[taste] [machine] [synthetic] assert/ruling  the count is 12", text)
        self.assertIn("supersedes: journal:%s" % first["id"], text)
        self.assertIn("the count is 11", text)  # the superseded line stays in place

    def test_a_struck_line_reads_struck_and_stays(self):
        self.land("a fact i took back", target_project="geardoor")
        events, _ = journal.read(self.ws)
        target = [e for e in events if e.get("body") == "a fact i took back"][0]
        with pressing("k"):
            notes.strike(self.ws, target["id"], "it was wrong")
            notes.approve(self.ws, out=lambda *a: None)
        text = export.render_md(self.ws, export.lines(self.ws))
        self.assertIn("[struck] [machine] [synthetic] assert/note  a fact i took back", text)

    def test_a_make_close_summarises_its_diff(self):
        from engine import make
        make.open_session(self.ws, "geardoor", "change one file")
        root = project.root_of(self.ws, "geardoor")
        with open(os.path.join(root, "new.txt"), "w", encoding="utf-8") as f:
            f.write("born\n")
        make.close_session(self.ws, "geardoor")
        text = export.render_md(self.ws, export.lines(self.ws))
        self.assertIn("make/close", text)
        self.assertIn("(+1 −0 ~0)", text)

    def test_a_torn_line_rides_in_as_a_scar(self):
        with open(journal.path(self.ws), "a", encoding="utf-8") as f:
            f.write("{torn json\n")
        self.land("after the tear", target_project="geardoor")
        rows = export.lines(self.ws)
        scars = [r for r in rows if r["scar"]]
        self.assertEqual(len(scars), 1)
        self.assertIn("unreadable", scars[0]["body"])
        text = export.render_md(self.ws, rows)
        self.assertIn("after the tear", text)

    def test_a_slice_says_it_is_a_slice(self):
        self.land("a landed fact", target_project="geardoor")
        path, _ = export.write(self.ws, project="geardoor", since="2020-01-01")
        head = _read(path).splitlines()[0]
        self.assertIn("geardoor", head)
        self.assertIn("since 2020-01-01", head)
        self.assertIn("(a slice, not the record)", head)


class TestNumbering(Workshop):
    def test_a_second_export_the_same_day_never_replaces_the_first(self):
        first, _ = export.write(self.ws)
        second, _ = export.write(self.ws)
        self.assertNotEqual(first, second)
        self.assertTrue(os.path.basename(second).endswith("-2.md"),
                        os.path.basename(second))
        self.assertTrue(os.path.exists(first))

    def test_to_puts_the_file_where_it_was_asked_for(self):
        elsewhere = tempfile.mkdtemp(prefix="sbx9-elsewhere-")
        path, _ = export.write(self.ws, to=elsewhere)
        self.assertEqual(os.path.dirname(path), elsewhere)


class TestRedaction(Workshop):
    def setUp(self):
        super(TestRedaction, self).setUp()
        d = tempfile.mkdtemp(prefix="sbx9-terms-")
        self.terms_file = os.path.join(d, "terms.txt")
        with open(self.terms_file, "w", encoding="utf-8") as f:
            f.write("acme\nghost\n")
        self.old = os.environ.get(clean.TERMS_ENV)
        os.environ[clean.TERMS_ENV] = self.terms_file

    def tearDown(self):
        if self.old is None:
            os.environ.pop(clean.TERMS_ENV, None)
        else:
            os.environ[clean.TERMS_ENV] = self.old

    def test_the_counts_equal_the_scrub_that_actually_happened(self):
        home = clean.FLOOR[0]
        self.land("acme lives at %sada/one.md and %sada/two.md" % (home, home),
                  target_project="geardoor")
        path, report = export.write(self.ws, redact=True)
        text = _read(path)
        self.assertNotIn(home, text)
        self.assertNotIn("acme", text)
        counts = report["counts"]
        self.assertEqual(counts["terms"], {"t1": 1})
        self.assertGreaterEqual(counts["home_path"], 2)
        removed = counts["home_path"] + sum(counts["terms"].values())
        self.assertIn("— redacted, %d span(s) removed" % removed, text)

    def test_the_record_keeps_the_index_and_never_the_term(self):
        self.land("acme and acme again", target_project="geardoor")
        export.write(self.ws, redact=True)
        raw = _read(journal.path(self.ws))
        marked = [json.loads(l) for l in raw.splitlines()
                  if l.strip() and json.loads(l).get("op") == "export"]
        self.assertEqual(len(marked), 1)
        self.assertEqual(marked[0]["scrubbed"]["terms"], {"t1": 2})
        after = raw.split('"op": "export"', 1)[1]
        self.assertNotIn("ghost", after)

    def test_the_terminal_names_the_terms_the_file_never_does(self):
        self.land("acme and acme again", target_project="geardoor")
        rc, out = _run(self.ws, "export", ["--redact"])
        self.assertEqual(rc, 0)
        self.assertIn("redacted 2 span(s)", out)
        self.assertIn("acme 2", out)          # named at the terminal
        self.assertIn("2 term(s), 1 never matched", out)
        path = out.strip().splitlines()[-1]
        self.assertNotIn("acme", _read(path))

    def test_an_unredacted_run_still_says_what_would_go(self):
        self.land("acme lives here", target_project="geardoor")
        rc, out = _run(self.ws, "export", [])
        self.assertEqual(rc, 0)
        self.assertIn("not redacted — ", out)
        self.assertIn("span(s) would go under --redact", out)

    def test_the_path_is_the_last_line_the_verb_prints(self):
        rc, out = _run(self.ws, "export", [])
        last = out.strip().splitlines()[-1]
        self.assertTrue(os.path.exists(last), last)
        self.assertTrue(last.endswith(".md"), last)


class TestTheEvent(Workshop):
    def test_one_export_mints_exactly_one_line(self):
        before, _ = journal.read(self.ws)
        path, report = export.write(self.ws)
        after, _ = journal.read(self.ws)
        minted = [e for e in after if e.get("op") == "export"]
        self.assertEqual(len(minted), 1)
        self.assertEqual(len(after), len(before) + 1)
        self.assertEqual(minted[0]["sha256"], _sha(path))
        self.assertEqual(minted[0]["receipt"], path)
        self.assertEqual(minted[0]["form"], "md")

    def test_opening_the_file_lands_nothing(self):
        path, _ = export.write(self.ws)
        before = _sha(journal.path(self.ws))
        for _ in range(3):
            _read(path)
        self.assertEqual(_sha(journal.path(self.ws)), before)

    def test_the_op_is_one_the_table_declares(self):
        export.write(self.ws)
        events, _ = journal.read(self.ws)
        for e in events:
            self.assertIn(e["op"], verbs.OPS, e)


class TestTheHtmlForm(Workshop):
    def test_the_page_is_inert_and_carries_the_same_foot(self):
        self.land("a landed fact", target_project="geardoor")
        path, _ = export.write(self.ws, form="html")
        text = _read(path)
        self.assertTrue(path.endswith(".html"), path)
        for shape in ("<script", "http://", "https://", "@import", "fetch("):
            self.assertNotIn(shape, text, shape)
        self.assertIn("this is a file — opening it leaves nothing on the record", text)
        self.assertIn("a landed fact", text)

    def test_age_is_one_rule_and_every_line_carries_its_place(self):
        self.land("a landed fact", target_project="geardoor")
        path, _ = export.write(self.ws, form="html")
        text = _read(path)
        self.assertEqual(text.count("var(--age)"), 1)
        self.assertIn('style="--age:0.000"', text)
        self.assertIn('style="--age:1.000"', text)

    def test_the_page_escapes_what_it_renders(self):
        self.land("<script>alert(1)</script>", target_project="geardoor")
        path, _ = export.write(self.ws, form="html")
        self.assertNotIn("<script>alert", _read(path))

    def test_page_is_the_alias_and_says_so(self):
        rc, out = _run(self.ws, "page", [])
        self.assertEqual(rc, 0)
        self.assertIn("page is export --html now — writing record-", out)
        last = out.strip().splitlines()[-1]
        self.assertTrue(last.endswith(".html"), last)
        self.assertTrue(os.path.exists(last))
        events, _ = journal.read(self.ws)
        self.assertEqual([e["form"] for e in events if e.get("op") == "export"],
                         ["html"])


class TestTheTornLineCount(Workshop):
    """item X10 — the count line says what a torn line is and where to look."""

    def test_the_header_says_what_a_torn_line_is(self):
        rows = [{"ts": "2026-08-22T00:00:00Z", "scar": False},
                {"ts": "2026-08-22T00:00:01Z", "scar": True}]
        head = export.header(self.ws, rows)
        self.assertIn("torn line(s) on the record", head[2])
        self.assertIn("a line it could not read", head[2])
        self.assertIn("doctor has details", head[2])
        self.assertTrue(head[2].split("·")[-1].strip().startswith("1 torn"),
                        head[2])

    def test_a_real_scar_reaches_the_page(self):
        self.land("a landed fact", target_project="geardoor")
        with open(journal.path(self.ws), "a", encoding="utf-8") as f:
            f.write("this line is not json\n")
        path, _ = export.write(self.ws, form="html")
        text = _read(path)
        self.assertIn("torn line(s) on the record", text)
        self.assertIn("doctor has details", text)
        self.assertIn("this is a file — opening it leaves nothing on the record",
                      text)


class TestPortable(Workshop):
    def test_the_leaving_directory_carries_the_record_byte_for_byte(self):
        self.land("the tax rule is 5 percent", target_project="geardoor")
        before = _sha(journal.path(self.ws))
        path, report = export.write(self.ws, form="portable")
        self.assertTrue(os.path.isdir(path))
        names = sorted(os.listdir(path))
        self.assertIn("journal.jsonl", names)
        self.assertIn("path-map.json", names)
        self.assertEqual(_sha(os.path.join(path, "journal.jsonl")), before)

    def test_a_redacted_portable_refuses_and_says_what_would_work(self):
        path, report = export.write(self.ws, form="portable", redact=True)
        self.assertIsNone(path)
        self.assertIn("a redacted export is a reading copy", report["refused"])
        rc, out = _run(self.ws, "export", ["--portable", "--redact"])
        self.assertEqual(rc, 1)
        self.assertIn("export --portable by itself", out)

    def test_two_forms_at_once_refuses(self):
        rc, out = _run(self.ws, "export", ["--html", "--portable"])
        self.assertEqual(rc, 2)
        self.assertIn("one form at a time", out)


class TestTheDoor(Workshop):
    def test_export_refuses_a_flag_it_does_not_know(self):
        rc, out = _run(self.ws, "export", ["--no-such-flag"])
        self.assertEqual(rc, 2)
        self.assertIn("doesn't know --no-such-flag", out)

    def test_the_verb_declares_what_it_writes(self):
        d = verbs.DECLARATIONS["export"]
        self.assertEqual(d["emits"], "export")
        self.assertEqual(d["gate"], "none")   # a file lands no claim
        self.assertEqual(d["writes"], ("workshop",))


if __name__ == "__main__":
    unittest.main()
