# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the plugin, held to what it may do — and to the one op it may mint.

Two scars are tests here. The 07-31 one is a path: a hook command that
resolved one directory above the plugin root read as a block and denied every
write, so every command in `hooks.json` is resolved against the root and the
file it names is opened. The custody-by-proxy one is a claim: a hook that
lands anything would be the model writing the record through a shell. That is
proved positively rather than greped — each hook runs against a throwaway
workshop with a synthetic event on its stdin, and the journal afterwards is
allowed to have grown by `session` rows and by nothing else.
"""
import ast
import contextlib
import io
import json
import os
import shutil
import subprocess
import tempfile
import unittest

from engine import journal, vessel, voicelint

from . import REPO

PLUGIN = os.path.join(REPO, "vessel", "plugin")
HOOKS = os.path.join(PLUGIN, "hooks")
LANDING_VERBS = ("approve", "resume", "ship")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _json(path):
    return json.loads(_read(path))


def _events(ws):
    events, _scars = journal.read(ws)
    return events


class TestPluginRoot(unittest.TestCase):
    """the 07-31 scar, as a check."""

    def test_every_hook_command_resolves_inside_the_plugin_root(self):
        wiring = vessel.hook_commands()
        self.assertEqual({e for e, _m, _c in wiring},
                         {"SessionStart", "PreToolUse", "Stop", "SessionEnd"})
        root = os.path.realpath(PLUGIN)
        for event, _matcher, command in wiring:
            self.assertIn("${CLAUDE_PLUGIN_ROOT}", command, event)
            self.assertTrue(command.startswith("python3 "), command)
            rel = command.split("${CLAUDE_PLUGIN_ROOT}", 1)[1].strip('" ')
            target = os.path.realpath(os.path.join(root, rel.lstrip("/")))
            self.assertTrue(target.startswith(root + os.sep),
                            "%s resolves outside the plugin: %s" % (event, target))
            self.assertTrue(os.path.exists(target), target)

    def test_the_write_matcher_names_the_tools_the_guard_reads(self):
        by_event = {e: m for e, m, _c in vessel.hook_commands()}
        self.assertEqual(by_event["PreToolUse"], "Edit|Write|NotebookEdit|Bash")

    def test_payload_names_what_ships_and_what_init_places(self):
        ships = vessel.payload()
        self.assertEqual(ships["root"], PLUGIN)
        for name in ("hooks/hooks.json", "hooks/guard.py", "crew.json",
                     "crew-tail.md", ".claude-plugin/plugin.json", "README.md",
                     "commands/make.md", "commands/sandbox.md",
                     "output-styles/across-the-desk.md",
                     "agents/checker.md", "skills/sandbox-workshop/SKILL.md"):
            self.assertIn(name, ships["ships"], name)
        self.assertEqual([os.path.basename(p) for p in ships["places"]],
                         ["CLAUDE.md"])
        for path in ships["places"]:
            self.assertTrue(os.path.exists(path), path)

    def test_init_places_the_manifest_list_and_nothing_beside_it(self):
        """one list: `places` is what init copies, read off the manifest
        rather than typed a second time in onboard.py. 9.0 shrank it to the
        contract, and everything else is loaded from the plugin."""
        from engine import onboard
        tmp = tempfile.mkdtemp(prefix="places-")
        ws = os.path.join(tmp, "Sandbox")
        try:
            placed = onboard.shipped_payload(ws)
            self.assertEqual(sorted(placed.values()),
                             sorted(vessel.payload()["places"]))
            self.assertEqual(sorted(placed), [os.path.join(ws, "CLAUDE.md")])
            for src in placed.values():
                self.assertNotIn(os.path.realpath(PLUGIN) + os.sep,
                                 os.path.realpath(src),
                                 "init copies a file the plugin already serves")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


class TestNoLanding(unittest.TestCase):
    """law 10, greped where a grep is honest: a hook never runs the key's verb."""

    def _files(self, *dirs):
        out = []
        for d in dirs:
            for dirpath, dirnames, filenames in os.walk(d):
                dirnames[:] = [x for x in dirnames if x != "__pycache__"]
                out += [os.path.join(dirpath, n) for n in sorted(filenames)]
        return out

    def test_no_hook_calls_a_landing_verb(self):
        """the hooks pass verbs to a shell as string literals; none is a
        verb that reads the owner's key."""
        for path in self._files(HOOKS):
            if not path.endswith(".py"):
                continue
            tree = ast.parse(_read(path), path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    self.assertNotIn(node.value.strip(), LANDING_VERBS,
                                     "%s runs %r" % (path, node.value))

    def test_the_commands_only_tell_the_owner(self):
        """a command may say the word in prose addressed to the owner; it may
        never sit on a line the session is told to run."""
        for path in self._files(os.path.join(PLUGIN, "commands")):
            for n, line in enumerate(_read(path).splitlines(), 1):
                low = line.lower()
                if not any(v in low for v in LANDING_VERBS):
                    continue
                self.assertFalse(low.lstrip().startswith("!"),
                                 "%s:%d runs a landing verb" % (path, n))
                self.assertFalse(low.startswith("allowed-tools:"),
                                 "%s:%d permits a landing verb" % (path, n))
                self.assertTrue("your" in low or "their" in low or "owner" in low,
                                "%s:%d names a landing verb outside prose: %s"
                                % (path, n, line.strip()))


    def test_a_landing_verb_only_ever_appears_in_prose(self):
        """the grep the spec asks for: `sandbox approve|resume|ship` inside
        the plugin sits on a line of prose about what the owner types, and
        never on a line the plugin runs."""
        import re
        rx = re.compile(r"sandbox (approve|resume|ship)\b")
        for path in self._files(HOOKS, os.path.join(PLUGIN, "commands")):
            for n, line in enumerate(_read(path).splitlines(), 1):
                if not rx.search(line):
                    continue
                prose = line.lstrip().startswith(("#", '"""', "*", "-")) \
                    or "`" in line or line.lstrip().startswith("The ")
                self.assertTrue(prose, "%s:%d runs a landing verb: %s"
                                % (path, n, line.strip()))


class TestNoWriteOutsideTheRoot(unittest.TestCase):
    def test_no_hook_opens_a_file_for_writing(self):
        """everything a hook keeps goes through a `sandbox` verb, so no hook
        holds a write handle of its own."""
        for name in sorted(os.listdir(HOOKS)):
            if not name.endswith(".py"):
                continue
            path = os.path.join(HOOKS, name)
            tree = ast.parse(_read(path), path)
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                fn = node.func
                if not (isinstance(fn, ast.Name) and fn.id == "open"):
                    continue
                mode = node.args[1] if len(node.args) > 1 else None
                text = mode.value if isinstance(mode, ast.Constant) else "r"
                self.assertNotIn("w", text, "%s writes" % name)
                self.assertNotIn("a", text, "%s appends" % name)


class HookRun(unittest.TestCase):
    """the shared rig: a throwaway workshop, a jailed home, one hook run."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="plugin-")
        self.ws = os.path.join(self.tmp, "Sandbox")
        self.home = os.path.join(self.tmp, "home")
        os.makedirs(self.home)
        from engine import onboard
        onboard.run(self.ws)
        self.before = len(_events(self.ws))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_hook(self, name, event):
        env = dict(os.environ)
        env.update({"SANDBOX_HOME": self.ws, "HOME": self.home,
                    "CLAUDE_PLUGIN_ROOT": PLUGIN,
                    "SANDBOX_SHIM_DIR": os.path.join(self.tmp, "bin")})
        run = subprocess.run(
            ["python3", os.path.join(HOOKS, name)],
            input=json.dumps(event), capture_output=True, text=True,
            timeout=60, env=env, cwd=self.ws)
        return run

    def transcript(self, rows):
        p = os.path.join(self.tmp, "transcript.jsonl")
        with open(p, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        return p

    def new_ops(self):
        return [e.get("op") for e in _events(self.ws)[self.before:]]


class TestHooksMintOnlySession(HookRun):
    def test_every_hook_mints_session_and_nothing_else(self):
        events = {
            "session-start.py": {"session_id": "probe-1", "cwd": self.ws},
            "guard.py": {"tool_name": "Write", "cwd": self.ws,
                         "tool_input": {"file_path": os.path.join(self.ws, "x.md")}},
            "sweep.py": {"cwd": self.ws,
                         "transcript_path": self.transcript([
                             {"type": "assistant",
                              "message": {"role": "assistant", "content": [
                                  {"type": "text",
                                   "text": "finding: the probe found one thing"}]}}])},
            "session-end.py": {"session_id": "probe-1", "cwd": self.ws,
                               "transcript_path": self.transcript([])},
        }
        for name, event in events.items():
            run = self.run_hook(name, event)
            self.assertEqual(run.returncode, 0, "%s: %s" % (name, run.stderr))
        self.assertEqual(set(self.new_ops()), {"session"},
                         "a hook minted something other than a sitting")
        landed = [e for e in _events(self.ws)[self.before:]
                  if e.get("op") == "assert"]
        self.assertEqual(landed, [], "a hook landed a claim")

    def test_the_sweep_stages_and_lands_nothing(self):
        from engine import desk
        before, _ = desk.drafts(self.ws)
        run = self.run_hook("sweep.py", {
            "cwd": self.ws,
            "transcript_path": self.transcript([
                {"type": "assistant", "message": {"role": "assistant", "content": [
                    {"type": "text", "text":
                     "here is what i did.\nfinding: the scrub refuses its own card\n"
                     "ruling: the close always refuses on red"}]}},
                {"type": "user", "message": {"role": "user", "content": "finding: not mine"}},
                {"systemMessage": "the host's own hook said this"},
            ])})
        self.assertEqual(run.returncode, 0, run.stderr)
        after, _ = desk.drafts(self.ws)
        bodies = [d.get("body") for d in after[len(before):]]
        self.assertEqual(len(bodies), 3, bodies)
        self.assertIn("finding: the scrub refuses its own card", bodies)
        self.assertIn("ruling: the close always refuses on red", bodies)
        self.assertTrue(any("the host's own hook" in b for b in bodies), bodies)
        self.assertFalse(any("not mine" in b for b in bodies),
                         "the sweep read the person's words as its own")
        self.assertIn("3 findings staged — sandbox drafts", run.stdout)
        self.assertEqual(set(self.new_ops()) - {"session"}, set())

    def test_the_sweep_says_a_thing_once(self):
        rows = [{"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "text", "text": "finding: the same line twice"}]}}]
        first = self.run_hook("sweep.py", {"cwd": self.ws,
                                           "transcript_path": self.transcript(rows)})
        second = self.run_hook("sweep.py", {"cwd": self.ws,
                                            "transcript_path": self.transcript(rows)})
        self.assertIn("1 finding staged", first.stdout)
        self.assertEqual(second.stdout.strip(), "",
                         "the sweep staged a line that was already waiting")

    def test_the_sweep_is_silent_when_the_turn_found_nothing(self):
        run = self.run_hook("sweep.py", {"cwd": self.ws,
                                         "transcript_path": self.transcript([
                                             {"type": "assistant",
                                              "message": {"role": "assistant",
                                                          "content": [{"type": "text",
                                                                       "text": "done."}]}}])})
        self.assertEqual(run.stdout.strip(), "")
        self.assertEqual(run.returncode, 0)


class TestTheTwoSittingHooks(HookRun):
    def test_session_start_prints_one_needs_sentence_and_opens(self):
        from engine import notes
        notes.note(self.ws, "the scrub refuses its own card")
        run = self.run_hook("session-start.py",
                            {"session_id": "probe-2", "cwd": self.ws})
        self.assertEqual(run.returncode, 0, run.stderr)
        said = json.loads(run.stdout)["hookSpecificOutput"]
        self.assertEqual(said["hookEventName"], "SessionStart")
        line = said["additionalContext"]
        self.assertEqual(len(line.splitlines()), 1, line)
        self.assertTrue(line.startswith("one thing needs you"), line)
        self.assertNotIn("— sandbox ", line,
                         "the needs line offers a door the hook could walk through")
        opened = [e for e in _events(self.ws)[self.before:]
                  if e.get("op") == "session" and e.get("phase") == "open"]
        self.assertEqual([e.get("key") for e in opened], ["probe-2"])

    def test_session_start_says_so_when_nothing_waits(self):
        run = self.run_hook("session-start.py",
                            {"session_id": "probe-3", "cwd": self.ws})
        line = json.loads(run.stdout)["hookSpecificOutput"]["additionalContext"]
        self.assertEqual(line, "nothing needs you.")

    def test_session_start_inside_a_project_carries_its_now_page(self):
        from engine import project
        project.new(self.ws, "geardoor", "the store's data")
        run = self.run_hook("session-start.py", {
            "session_id": "probe-4",
            "cwd": project.dirpath(self.ws, "geardoor")})
        self.assertEqual(run.returncode, 0, run.stderr)
        said = json.loads(run.stdout)["hookSpecificOutput"]["additionalContext"]
        first, blank, rest = said.split("\n", 2)
        self.assertNotIn("now —", first)  # the needs sentence still opens it
        self.assertEqual(blank, "")
        self.assertTrue(rest.startswith("now — geardoor (projects/geardoor/NOW.md):"),
                        said)
        self.assertEqual(rest.splitlines()[5], "**Outcome.** the store's data")

    def test_session_end_counts_the_seats_the_sitting_called(self):
        self.run_hook("session-start.py", {"session_id": "probe-4", "cwd": self.ws})
        rows = [{"type": "assistant", "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "checker"}},
            {"type": "tool_use", "name": "Agent", "input": {"subagent_type": "checker"}},
            {"type": "tool_use", "name": "Task", "input": {"subagent_type": "voicer"}},
            {"type": "tool_use", "name": "Read", "input": {"file_path": "x"}},
        ]}}]
        run = self.run_hook("session-end.py",
                            {"session_id": "probe-4", "cwd": self.ws,
                             "transcript_path": self.transcript(rows)})
        self.assertEqual(run.returncode, 0, run.stderr)
        closed = [e for e in _events(self.ws)[self.before:]
                  if e.get("op") == "session" and e.get("phase") == "close"]
        self.assertEqual(len(closed), 1, closed)
        self.assertEqual(closed[0].get("agents"), {"checker": 2, "voicer": 1})


class TestCrewIsGenerated(unittest.TestCase):
    def test_every_brief_matches_what_crew_json_renders(self):
        rendered = vessel.render_crew()
        adir = vessel.agents_dir()
        self.assertEqual(sorted(rendered), sorted(os.listdir(adir)))
        for name, text in sorted(rendered.items()):
            self.assertEqual(_read(os.path.join(adir, name)), text,
                             "%s was edited by hand — rebuild it: "
                             "python3 -m engine.vessel --build" % name)
        self.assertEqual(vessel.hand_edited(), [])

    def test_the_shared_tail_is_written_once(self):
        """the tail lives in one file and reaches six briefs; the check is
        that no brief carries a copy crew-tail.md does not."""
        tail = _read(os.path.join(PLUGIN, "crew-tail.md"))
        self.assertIn("## how your report reads", tail)
        for name, text in vessel.render_crew().items():
            self.assertEqual(text.count("## how your report reads"), 1, name)
            self.assertEqual(text.count("## what you find goes on the record"),
                             1, name)


class TestShippedText(unittest.TestCase):
    def test_the_skills_read_under_the_ceiling(self):
        sdir = os.path.join(PLUGIN, "skills")
        found = sorted(os.listdir(sdir))
        self.assertEqual(found, ["backlog-sync", "sandbox-workshop",
                                 "spec-driven-discovery"])
        for name in found:
            path = os.path.join(sdir, name, "SKILL.md")
            rel = os.path.relpath(path, REPO).replace(os.sep, "/")
            text = _read(path)
            d, _words = voicelint.density(text, rel)
            self.assertLessEqual(d, voicelint.CEILING,
                                 "%s is %.2f per 100 words" % (name, d))
            self.assertEqual(voicelint.stacked(text, rel), [], name)
            self.assertEqual(voicelint.naked(text, rel), [], name)

    def test_the_skills_name_no_path_that_died(self):
        sdir = os.path.join(PLUGIN, "skills")
        for name in sorted(os.listdir(sdir)):
            text = _read(os.path.join(sdir, name, "SKILL.md"))
            for dead in ("channels/", "--channel", "~/eighth/core",
                         "~/SandboxOS-core", "cartridges/"):
                self.assertNotIn(dead, text, "%s names %s" % (name, dead))

    def test_the_style_carries_the_rule_and_two_examples(self):
        path = os.path.join(PLUGIN, "output-styles", "across-the-desk.md")
        text = _read(path)
        self.assertLessEqual(len(text.splitlines()), 65)
        rel = "vessel/plugin/output-styles/across-the-desk.md"
        exempt = voicelint.exempt_lines(rel, text, "forbidden")
        self.assertEqual(len(exempt), 1,
                         "the style carries a list again; it names examples")
        self.assertIn("soul/voice.md",
                      _read(os.path.join(PLUGIN, "agents", "voicer.md")))

    def test_the_plugin_and_the_marketplace_say_the_same_sentence(self):
        plugin = _json(os.path.join(PLUGIN, ".claude-plugin", "plugin.json"))
        self.assertEqual(plugin["version"],
                         _read(os.path.join(REPO, "VERSION")).strip())
        market = _json(os.path.join(REPO, ".claude-plugin", "marketplace.json"))
        entry = [p for p in market["plugins"] if p["name"] == plugin["name"]]
        self.assertEqual(len(entry), 1)
        self.assertEqual(entry[0]["description"], plugin["description"])


class TestTheMemoryPage(unittest.TestCase):
    """MEMORY.md is written by the engine and read by the hook, never back."""

    def test_canon_memory_writes_a_projection_the_engine_owns(self):
        from engine import notes, verbs
        tmp = tempfile.mkdtemp(prefix="memory-")
        ws = os.path.join(tmp, "Sandbox")
        try:
            from engine import onboard
            onboard.run(ws)
            journal.append(ws, {"op": "assert", "cls": "note", "origin": "human",
                                "body": "the scrub refuses its own card"})
            journal.append(ws, {"op": "assert", "cls": "ruling", "origin": "human",
                                "stratum": "taste", "body": "close refuses on red"})
            path, n = notes.memory(ws)
            self.assertEqual(path, os.path.join(ws, ".claude", "MEMORY.md"))
            text = _read(path)
            self.assertLessEqual(n, notes.MEMORY_LINES)
            self.assertIn("sandbox canon --memory", text)
            self.assertIn("close refuses on red", text)
            self.assertIn("the scrub refuses its own card", text)
            self.assertIn("canon", verbs.TABLE)
            said = io.StringIO()
            with contextlib.redirect_stdout(said):
                self.assertEqual(verbs.dispatch(ws, "canon", ["--memory"]), 0)
            self.assertIn("projected from the record", said.getvalue())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
