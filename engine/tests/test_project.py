# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""projects: born with a contract and a history, closed on the owner's confirm."""
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


class TestTheTemplatesItWrites(unittest.TestCase):
    """item X10 — what a person or a model opens later, and what it says."""

    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)

    def test_the_checks_section_says_what_belongs_under_it(self):
        project.new(self.ws, "geardoor", "the store's data")
        p = project.contract_path(self.ws, "geardoor")
        with open(p, encoding="utf-8") as f:
            text = f.read()
        self.assertIn("## checks\n%s\n" % project.CHECKS_HINT, text)
        self.assertIn("one command per line", project.CHECKS_HINT)

    def test_the_hint_is_a_comment_and_never_a_check(self):
        """it sits inside `## checks`, so a parser that read it would hand
        `sandbox ship` a line no shell can run."""
        project.new(self.ws, "geardoor")
        c = project.parse_contract(project.contract_path(self.ws, "geardoor"))
        self.assertEqual(c["checks"], [])
        p = project.contract_path(self.ws, "geardoor")
        with open(p, encoding="utf-8") as f:
            text = f.read()
        with open(p, "w", encoding="utf-8") as f:
            f.write(text.replace(project.CHECKS_HINT,
                                 project.CHECKS_HINT + "\necho one"))
        c = project.parse_contract(p)
        self.assertEqual(c["checks"], ["echo one"])

    def test_the_canon_header_carries_its_reason_and_its_door(self):
        project.new(self.ws, "geardoor")
        with open(os.path.join(project.dirpath(self.ws, "geardoor"),
                               "CANON.md"), encoding="utf-8") as f:
            head = f.read()
        self.assertIn(project.CANON_HEADER, head)
        self.assertIn("sandbox note", project.CANON_HEADER)
        self.assertIn("lost on the next rebuild", project.CANON_HEADER)
        self.assertIn("edits here are", project.CANON_HEADER)

    def test_the_same_header_comes_out_of_the_other_writer(self):
        """two writers, one line: project.new presses the page and
        notes.refresh_canon rebuilds it."""
        from engine import notes
        project.new(self.ws, "geardoor")
        notes.refresh_canon(self.ws, "geardoor")
        with open(os.path.join(project.dirpath(self.ws, "geardoor"),
                               "CANON.md"), encoding="utf-8") as f:
            self.assertIn(project.CANON_HEADER, f.read())

    def test_a_root_gets_the_contract_line_and_both_briefs(self):
        root = tempfile.mkdtemp(prefix="sbx8root-")
        pname = "geardoor"
        ok, msg = project.new(self.ws, pname, "the store's data", root=root)
        self.assertTrue(ok, msg)
        c = project.parse_contract(project.contract_path(self.ws, "geardoor"))
        self.assertEqual(c["root"], root)
        self.assertEqual(project.root_of(self.ws, "geardoor"), root)
        for name in project.BRIEFS:
            p = os.path.join(root, name)
            self.assertTrue(os.path.exists(p), p)
            with open(p, encoding="utf-8") as f:
                text = f.read()
            self.assertLessEqual(len(text.strip().splitlines()), 12, name)
            self.assertIn(pname, text)   # the project it belongs to
            self.assertIn("sandbox status", text)
            self.assertIn("sandbox note", text)
            self.assertIn("CLAUDE.md", text)
        self.assertIn("on the root — what this project is", msg)
        self.assertTrue(all(n in msg for n in project.BRIEFS), msg)

    def test_a_file_already_on_the_root_is_left_as_it_is(self):
        root = tempfile.mkdtemp(prefix="sbx8root-")
        with open(os.path.join(root, "CLAUDE.md"), "w", encoding="utf-8") as f:
            f.write("mine, and older than this project\n")
        ok, msg = project.new(self.ws, "geardoor", root=root)
        self.assertTrue(ok, msg)
        with open(os.path.join(root, "CLAUDE.md"), encoding="utf-8") as f:
            self.assertEqual(f.read(), "mine, and older than this project\n")
        self.assertIn("already lives on that root — left as it is", msg)
        self.assertTrue(msg.count("CLAUDE.md"), msg)
        self.assertTrue(os.path.exists(os.path.join(root, "AGENTS.md")))

    def test_the_workshop_as_a_root_gets_no_second_charter(self):
        """the charter is already there; a copy of it under another name is
        a second page saying what one page says."""
        ok, msg = project.new(self.ws, "geardoor", root=self.ws)
        self.assertTrue(ok, msg)
        for name in project.BRIEFS:
            self.assertFalse(os.path.exists(os.path.join(self.ws, name)), name)

    def test_a_root_that_is_not_there_refuses_with_the_door(self):
        ok, msg = project.new(self.ws, "geardoor", root="/nowhere/at/all")
        self.assertFalse(ok)
        self.assertIn("sandbox project new", msg)
        self.assertFalse(os.path.exists(project.contract_path(self.ws, "geardoor")))

    def test_a_root_with_its_own_history_gets_no_briefs(self):
        """the 2026-10-23 scar: two untracked pages in the release-only main."""
        for kind in ("dir", "file"):
            root = tempfile.mkdtemp(prefix="sbx8git-")
            git = os.path.join(root, ".git")
            if kind == "dir":
                os.makedirs(git)
            else:
                with open(git, "w", encoding="utf-8") as f:
                    f.write("gitdir: /elsewhere/.git/worktrees/x\n")
            ok, msg = project.new(self.ws, "tree-" + kind, root=root)
            self.assertTrue(ok, msg)
            for name in project.BRIEFS:
                self.assertFalse(os.path.exists(os.path.join(root, name)), name)
            self.assertIn("is a git repository with its own history — left "
                          "untouched", msg)
            self.assertIn("add a brief there yourself", msg)


class TestNow(unittest.TestCase):
    """phase 1 of the reset: a session starts from NOW.md, not the archive."""

    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)

    def write_now(self, name, nxt):
        p = os.path.join(project.dirpath(self.ws, name), project.NOW)
        with open(p, encoding="utf-8") as f:
            text = f.read()
        with open(p, "w", encoding="utf-8") as f:
            f.write(text.replace("**Next.**", "**Next.** " + nxt))

    def test_a_new_project_starts_from_now_md(self):
        project.new(self.ws, "geardoor", "the store's data")
        d = project.dirpath(self.ws, "geardoor")
        with open(os.path.join(d, project.NOW), encoding="utf-8") as f:
            page = f.read()
        self.assertTrue(page.startswith("# geardoor: now ("), page)
        lines = page.splitlines()
        self.assertEqual(lines[4], "**Outcome.** the store's data")
        self.assertIn("**Where it stands.** Just made.", page)
        self.assertIn("CANON.md is the archive", page)
        for field in ("**Authority.**", "**Next.**"):
            self.assertIn(field, page)
        with open(project.contract_path(self.ws, "geardoor"),
                  encoding="utf-8") as f:
            contract = f.read().splitlines()
        notes_at = contract.index("## notes")
        self.assertEqual(contract[notes_at + 1], "start here: NOW.md")

    def test_project_for_path_reads_the_projects_dir(self):
        project.new(self.ws, "geardoor")
        inside = os.path.join(project.dirpath(self.ws, "geardoor"), "sub")
        os.makedirs(inside)
        self.assertEqual(project.project_for_path(self.ws, inside), "geardoor")
        self.assertIsNone(project.project_for_path(self.ws, self.ws))

    def test_project_for_path_reads_a_declared_root_and_the_deepest_wins(self):
        outer = tempfile.mkdtemp(prefix="sbx8root-")
        inner = os.path.join(outer, "inner")
        os.makedirs(os.path.join(inner, "deep"))
        project.new(self.ws, "outer", root=outer)
        project.new(self.ws, "inner", root=inner)
        self.assertEqual(project.project_for_path(self.ws, outer), "outer")
        self.assertEqual(project.project_for_path(
            self.ws, os.path.join(inner, "deep")), "inner")
        self.assertIsNone(project.project_for_path(self.ws, tempfile.gettempdir()))

    def test_a_done_project_claims_no_path(self):
        root = tempfile.mkdtemp(prefix="sbx8root-")
        project.new(self.ws, "geardoor", root=root)
        project.done(self.ws, "geardoor")
        self.assertIsNone(project.project_for_path(self.ws, root))
        self.assertIsNone(project.project_for_path(
            self.ws, project.dirpath(self.ws, "geardoor")))

    def test_now_brief_standing_in_a_project_gives_its_page(self):
        project.new(self.ws, "geardoor", "the store's data")
        out = project.now_brief(self.ws, path=project.dirpath(self.ws, "geardoor"))
        self.assertTrue(out.startswith(
            "now — geardoor (projects/geardoor/NOW.md):\n# geardoor: now ("), out)
        self.assertEqual(out, project.now_brief(self.ws, name="geardoor"))

    def test_now_brief_cuts_a_long_page(self):
        project.new(self.ws, "geardoor")
        p = os.path.join(project.dirpath(self.ws, "geardoor"), project.NOW)
        with open(p, "a", encoding="utf-8") as f:
            f.write("x" * (project.NOW_LIMIT * 2))
        self.assertEqual(len(project.now_page(self.ws, "geardoor")),
                         project.NOW_LIMIT)

    def test_now_brief_elsewhere_lists_the_on_projects_next_lines(self):
        for name in ("geardoor", "offshop", "quiet"):
            project.new(self.ws, name)
        self.write_now("geardoor", "wire the refund path")
        self.write_now("offshop", "nothing, it is off")
        os.remove(os.path.join(project.dirpath(self.ws, "quiet"), project.NOW))
        project.switch(self.ws, "geardoor", True)
        project.switch(self.ws, "quiet", True)
        out = project.now_brief(self.ws, path=tempfile.gettempdir())
        self.assertEqual(out, "now — geardoor: wire the refund path")

    def test_now_brief_is_empty_when_nothing_is_on(self):
        project.new(self.ws, "geardoor")
        self.assertEqual(project.now_brief(self.ws, path=self.ws), "")

    def test_next_line_reads_the_line_or_the_one_under_it(self):
        self.assertEqual(project.next_line("**Next.** ship it\n"), "ship it")
        self.assertEqual(project.next_line("**Next.**\n\n- ship it\n"), "- ship it")
        self.assertEqual(project.next_line("no such field"), "")


if __name__ == "__main__":
    unittest.main()
