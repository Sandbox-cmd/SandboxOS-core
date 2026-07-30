# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Projects: born with a contract and a history, closed on the owner's confirm."""
import os
import tempfile
import unittest

from engine import journal, project, provisional


class TestProject(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)

    def test_new_writes_contract_canon_git_and_event(self):
        ok, msg = project.new(self.ws, "geardoor", "the store's data")
        self.assertTrue(ok)
        c = project.parse_contract(project.contract_path(self.ws, "geardoor"))
        self.assertEqual(c["goal"], "the store's data")
        self.assertEqual(c["state"], "active")
        self.assertTrue(os.path.exists(os.path.join(project.dirpath(self.ws, "geardoor"), "CANON.md")))
        events, _ = journal.read(self.ws)
        self.assertTrue(any(e.get("cls") == "project-state" and "born" in e.get("body", "")
                            for e in events))

    def test_new_never_overwrites_a_living_project(self):
        project.new(self.ws, "geardoor", "one")
        with open(project.contract_path(self.ws, "geardoor"), "a") as f:
            f.write("precious: yes\n")
        ok, msg = project.new(self.ws, "geardoor", "two")
        self.assertFalse(ok)
        self.assertIn("precious", open(project.contract_path(self.ws, "geardoor")).read())

    def test_switchboard_on_off(self):
        project.new(self.ws, "geardoor")
        ok, _ = project.switch(self.ws, "geardoor", True)
        self.assertTrue(ok)
        self.assertEqual(project.on_list(self.ws), ["geardoor"])
        project.switch(self.ws, "geardoor", False)
        self.assertEqual(project.on_list(self.ws), [])
        ok, msg = project.switch(self.ws, "ghost", True)
        self.assertFalse(ok)

    def test_done_rides_the_provisional_lane(self):
        project.new(self.ws, "geardoor")
        ok, msg = project.done(self.ws, "geardoor")
        self.assertTrue(ok)
        c = project.parse_contract(project.contract_path(self.ws, "geardoor"))
        self.assertEqual(c["state"], "done")  # it happened now
        acts = provisional.pending(self.ws, "geardoor")
        self.assertEqual(len(acts), 1)  # and waits for the confirm
        provisional.revert(self.ws, acts[0]["id"])
        c = project.parse_contract(project.contract_path(self.ws, "geardoor"))
        self.assertEqual(c["state"], "active")  # one key put it back

    def test_root_of_honors_declared_root(self):
        project.new(self.ws, "body")
        elsewhere = tempfile.mkdtemp(prefix="sbx8r-")
        with open(project.contract_path(self.ws, "body"), "a") as f:
            f.write("root: %s\n" % elsewhere)
        self.assertEqual(project.root_of(self.ws, "body"), elsewhere)

    def test_checks_parse(self):
        project.new(self.ws, "geardoor")
        with open(project.contract_path(self.ws, "geardoor"), "a") as f:
            f.write("\n## checks\necho one\necho two\n")
        c = project.parse_contract(project.contract_path(self.ws, "geardoor"))
        self.assertEqual(c["checks"], ["echo one", "echo two"])


if __name__ == "__main__":
    unittest.main()
