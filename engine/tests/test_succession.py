# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Succession: the record comes whole, the past opens at new addresses."""
import json
import os
import tempfile
import unittest

from engine import journal, notes, onboard, project, succession, update


def make_seventh_body():
    """A little old workshop in the seventh body's shapes."""
    old = tempfile.mkdtemp(prefix="sbx7-")
    state = os.path.join(old, ".sandbox")
    os.makedirs(state)
    with open(os.path.join(state, "journal.jsonl"), "w", encoding="utf-8") as f:
        f.write(json.dumps({"op": "genesis", "who": "desk",
                            "ts": "2025-11-01T00:00:00Z", "id": "eid-genesis7"}) + "\n")
        f.write(json.dumps({"op": "assert", "cls": "note", "origin": "human",
                            "body": "the tax rule is 5 percent", "ink": "checked",
                            "project": "geardoor",
                            "receipt": old + "/channels/geardoor/CANON.md",
                            "ts": "2026-06-01T00:00:00Z", "id": "eid-old1"},
                           ensure_ascii=False) + "\n")
    ch = os.path.join(old, "channels", "geardoor")
    os.makedirs(ch)
    with open(os.path.join(ch, "CHANNEL.md"), "w") as f:
        f.write("# geardoor\ngoal: the store's data\nstate: active\n\n## checks\ntrue\n")
    with open(os.path.join(ch, "CANON.md"), "w") as f:
        f.write("# canon\n")
    rk = os.path.join(old, "rack", "kit")
    os.makedirs(rk)
    with open(os.path.join(rk, "CART.md"), "w") as f:
        f.write("# kit\nkept: 2026-07-01T00:00:00Z\nsha256: abc\norigin: owner-kept\n\n## used\n")
    with open(os.path.join(rk, "payload.md"), "w") as f:
        f.write("the payload\n")
    ag = os.path.join(old, ".claude", "agents")
    os.makedirs(ag)
    with open(os.path.join(ag, "keeper.md"), "w") as f:
        f.write("---\nname: keeper\n---\nmine\n")
    return old


class TestImport(unittest.TestCase):
    def setUp(self):
        self.old = make_seventh_body()
        self.ws = tempfile.mkdtemp(prefix="sbx8-")

    def test_list_offers_the_old_projects(self):
        offers = succession.list_old(self.old)
        self.assertEqual(offers[0]["name"], "geardoor")

    def test_the_record_comes_verbatim_and_continuous(self):
        ok, text = succession.run(self.ws, self.old, ["geardoor"])
        self.assertTrue(ok, text)
        old_bytes = open(os.path.join(self.old, ".sandbox", "journal.jsonl"), "rb").read()
        new_bytes = open(journal.path(self.ws), "rb").read()
        self.assertEqual(old_bytes, new_bytes)  # verbatim — the self survives
        events, _ = journal.read(self.ws)
        self.assertEqual(events[0]["id"], "eid-genesis7")  # the old genesis stays

    def test_projects_arrive_live_with_checks_ratification_void(self):
        succession.run(self.ws, self.old, ["geardoor"])
        c = project.parse_contract(project.contract_path(self.ws, "geardoor"))
        self.assertEqual(c["goal"], "the store's data")
        self.assertEqual(c["checks"], ["true"])
        from engine import ship
        ok, msg = ship.ship(self.ws, "geardoor")  # headless — must re-ask
        self.assertFalse(ok)
        self.assertIn("new or changed", msg)

    def test_old_receipts_open_through_the_path_map(self):
        succession.run(self.ws, self.old, ["geardoor"])
        old_receipt = self.old + "/channels/geardoor/CANON.md"
        resolved = update.resolve(self.ws, old_receipt)
        self.assertTrue(resolved.startswith(self.ws))
        self.assertTrue(os.path.exists(resolved))

    def test_builds_and_agents_come_along(self):
        succession.run(self.ws, self.old, [])
        self.assertTrue(os.path.exists(os.path.join(self.ws, "shelf", "kit", "BUILD.md")))
        self.assertTrue(os.path.exists(os.path.join(self.ws, ".claude", "agents", "keeper.md")))

    def test_import_refuses_a_lived_in_workshop(self):
        onboard.run(self.ws)
        notes.note(self.ws, "already mine", target_project=None)
        notes.approve(self.ws, is_real_tty=True, keychar="k")
        ok, text = succession.run(self.ws, self.old, [])
        self.assertFalse(ok)
        self.assertIn("never merges selves", text)

    def test_init_after_import_touches_nothing_and_recall_reaches_the_past(self):
        succession.run(self.ws, self.old, ["geardoor"])
        ok, text = onboard.run(self.ws)
        self.assertTrue(ok)
        self.assertIn("nothing that lives is touched", text)
        events, _ = journal.read(self.ws)
        self.assertEqual(events[0]["id"], "eid-genesis7")
        hits = notes.recall(self.ws, "tax rule")
        self.assertEqual(len(hits), 1)  # the past answers in the new body


if __name__ == "__main__":
    unittest.main()
