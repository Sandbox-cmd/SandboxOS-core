# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the guard: every fence proven to fire, and to stay open where it should.

The guard ships in the plugin now, so it is imported from there — the same
file the host runs at `${CLAUDE_PLUGIN_ROOT}/hooks/guard.py`. Three claims
live here. The four write fences fire. The Bash branch reads write intent and
nothing else, which is the 8.2.3 scar as a check: a substring match blocked
`cat .sandbox/journal.jsonl` and made the record unreadable to a session that
was only looking. And anything the guard cannot parse exits 0 and allows.
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

from . import REPO

HOOKS = os.path.join(REPO, "vessel", "plugin", "hooks")
sys.path.insert(0, HOOKS)
import guard  # noqa: E402


def write_event(path, tool="Write"):
    return {"tool_name": tool, "tool_input": {"file_path": path}}


def bash_event(command):
    return {"tool_name": "Bash", "tool_input": {"command": command}}


class GuardCase(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9g-")
        os.makedirs(os.path.join(self.ws, "projects", "geardoor"), exist_ok=True)
        os.makedirs(os.path.join(self.ws, "projects", "other"), exist_ok=True)
        # a system tree of its own, so the fence is proved without standing
        # inside the real one.
        self.tree = tempfile.mkdtemp(prefix="sbx9core-")
        self.root = os.path.join(self.tree, "vessel", "plugin")

    def reason(self, out):
        return out.get("hookSpecificOutput", {}).get("permissionDecisionReason")

    def denied(self, out):
        if not out:
            return None
        self.assertEqual(out["decision"], "block", out)
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertEqual(out["reason"], self.reason(out),
                         "the two shapes carry different words")
        return out["reason"]

    def decide(self, event, **kw):
        kw.setdefault("ws", self.ws)
        kw.setdefault("root", self.root)
        return guard.decide(event, **kw)


class TestTheFourWriteFences(GuardCase):
    def test_a_write_into_the_record_is_turned_back(self):
        out = self.decide(write_event(
            os.path.join(self.ws, guard.STATE, "journal.jsonl")))
        self.assertEqual(
            self.denied(out),
            "i keep the record for the verbs that write it. "
            "stage this instead: sandbox note")

    def test_every_write_tool_meets_the_same_fence(self):
        for tool in guard.WRITE_TOOLS:
            out = self.decide(write_event(
                os.path.join(self.ws, guard.STATE, "place.json"), tool=tool))
            self.assertTrue(self.denied(out), tool)
        self.assertNotIn("MultiEdit", guard.WRITE_TOOLS)

    def test_a_write_into_the_hosts_memory_is_routed_to_the_key(self):
        out = self.decide(write_event(
            os.path.expanduser("~/.claude/projects/x/memory/MEMORY.md")))
        self.assertEqual(
            self.denied(out),
            "memory lands on your k, so i turned that write back. "
            "stage it instead: sandbox note")

    def test_a_write_into_agent_memory_is_turned_back(self):
        out = self.decide(write_event(
            os.path.expanduser("~/.claude/agent-memory/notes.md")))
        self.assertEqual(
            self.denied(out),
            "agent memory is a second record no one audits — i stopped that "
            "write. put it in your report, or stage it: sandbox note")

    def test_a_write_into_another_project_names_both(self):
        cwd = os.path.join(self.ws, "projects", "geardoor")
        out = self.decide(write_event(
            os.path.join(self.ws, "projects", "other", "file.md")), cwd=cwd)
        self.assertEqual(
            self.denied(out),
            "you are sitting in geardoor, so i left that write in other alone. "
            "switch first: sandbox project")

    def test_the_cross_project_line_takes_exactly_two_names(self):
        """repair B3: the drafted line carried three placeholders against a
        two-argument call, so `decide` raised and every fence behind it fell
        open. The count is a check now, not a reading."""
        self.assertEqual(guard.CROSS_PROJECT.count("%s"), 2)

    def test_a_write_into_the_system_tree_is_turned_back(self):
        out = self.decide(write_event(
            os.path.join(self.tree, "engine", "cli.py")))
        self.assertEqual(
            self.denied(out),
            "the system tree keeps its own repo and checks, and i hold you "
            "to them — edit it in ~/Sandbox/system on a branch")

    def test_the_system_tree_is_derived_from_the_plugin_root(self):
        """rule R2: the `engine-root` pointer file is gone, and with it the copy of
        a path that could name a tree the owner had already moved."""
        self.assertEqual(guard._system_tree(self.root), self.tree)
        os.environ["CLAUDE_PLUGIN_ROOT"] = self.root
        try:
            self.assertEqual(guard._system_tree(), self.tree)
        finally:
            os.environ.pop("CLAUDE_PLUGIN_ROOT", None)

    def test_ordinary_writes_pass(self):
        cwd = os.path.join(self.ws, "projects", "geardoor")
        self.assertEqual(self.decide(write_event(
            os.path.join(cwd, "notes.md")), cwd=cwd), {})
        self.assertEqual(self.decide(write_event(
            os.path.join(self.ws, "CLAUDE.md")), cwd=self.ws), {})


class TestTheBashBranchReadsIntent(GuardCase):
    """the 8.2.3 scar: the substring fence blocked reads of the record."""

    READS = (
        "cat .sandbox/journal.jsonl",
        "grep -r sandbox .sandbox",
        "ls -la .sandbox",
        "head -5 .sandbox/place.json",
        "tail -n 20 .sandbox/staging.jsonl",
        "wc -l .sandbox/journal.jsonl",
        "git log --oneline -- .sandbox",
        "sandbox recall geardoor",
        "python3 -c 'print(1)'",
        "diff a.txt b.txt",
    )
    WRITES = (
        "echo x > .sandbox/journal.jsonl",
        "echo x >> .sandbox/journal.jsonl",
        "cat notes | tee .sandbox/place.json",
        "sed -i '' s/a/b/ .sandbox/place.json",
        "rm -rf .sandbox",
        "mv .sandbox/journal.jsonl /tmp/j",
        "cp /tmp/j .sandbox/journal.jsonl",
        "truncate -s 0 .sandbox/journal.jsonl",
        "mkdir -p .sandbox/vessel",
        "touch .sandbox/place.json",
        "chmod 777 .sandbox/journal.jsonl",
        "python3 - <<'PY'\nopen('.sandbox/journal.jsonl','w')\nPY",
    )

    def test_reading_the_record_passes(self):
        for command in self.READS:
            self.assertEqual(self.decide(bash_event(command)), {},
                             "a read was turned back: %s" % command)

    def test_writing_the_record_is_turned_back(self):
        for command in self.WRITES:
            out = self.decide(bash_event(command))
            self.assertEqual(
                self.denied(out),
                "that command writes the record, and i keep it for the verbs — "
                "reading is free; change it with: sandbox note",
                command)

    def test_a_write_form_over_a_path_that_is_not_fenced_passes(self):
        self.assertEqual(self.decide(bash_event("rm -rf build/")), {})
        self.assertEqual(self.decide(bash_event("echo hi > /tmp/x")), {})

    def test_an_arrow_is_not_a_redirect(self):
        """`->`, `=>`, `>=` and `2>&1` are not writes, and a command that only
        reads the record must not be denied for carrying one."""
        for command in ("cat .sandbox/journal.jsonl 2>&1",
                        "grep -- '->' .sandbox/journal.jsonl",
                        "python3 -c 'print(1 >= 0)' && ls .sandbox"):
            self.assertEqual(self.decide(bash_event(command)), {}, command)

    def test_the_bash_branch_holds_the_agent_memory_fence_too(self):
        """item C10 (repair S1, third sighting): the memory fence sat inside the
        write-tools branch, so a shell append to the same directory met
        nothing at all."""
        for command in ("cat >> ~/.claude/agent-memory/x",
                        "echo note > ~/.claude/agent-memory/geardoor.md",
                        "mkdir -p ~/.claude/agent-memory/new"):
            out = self.decide(bash_event(command))
            self.assertEqual(
                self.denied(out),
                "agent memory is a second record no one audits — i stopped that "
                "write. put it in your report, or stage it: sandbox note",
                command)

    def test_reading_agent_memory_passes(self):
        self.assertEqual(
            self.decide(bash_event("cat ~/.claude/agent-memory/x")), {})


class TestTheRefusalsThemselves(GuardCase):
    REFUSALS = ("RECORD_WRITE", "MEMORY_WRITE", "AGENT_MEMORY_WRITE",
                "CROSS_PROJECT", "SYSTEM_TREE", "RECORD_COMMAND")

    def test_there_are_six_and_each_says_i(self):
        for name in self.REFUSALS:
            text = getattr(guard, name)
            self.assertIn("i ", " " + text, name)
            self.assertTrue(text[0].islower(), name)

    def test_each_one_names_a_door(self):
        for name in self.REFUSALS:
            text = getattr(guard, name)
            self.assertTrue("sandbox " in text or "~/Sandbox/system" in text,
                            "%s names no door" % name)

    def test_no_two_open_with_the_same_words(self):
        """repair S7: five of the six opened with the same four words, and a
        reader stops reading the opening they have already read."""
        openings = [" ".join(getattr(guard, n).split()[:3]) for n in self.REFUSALS]
        self.assertEqual(len(set(openings)), len(openings), openings)

    def test_no_insider_noun_reaches_a_person_mid_mistake(self):
        for name in self.REFUSALS:
            text = getattr(guard, name).lower()
            for word in ("desk", "wall", "seam", "ink", "amana"):
                self.assertNotIn(word, text, "%s says %r" % (name, word))


class TestFailOpen(GuardCase):
    def test_malformed_events_decide_nothing(self):
        self.assertEqual(guard.decide({"tool_name": "Write"}), {})
        self.assertEqual(guard.decide({}), {})
        self.assertEqual(guard.decide({"tool_name": "Bash", "tool_input": None}), {})

    def _run(self, stdin, env=None):
        e = dict(os.environ)
        e["CLAUDE_PLUGIN_ROOT"] = self.root
        e["SANDBOX_HOME"] = self.ws
        e.update(env or {})
        return subprocess.run(["python3", os.path.join(HOOKS, "guard.py")],
                              input=stdin, capture_output=True, text=True,
                              timeout=60, env=e)

    def test_unparseable_stdin_exits_zero_and_says_nothing(self):
        run = self._run("not json at all")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout.strip(), "{}")

    def test_an_allowed_call_exits_zero(self):
        run = self._run(json.dumps(write_event(
            os.path.join(self.ws, "projects", "geardoor", "notes.md"))))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads(run.stdout), {})

    def test_a_denied_call_carries_both_shapes_the_host_might_read(self):
        """exit 2 with the refusal on stderr is the documented block; the JSON
        decision on stdout is the other shape a host may honor. Both, so
        whichever this host reads, the fence holds."""
        run = self._run(json.dumps(write_event(
            os.path.join(self.ws, guard.STATE, "journal.jsonl"))))
        self.assertEqual(run.returncode, 2)
        said = json.loads(run.stdout)
        self.assertEqual(said["decision"], "block")
        self.assertIn("sandbox note", said["reason"])
        self.assertEqual(run.stderr.strip(), said["reason"])


if __name__ == "__main__":
    unittest.main()
