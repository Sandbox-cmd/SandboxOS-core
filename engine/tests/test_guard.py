# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The guard: every fence proven to fire, and to stay open where it should."""
import os
import sys
import tempfile
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(REPO, "vessel", "claude-code"))
import guard  # noqa: E402


def write_event(path, tool="Write"):
    return {"tool_name": tool, "tool_input": {"file_path": path}}


class TestGuard(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        os.makedirs(os.path.join(self.ws, "projects", "geardoor"), exist_ok=True)
        os.makedirs(os.path.join(self.ws, "projects", "other"), exist_ok=True)

    def _denied(self, out):
        return out.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

    def test_record_write_denied(self):
        out = guard.decide(write_event(os.path.join(self.ws, guard.STATE, "journal.jsonl")),
                           ws=self.ws)
        self.assertTrue(self._denied(out))
        self.assertIn("sandbox note", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_bash_naming_the_record_denied(self):
        out = guard.decide({"tool_name": "Bash",
                            "tool_input": {"command": "cat %s/journal.jsonl" % guard.STATE}},
                           ws=self.ws)
        self.assertTrue(self._denied(out))

    def test_auto_memory_write_routed_to_the_gate(self):
        p = os.path.expanduser("~/.claude/projects/x/memory/MEMORY.md")
        out = guard.decide(write_event(p), ws=self.ws)
        self.assertTrue(self._denied(out))
        self.assertIn("sandbox note", out["hookSpecificOutput"]["permissionDecisionReason"])

    def test_cross_project_write_denied_same_project_passes(self):
        cwd = os.path.join(self.ws, "projects", "geardoor")
        other = os.path.join(self.ws, "projects", "other", "file.md")
        mine = os.path.join(self.ws, "projects", "geardoor", "file.md")
        self.assertTrue(self._denied(guard.decide(write_event(other), ws=self.ws, cwd=cwd)))
        self.assertEqual(guard.decide(write_event(mine), ws=self.ws, cwd=cwd), {})

    def test_core_tree_fenced_from_workshop_sessions(self):
        core = tempfile.mkdtemp(prefix="sbx8core-")
        hookdir = os.path.dirname(os.path.abspath(guard.__file__))
        rootfile = os.path.join(hookdir, "engine-root")
        with open(rootfile, "w") as f:
            f.write(core)
        try:
            out = guard.decide(write_event(os.path.join(core, "engine", "cli.py")), ws=self.ws)
            self.assertTrue(self._denied(out))
        finally:
            os.remove(rootfile)

    def test_ordinary_writes_pass(self):
        out = guard.decide(write_event(os.path.join(self.ws, "projects", "geardoor", "notes.md")),
                           ws=self.ws,
                           cwd=os.path.join(self.ws, "projects", "geardoor"))
        self.assertEqual(out, {})

    def test_malformed_input_fails_open(self):
        self.assertEqual(guard.decide({"tool_name": "Write"}), {})
        self.assertEqual(guard.decide({}), {})


if __name__ == "__main__":
    unittest.main()
