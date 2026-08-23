# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the shelf as a marketplace source the host already reads.

The catalog reader retired: nothing here re-implements the host's own
pinning. Sandbox writes one file in the shape the host reads, regenerated
from the cards, and `sandbox shelf-dir` prints the directory a friend hands
to `claude plugin marketplace add`. What this file holds is the shape, the
pin, and the two words a stranger meets — `build-<name>` in the host's list
and the same name in the shelf's own page (R18: the browse door is written
before it pulls).
"""
import json
import os
import subprocess
import tempfile
import unittest

from engine import journal, share, shelf

from . import REPO, key


def run_cli(*args, **kw):
    env = dict(os.environ)
    if kw.get("home"):
        env["SANDBOX_HOME"] = kw["home"]
    env.pop("SANDBOX_TEST_KEY", None)
    return subprocess.run([os.path.join(REPO, "sandbox"), *args], input="",
                          capture_output=True, text=True, timeout=60, env=env)


class TestMarketplaceFile(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9mkt-")
        journal.ensure_genesis(self.ws)
        src = os.path.join(tempfile.mkdtemp(prefix="sbx9src-"), "tokens.css")
        with open(src, "w") as f:
            f.write(":root {}\n")
        shelf.save(self.ws, src, note="the design tokens")

    def listed(self):
        with open(shelf.marketplace_path(self.ws), encoding="utf-8") as f:
            return json.load(f)

    def test_save_writes_a_file_the_host_can_parse(self):
        self.assertTrue(os.path.exists(shelf.marketplace_path(self.ws)))
        got = self.listed()
        self.assertIn("name", got)
        self.assertIn("owner", got)
        self.assertEqual(len(got["plugins"]), 1)

    def test_one_entry_per_build_named_for_the_build(self):
        entry = self.listed()["plugins"][0]
        self.assertEqual(entry["name"], "build-tokens.css")
        self.assertEqual(entry["source"], "./tokens.css")
        self.assertEqual(entry["description"], "the design tokens")

    def test_every_entry_is_pinned_by_the_hash_the_card_carries(self):
        """the pin is `shelf.payload_hash`, the one hashing rule — the card's
        `sha256:` and the entry's must be the same number or the two of them
        are guessing about different bytes."""
        for entry in self.listed()["plugins"]:
            name = entry["name"][len("build-"):]
            payload = shelf.payload_in(shelf.dirpath(self.ws, name))
            self.assertEqual(entry["sha256"], shelf.payload_hash(payload))
            self.assertEqual(entry["sha256"], shelf.card(self.ws, name)["sha256"])

    def test_the_owner_is_the_workshop_id_never_the_person(self):
        """law 13: a shelf a stranger adds says which workshop, not whose."""
        who = shelf.workshop_id(self.ws)
        got = self.listed()
        self.assertEqual(got["owner"]["name"], "shelf-%s" % who)
        self.assertNotIn(os.path.expanduser("~"), json.dumps(got))

    def test_the_file_is_regenerated_never_appended(self):
        src = os.path.join(tempfile.mkdtemp(prefix="sbx9src-"), "kit.md")
        with open(src, "w") as f:
            f.write("a kit\n")
        shelf.save(self.ws, src)
        names = sorted(e["name"] for e in self.listed()["plugins"])
        self.assertEqual(names, ["build-kit.md", "build-tokens.css"])
        # a hand-edited file loses to the cards, every time
        with open(shelf.marketplace_path(self.ws), "w", encoding="utf-8") as f:
            f.write('{"plugins": []}\n')
        shelf.write_marketplace(self.ws)
        self.assertEqual(len(self.listed()["plugins"]), 2)

    def test_share_and_fetch_both_regenerate_it(self):
        staging = tempfile.mkdtemp(prefix="sbx9st-")
        os.remove(shelf.marketplace_path(self.ws))
        share.share(self.ws, "tokens.css", staging)
        self.assertTrue(os.path.exists(shelf.marketplace_path(self.ws)))
        mine = tempfile.mkdtemp(prefix="sbx9me-")
        journal.ensure_genesis(mine)
        ok, msg = share.fetch(mine, staging, "tokens.css", key())
        self.assertTrue(ok, msg)
        with open(shelf.marketplace_path(mine), encoding="utf-8") as f:
            self.assertEqual(json.load(f)["plugins"][0]["name"],
                             "build-tokens.css")

    def test_the_shelf_page_names_what_the_host_will_list(self):
        with open(os.path.join(shelf.dirpath(self.ws), "README.md"),
                  encoding="utf-8") as f:
            page = f.read()
        self.assertIn("`build-tokens.css`", page)
        self.assertIn('claude plugin marketplace add "$(sandbox shelf-dir)"', page)
        self.assertIn("sandbox fetch", page)   # the door that records is named

    def test_the_marketplace_file_is_not_mistaken_for_a_build(self):
        """`.claude-plugin` and the page sit beside the cards; neither is one."""
        self.assertEqual([c["name"] for c in shelf.list_all(self.ws)],
                         ["tokens.css"])

    def test_an_entry_verifies_through_the_one_reader(self):
        d, ok, why = shelf.verify_entry(shelf.dirpath(self.ws), "tokens.css")
        self.assertTrue(ok, why)
        payload = shelf.payload_in(shelf.dirpath(self.ws, "tokens.css"))
        with open(payload, "a") as f:
            f.write("/* drift */\n")
        d, ok, why = shelf.verify_entry(shelf.dirpath(self.ws), "tokens.css")
        self.assertFalse(ok)
        self.assertIn("disagree", why)


class TestShelfDirVerb(unittest.TestCase):
    def test_the_verb_prints_the_directory_and_writes_nothing(self):
        ws = tempfile.mkdtemp(prefix="sbx9dir-")
        journal.ensure_genesis(ws)
        before = sorted(os.listdir(ws))
        got = run_cli("shelf-dir", home=ws)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertEqual(got.stdout.strip(), os.path.join(ws, shelf.DIRNAME))
        self.assertEqual(sorted(os.listdir(ws)), before)

    def test_the_directory_it_prints_is_the_one_holding_the_file(self):
        ws = tempfile.mkdtemp(prefix="sbx9dir-")
        journal.ensure_genesis(ws)
        src = os.path.join(tempfile.mkdtemp(prefix="sbx9src-"), "kit.md")
        with open(src, "w") as f:
            f.write("a kit\n")
        shelf.save(ws, src)
        got = run_cli("shelf-dir", home=ws)
        printed = got.stdout.strip()
        self.assertTrue(os.path.exists(os.path.join(
            printed, shelf.MARKET_DIR, shelf.MARKET_FILE)))

    def test_the_verb_takes_no_key_and_declares_no_write(self):
        from engine import verbs
        d = verbs.DECLARATIONS["shelf-dir"]
        self.assertEqual(d["gate"], "none")
        self.assertEqual(d["writes"], ())
        self.assertIsNone(d["emits"])

    def test_builds_tells_a_friend_how_to_add_the_shelf(self):
        ws = tempfile.mkdtemp(prefix="sbx9dir-")
        journal.ensure_genesis(ws)
        src = os.path.join(tempfile.mkdtemp(prefix="sbx9src-"), "kit.md")
        with open(src, "w") as f:
            f.write("a kit\n")
        shelf.save(ws, src)
        got = run_cli("builds", home=ws)
        self.assertEqual(got.returncode, 0, got.stderr)
        self.assertIn('a friend adds this shelf with: claude plugin '
                      'marketplace add "$(sandbox shelf-dir)"', got.stdout)
        self.assertIn("kept here", got.stdout)


if __name__ == "__main__":
    unittest.main()
