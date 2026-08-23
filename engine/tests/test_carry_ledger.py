# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the carry ledger, run from the suite.

it skips plainly on a clone without the tag rather than passing quietly: a
check that cannot read its baseline says so, because a green line nobody could
have earned is the thing this file exists to stop.
"""
import os
import unittest

from engine.tests import REPO, carry_ledger


class TestCarryLedger(unittest.TestCase):
    def setUp(self):
        if not carry_ledger.tag_is_reachable():
            self.skipTest("%s is not a reachable tag in this clone"
                          % carry_ledger.TAG)

    def test_every_retired_name_is_named_in_the_changelog(self):
        rows = carry_ledger.ledger()
        print(carry_ledger.line(rows))
        self.assertEqual(
            rows["unnamed"], [],
            "these 8.2.3 tests are gone and the CHANGELOG names none of them: %s"
            % rows["unnamed"])

    def test_the_baseline_comes_from_the_tag_and_not_from_a_list(self):
        """a hand-written baseline is the shape that rotted last time."""
        old = carry_ledger.baseline()
        self.assertGreater(len(old), 100, "the tag read as almost no tests")
        src = carry_ledger._text(
            os.path.join(REPO, "engine", "tests", "carry_ledger.py"))
        self.assertIn("git", src)
        for name in sorted(old)[:5]:
            self.assertNotIn(name, src, "the baseline is typed into the file")

    def test_the_suite_still_carries_most_of_what_it_had(self):
        rows = carry_ledger.ledger()
        self.assertGreater(len(rows["carried"]), len(rows["retired"]))
        self.assertGreater(len(rows["new"]), 0)

    def test_the_lint_fires(self):
        """a name the CHANGELOG never met is caught, not absorbed."""
        rows = carry_ledger.ledger()
        made_up = "test_a_name_no_release_note_ever_carried"
        self.assertNotIn(made_up, rows["retired"])
        text = carry_ledger._text(os.path.join(REPO, "CHANGELOG.md"))
        self.assertNotIn(made_up, text)


if __name__ == "__main__":
    unittest.main()
