# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the status line's contract: one row, four fields, nothing written.

`sandbox status --line` is the one producer the host's status line calls.
This file writes the contract down and holds the engine to it; the script
that will call it is the owner's file and is read here, never edited (X8) —
the test hashes it before and after to say so.

The finding this contract exists to close: the live script reads
`.sandbox/focus` and `.sandbox/staging/proposals.jsonl`, and the engine
writes neither, so its draft count has always been 0 and its project field
always empty. Both paths are named below as paths nothing here writes.
"""
import hashlib
import os
import subprocess
import tempfile
import unittest

from engine import desk, journal, make, notes, onboard, project, status

from . import REPO

SCRIPT = os.path.expanduser("~/.claude/statusline-phosphor.sh")

# what the live script reads today. the engine writes neither, and this test
# is where that stays true until the script is repointed at the verb.
DEAD_READS = (os.path.join(".sandbox", "focus"),
              os.path.join(".sandbox", "staging", "proposals.jsonl"))


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class TestTheLine(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9line-")
        onboard.run(self.ws)

    def test_a_quiet_workshop_reads_as_four_plain_fields(self):
        row = status.line(self.ws)
        self.assertEqual(row, "no project · no drafts · no make · shipped")

    def test_the_four_fields_say_what_waits(self):
        project.new(self.ws, "geardoor", "the store's data")
        project.switch(self.ws, "geardoor", True)
        notes.note(self.ws, "a finding", target_project="geardoor")
        make.open_session(self.ws, "geardoor", "the tax table")
        row = status.line(self.ws)
        fields = row.split(" · ")
        self.assertEqual(len(fields), 4)
        self.assertEqual(fields[0], "geardoor")
        self.assertEqual(fields[1], "1 draft")
        self.assertTrue(fields[2].startswith("make "), fields[2])
        self.assertEqual(fields[3], "shipped")

    def test_the_closes_field_counts_the_ship_debt(self):
        project.new(self.ws, "geardoor", "the store's data")
        make.open_session(self.ws, "geardoor", "one pass")
        make.close_session(self.ws, "geardoor")
        self.assertIn("1 closes since ship", status.line(self.ws))

    def test_the_age_is_the_one_formatter(self):
        """`21 d` on the line is the same string status and doctor print."""
        project.new(self.ws, "geardoor", "the store's data")
        from engine.tests.test_doctor import days_ago, plant_open_make
        plant_open_make(self.ws, "geardoor", "a long pass", days_ago(21))
        self.assertIn("make %s" % status.age(days_ago(21)), status.line(self.ws))
        self.assertIn("21 d", status.line(self.ws))

    def test_the_door_prints_one_line_and_exits_zero(self):
        env = dict(os.environ)
        env["SANDBOX_HOME"] = self.ws
        env.pop("SANDBOX_TEST_KEY", None)
        got = subprocess.run([os.path.join(REPO, "sandbox"), "status", "--line"],
                             capture_output=True, text=True, timeout=60, env=env)
        self.assertEqual(got.returncode, 0)
        self.assertEqual(len(got.stdout.strip().splitlines()), 1)
        self.assertEqual(got.stdout.strip().count(" · "), 3)

    def test_the_line_writes_nothing(self):
        from engine.tests.test_doctor import hash_tree
        before = hash_tree(self.ws)
        status.line(self.ws)
        self.assertEqual(before, hash_tree(self.ws))

    def test_the_paths_the_live_script_reads_are_paths_nothing_writes(self):
        """the draft count has always been 0; here is why, in one assert."""
        notes.note(self.ws, "a finding")
        self.assertTrue(desk.drafts(self.ws)[0])
        self.assertEqual(desk.staging_path(self.ws),
                         os.path.join(self.ws, journal.STATE_DIR, "staging.jsonl"))
        for rel in DEAD_READS:
            self.assertFalse(os.path.exists(os.path.join(self.ws, rel)), rel)
        self.assertIn("1 draft", status.line(self.ws))

    def test_the_owner_s_script_is_read_and_never_edited(self):
        """item X8: the phosphor script is the owner's file. this test only reads it."""
        if not os.path.exists(SCRIPT):
            self.skipTest("no status line script on this machine")
        before = sha(SCRIPT)
        status.line(self.ws)
        self.assertEqual(before, sha(SCRIPT))


if __name__ == "__main__":
    unittest.main()
