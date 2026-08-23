# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the page: one self-contained file that asks the network for nothing.

what the page owns after the ruling is the render — the export owns the lines
and the verb owns the writing, and both are pinned in `test_export.py`. these
hold the file itself: it escapes every field, it reaches for nothing outside
itself, its one design rule is age, and it makes no claim about being live.
"""
import tempfile
import unittest

from engine import export, journal, notes, page, project

from . import pressing


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestPage(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-page-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor", "the store")

    def _html(self):
        rows = export.lines(self.ws)
        return page.render(rows, export.header(self.ws, rows),
                           export.ROUND_TRIP, export.FOOTER)

    def test_the_page_asks_the_network_for_nothing(self):
        text = self._html()
        for shape in ("<script", "http://", "https://", "@import", "fetch(",
                      "<link", "<img"):
            self.assertNotIn(shape, text, shape)

    def test_the_page_escapes_every_field_it_renders(self):
        with pressing("k"):
            notes.note(self.ws, "<script>alert(1)</script>", target_project="geardoor")
            notes.approve(self.ws, out=lambda *a: None)
        text = self._html()
        self.assertNotIn("<script>alert", text)
        self.assertIn("&lt;script&gt;alert", text)

    def test_age_is_the_one_rule_and_it_is_written_once(self):
        text = self._html()
        self.assertEqual(text.count("var(--age)"), 1)
        self.assertIn('style="--age:0.000"', text)   # the oldest, dimmest
        self.assertIn('style="--age:1.000"', text)   # the newest, at full

    def test_the_page_carries_the_footer_and_no_live_claim(self):
        text = self._html()
        self.assertIn("this is a file — opening it leaves nothing on the record", text)
        for claim in ("as of", "live state", "a local render of local state"):
            self.assertNotIn(claim, text, claim)

    def test_the_heading_is_the_record_and_never_the_workshop_state(self):
        text = self._html()
        self.assertIn("record —", text)
        self.assertNotIn("THE WORKSHOP", text)
        self.assertNotIn("nothing needs you", text)   # that is status's line


if __name__ == "__main__":
    unittest.main()
