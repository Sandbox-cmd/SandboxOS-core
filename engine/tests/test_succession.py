# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""succession: the record comes whole, the past opens at new addresses."""
import json
import os
import tempfile
import unittest

from engine import journal, notes, onboard, project, succession, update

from . import no_terminal, pressing, quiet


def make_seventh_body():
    """a little old workshop in the seventh body's shapes."""
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
        with no_terminal():                       # headless — must re-ask
            ok, msg = ship.ship(self.ws, "geardoor", quiet)
        self.assertFalse(ok)
        self.assertIn("ratifying checks needs your 'k' at a real terminal", msg)

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

    def test_moved_roots_relocate_by_suffix(self):
        """a root recorded before the workshop moved still comes in."""
        cart = os.path.join(self.old, "cartridges", "shop")
        os.makedirs(cart)
        open(os.path.join(cart, "data.json"), "w").write("{}")
        ch = os.path.join(self.old, "channels", "shop")
        os.makedirs(ch)
        with open(os.path.join(ch, "CHANNEL.md"), "w") as f:
            # The root as it was recorded BEFORE the move — a path that no
            # longer exists anywhere.
            f.write("# shop\ngoal: g\nstate: active\nroot: /gone/den/Old/cartridges/shop\n\n## checks\n")
        ok, text = succession.run(self.ws, self.old, ["shop"])
        self.assertTrue(ok, text)
        self.assertTrue(os.path.exists(
            os.path.join(project.dirpath(self.ws, "shop"), "data.json")))

    def test_import_refuses_a_lived_in_workshop(self):
        onboard.run(self.ws)
        notes.note(self.ws, "already mine", target_project=None)
        with pressing("k"):
            notes.approve(self.ws, out=lambda _line: None)
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


class TestExternalRoots(unittest.TestCase):
    def test_external_root_stays_a_root_never_moves_in(self):
        old = make_seventh_body()
        external = tempfile.mkdtemp(prefix="sbx8ext-")
        open(os.path.join(external, "engine.py"), "w").write("# the tool\n")
        ch = os.path.join(old, "channels", "toolwork")
        os.makedirs(ch)
        with open(os.path.join(ch, "CHANNEL.md"), "w") as f:
            f.write("# toolwork\ngoal: g\nstate: active\nroot: %s\n\n## checks\n" % external)
        open(os.path.join(ch, "NOTES.md"), "w").write("the project docs\n")
        ws = tempfile.mkdtemp(prefix="sbx8-")
        ok, text = succession.run(ws, old, ["toolwork"])
        self.assertTrue(ok, text)
        c = project.parse_contract(project.contract_path(ws, "toolwork"))
        self.assertEqual(c["root"], external)  # the root stays a root
        self.assertTrue(os.path.exists(
            os.path.join(project.dirpath(ws, "toolwork"), "NOTES.md")))  # docs came
        self.assertFalse(os.path.exists(
            os.path.join(project.dirpath(ws, "toolwork"), "engine.py")))  # tree did not


class TestPortableRoundTrip(unittest.TestCase):
    """the outward half of law 2: what `export --portable` writes, `import`
    reads, and what stays behind is said in the file it wrote."""

    def setUp(self):
        from engine import export, project as prj
        self.old = tempfile.mkdtemp(prefix="sbx9-leaving-")
        journal.ensure_genesis(self.old)
        prj.new(self.old, "geardoor", "the store")
        with pressing("k"):
            notes.note(self.old, "the tax rule is 5 percent", target_project="geardoor")
            notes.approve(self.old, out=quiet)
        self.leaving, _ = export.write(self.old, form="portable")
        self.ws = tempfile.mkdtemp(prefix="sbx9-arriving-")

    def _sha(self, path):
        import hashlib
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()

    def test_the_record_comes_back_verbatim(self):
        ok, text = succession.run(self.ws, self.leaving, [])
        self.assertTrue(ok, text)
        self.assertEqual(self._sha(os.path.join(self.leaving, "journal.jsonl")),
                         self._sha(journal.path(self.ws)))
        with open(os.path.join(self.leaving, "journal.jsonl"), encoding="utf-8") as f:
            left = [json.loads(l) for l in f if l.strip()]
        after, _ = journal.read(self.ws)
        self.assertEqual([e.get("id") for e in left],
                         [e.get("id") for e in after])
        self.assertEqual(len(notes.recall(self.ws, "tax rule")), 1)
        # the line the export itself minted lands after the copy is taken, so
        # it stays with the workshop that wrote it rather than riding along.
        self.assertEqual([e for e in after if e.get("op") == "export"], [])

    def test_an_old_receipt_opens_at_its_new_address(self):
        succession.run(self.ws, self.leaving, [])
        from engine import project as prj
        old_receipt = prj.contract_path(self.old, "geardoor")
        self.assertTrue(update.resolve(self.ws, old_receipt).startswith(self.ws))

    def test_what_stays_behind_is_named_on_the_file_itself(self):
        name = [n for n in os.listdir(self.leaving) if n.endswith(".md")][0]
        with open(os.path.join(self.leaving, name), encoding="utf-8") as f:
            text = f.read()
        self.assertIn("what comes back through import", text)
        self.assertIn("what stays behind", text)
        self.assertIn("the shelf's cards", text)
        self.assertIn("the project trees", text)

    def test_the_projects_and_the_cards_stay_where_they_were(self):
        """the leaving directory is the record, and it says so rather than
        arriving with a project tree that never travelled."""
        succession.run(self.ws, self.leaving, [])
        from engine import project as prj
        self.assertFalse(os.path.isdir(prj.dirpath(self.ws, "geardoor")))
        self.assertFalse(os.path.isdir(os.path.join(self.ws, "shelf")))

    def test_a_leaving_directory_is_refused_by_a_workshop_that_lived(self):
        onboard.run(self.ws)
        with pressing("k"):
            notes.note(self.ws, "already mine", target_project=None)
            notes.approve(self.ws, out=quiet)
        ok, text = succession.run(self.ws, self.leaving, [])
        self.assertFalse(ok)
        self.assertIn("never merges selves", text)
