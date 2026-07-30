# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The record: append-only, addressable, honest about its tears."""
import json
import os
import tempfile
import unittest

from engine import journal


class TestJournal(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")

    def test_genesis_once_never_truncates(self):
        self.assertTrue(journal.ensure_genesis(self.ws))
        journal.append(self.ws, {"op": "assert", "note": "one"})
        self.assertFalse(journal.ensure_genesis(self.ws))
        events, scars = journal.read(self.ws)
        self.assertEqual([e["op"] for e in events], ["genesis", "assert"])
        self.assertEqual(scars, [])

    def test_append_stamps_ts_and_id(self):
        e = journal.append(self.ws, {"op": "place", "path": "x"})
        self.assertTrue(e["id"].startswith("eid-"))
        self.assertIn("ts", e)

    def test_append_refuses_opless(self):
        with self.assertRaises(ValueError):
            journal.append(self.ws, {"note": "no op"})

    def test_torn_ascii_line_scars_and_never_kills(self):
        journal.ensure_genesis(self.ws)
        with open(journal.path(self.ws), "a", encoding="utf-8") as f:
            f.write('{"op": "assert", "note": "torn mid-wr')  # no newline, no close
        events, scars = journal.read(self.ws)
        self.assertEqual(len(events), 1)
        self.assertEqual(len(scars), 1)
        self.assertIn("torn", scars[0])

    def test_torn_multibyte_scars_not_crashes(self):
        journal.ensure_genesis(self.ws)
        full = json.dumps({"op": "assert", "note": "حُرّ"}, ensure_ascii=False).encode("utf-8")
        with open(journal.path(self.ws), "ab") as f:
            f.write(full[:-3])  # tear inside the multibyte tail
        events, scars = journal.read(self.ws)  # must not raise
        self.assertEqual(len(events), 1)
        self.assertEqual(len(scars), 1)

    def test_append_after_tear_starts_fresh_line(self):
        journal.ensure_genesis(self.ws)
        with open(journal.path(self.ws), "a", encoding="utf-8") as f:
            f.write('{"op": "assert", "note": "torn')
        journal.append(self.ws, {"op": "assert", "note": "after the tear"})
        events, scars = journal.read(self.ws)
        self.assertEqual([e.get("note") for e in events if e["op"] == "assert"],
                         ["after the tear"])
        self.assertEqual(len(scars), 1)

    def test_landed_events_never_rewritten(self):
        journal.ensure_genesis(self.ws)
        first = journal.append(self.ws, {"op": "assert", "note": "landed"})
        journal.append(self.ws, {"op": "invalidate", "of": first["id"]})
        events, _ = journal.read(self.ws)
        by_id = [e for e in events if e.get("id") == first["id"]]
        self.assertEqual(len(by_id), 1)
        self.assertEqual(by_id[0]["note"], "landed")  # the second thought is a new event


if __name__ == "__main__":
    unittest.main()
