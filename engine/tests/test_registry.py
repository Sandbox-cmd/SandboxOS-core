# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the registry: typed, projection-only, and its schema keeps its promises."""
import ast
import os
import tempfile
import unittest

from engine import apps, check, journal, project, registry, shelf

from . import REPO, key
from .test_app import make_app


class TestSchema(unittest.TestCase):
    def test_every_declared_type_present(self):
        for t in ("project", "build", "app", "note", "ruling", "check",
                  "session", "event"):
            self.assertIn(t, registry.TYPES)
            self.assertTrue(registry.TYPES[t]["description"])

    def test_links_reference_declared_types(self):
        names = set(registry.TYPES) | {"workshop", "any"}
        for frm, link, to, rev in registry.LINKS:
            self.assertIn(frm, names, link)
            self.assertIn(to, names, link)
            self.assertTrue(rev, link)

    def test_ruling_carries_stratum_and_supersession(self):
        self.assertIn("stratum", registry.TYPES["ruling"]["fields"])
        self.assertIn("supersedes", registry.TYPES["ruling"]["fields"])
        self.assertEqual(registry.STRATA, ("law", "taste"))

    def test_fact_shape_refuses_unknown_status(self):
        f = registry.fact("x", "human", "checked", receipt="journal:eid-1")
        self.assertEqual(f["ink"], "checked")
        with self.assertRaises(ValueError):
            registry.fact("x", "vibes", "checked")
        with self.assertRaises(ValueError):
            registry.fact("x", "human", "definitely-true")


class TestProjection(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx8-")
        journal.ensure_genesis(self.ws)

    def test_projection_only_no_second_store(self):
        """projecting writes nothing; two runs answer identically."""
        journal.append(self.ws, {"op": "assert", "cls": "note", "body": "a fact"})
        state_dir = os.path.join(self.ws, journal.STATE_DIR)
        before = sorted(os.listdir(state_dir))
        first = registry.project(self.ws)
        second = registry.project(self.ws)
        self.assertEqual(before, sorted(os.listdir(state_dir)))
        self.assertEqual(first, second)

    def test_rulings_project_with_stratum(self):
        journal.append(self.ws, {"op": "assert", "cls": "ruling",
                                 "body": "plain first", "stratum": "law"})
        journal.append(self.ws, {"op": "assert", "cls": "ruling",
                                 "body": "teal accents"})  # stratum defaults taste
        world = registry.project(self.ws)
        strata = {r["body"]: r["stratum"] for r in world["ruling"]}
        self.assertEqual(strata["plain first"], "law")
        self.assertEqual(strata["teal accents"], "taste")

    def test_newest_word_wins_chronology_kept(self):
        old = journal.append(self.ws, {"op": "assert", "cls": "ruling",
                                       "body": "curses stays"})
        journal.append(self.ws, {"op": "assert", "cls": "ruling",
                                 "body": "textual now", "supersedes": old["id"]})
        world = registry.project(self.ws)
        standing = registry.newest_word(world)
        self.assertEqual([r["body"] for r in standing], ["textual now"])
        self.assertEqual(len(world["ruling"]), 2)  # chronology never deleted

    def test_sessions_are_nameable(self):
        journal.append(self.ws, {"op": "session", "phase": "open",
                                 "key": "s1", "project": "geardoor"})
        journal.append(self.ws, {"op": "session", "phase": "close", "key": "s1"})
        world = registry.project(self.ws)
        self.assertEqual(len(world["session"]), 1)
        self.assertIsNotNone(world["session"][0]["closed"])

    def test_a_close_finds_its_own_open_and_only_that_one(self):
        """the unkeyed-close scar: a close is matched by `key` and by nothing
        else, so a close with no key closes nothing rather than closing
        whichever sitting happened to be open."""
        journal.append(self.ws, {"op": "session", "phase": "open", "key": "a"})
        journal.append(self.ws, {"op": "session", "phase": "open", "key": "b"})
        journal.append(self.ws, {"op": "session", "phase": "close"})  # no key
        world = registry.project(self.ws)
        self.assertEqual([s["closed"] for s in world["session"]], [None, None])
        journal.append(self.ws, {"op": "session", "phase": "close", "key": "b"})
        world = registry.project(self.ws)
        shut = {s["key"]: s["closed"] for s in world["session"]}
        self.assertIsNone(shut["a"])
        self.assertIsNotNone(shut["b"])

    def test_agent_counts_ride_the_close(self):
        journal.append(self.ws, {"op": "session", "phase": "open", "key": "s1"})
        journal.append(self.ws, {"op": "session", "phase": "close", "key": "s1",
                                 "agents": {"keeper": 3}})
        world = registry.project(self.ws)
        self.assertEqual(world["session"][0]["agents"], {"keeper": 3})

    def test_a_seventh_body_row_stays_exactly_as_it_is(self):
        """338 rows carry neither `phase` nor `key`. They are not guessed into
        shape here — a row that cannot say when it opened says nothing."""
        journal.append(self.ws, {"op": "session", "project": "old"})
        world = registry.project(self.ws)
        self.assertEqual(world["session"], [])
        self.assertEqual([e["op"] for e in world["event"] if e["op"] == "session"],
                         ["session"])

    def test_scars_surface_never_hide(self):
        with open(journal.path(self.ws), "a", encoding="utf-8") as f:
            f.write('{"op": "assert", "torn')
        world = registry.project(self.ws)
        self.assertEqual(len(world["_scars"]), 1)


class TestNothingIsStructurallyEmpty(unittest.TestCase):
    """six of the eight types projected as empty lists for two bodies — not
    because the workshop held none of those things, but because nothing ever
    joined the cards to the record. Build one of each and read them all back;
    this is the check that the empty-list finding cannot come back."""

    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-")
        journal.ensure_genesis(self.ws)
        project.new(self.ws, "geardoor", "the door work")
        with open(project.contract_path(self.ws, "geardoor"), "a", encoding="utf-8") as f:
            f.write("\n## checks\ntrue\n")
        src = os.path.join(tempfile.mkdtemp(prefix="sbx9b-"), "tokens.css")
        with open(src, "w", encoding="utf-8") as f:
            f.write(":root {}\n")
        shelf.save(self.ws, src)
        apps.install(self.ws, make_app(), key())
        journal.append(self.ws, {"op": "session", "phase": "open", "key": "s1",
                                 "project": "geardoor"})
        journal.append(self.ws, {"op": "assert", "cls": "ruling", "project": "geardoor",
                                 "body": "the prefix is per brand", "stratum": "taste"})
        journal.append(self.ws, {"op": "assert", "cls": "note", "project": "geardoor",
                                 "body": "a claim with nothing under it",
                                 "ink": "claimed"})
        check.run(self.ws, "geardoor")

    def test_no_type_is_structurally_empty(self):
        world = registry.project(self.ws)
        for t in registry.TYPES:
            self.assertTrue(world[t], "%s projects as an empty list" % t)

    def test_a_card_and_an_event_are_both_read(self):
        """the journal is the spine and the cards are the flesh: each row says
        whether an event named it and whether a card carries it, because a
        disagreement between the two is the thing doctor has to report."""
        world = registry.project(self.ws)
        build = world["build"][0]
        self.assertTrue(build["carded"] and build["evented"])
        self.assertEqual(len(build["sha256"]), 64)
        self.assertEqual(world["project"][0]["goal"], "the door work")
        self.assertEqual([c["line"] for c in world["check"]], ["true"])


class TestFieldNames(unittest.TestCase):
    """the record's stored field names never change; new fields only.

    A rename is invisible to every test that reads by key — the old name just
    stops appearing, and years of lines quietly stop answering. So the names
    are frozen here as a list, read out of the source rather than typed twice:
    a new field is added to FROZEN in the same commit that mints it, and a
    renamed one fails on the next run.
    """

    # every key the engine writes into a line on the record, as of 9.0.
    FROZEN = frozenset((
        "action", "agents", "body", "build", "checks", "cls", "diff",
        "form", "from_draft", "green", "hand", "hash", "id", "ink", "key",
        "lines", "note", "of", "op", "origin", "path", "phase", "project",
        "proves", "receipt", "redacted", "scrubbed", "sha", "sha256",
        "shown", "staged_at", "stratum", "supersedes", "triggered", "ts",
        "who",
    ))

    # the three calls that put a line on the record, and the local names an
    # organ builds one under before handing it over.
    MINTERS = {("journal", "append"), ("desk", "mint"), ("desk", "submit")}
    HOLDERS = ("event", "record", "staged", "line")

    @classmethod
    def stored_names(cls):
        out = set()
        engine = os.path.join(REPO, "engine")
        for name in sorted(os.listdir(engine)):
            if not name.endswith(".py"):
                continue
            path = os.path.join(engine, name)
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), path)
            for node in ast.walk(tree):
                out |= cls._from_node(node)
        return out

    @classmethod
    def _keys(cls, node):
        return {k.value for k in node.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)}

    @classmethod
    def _from_node(cls, node):
        out = set()
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            fn = node.func
            named = isinstance(fn.value, ast.Name)
            if named and (fn.value.id, fn.attr) in cls.MINTERS:
                for a in node.args:
                    if isinstance(a, ast.Dict):
                        out |= cls._keys(a)
            if (fn.attr == "setdefault" and named and fn.value.id in cls.HOLDERS
                    and node.args and isinstance(node.args[0], ast.Constant)):
                out.add(node.args[0].value)
        if isinstance(node, ast.Assign):
            for t in node.targets:
                if (isinstance(t, ast.Name) and t.id in cls.HOLDERS
                        and isinstance(node.value, ast.Dict)):
                    out |= cls._keys(node.value)
                if (isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                        and t.value.id in cls.HOLDERS
                        and isinstance(t.slice, ast.Constant)
                        and isinstance(t.slice.value, str)):
                    out.add(t.slice.value)
        return out

    def test_field_names_are_frozen(self):
        found = self.stored_names()
        self.assertEqual(sorted(found - self.FROZEN), [],
                         "a new stored field name: add it to FROZEN in this commit")
        self.assertEqual(sorted(self.FROZEN - found), [],
                         "a stored field name stopped being written — a rename "
                         "makes every past line stop answering")

    def test_the_scan_finds_a_planted_name(self):
        """the scan fires: a mint with a new key is seen, so the frozen list
        is a check rather than a comment."""
        src = "journal.append(ws, {'op': 'assert', 'smuggled': 1})\n"
        found = set()
        for node in ast.walk(ast.parse(src)):
            found |= self._from_node(node)
        self.assertIn("smuggled", found)
        self.assertEqual(sorted(found - self.FROZEN), ["smuggled"])


class TestTheIndex(unittest.TestCase):
    """the index is a speed decision, never a truth decision."""

    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9-")
        journal.ensure_genesis(self.ws)
        for i in range(5):
            journal.append(self.ws, {"op": "assert", "cls": "note",
                                     "body": "fact %d" % i, "ink": "claimed"})

    def test_index_is_a_projection_not_a_store(self):
        before = os.path.getsize(journal.path(self.ws))
        first = registry.index(self.ws)
        self.assertEqual(os.path.getsize(journal.path(self.ws)), before,
                         "reading the record changed the record")
        # under both thresholds nothing is kept at all: the counts are computed
        # and thrown away, and doctor prints the thresholds so the day one is
        # crossed is visible rather than guessed at.
        self.assertFalse(os.path.exists(registry.index_path(self.ws)))
        self.assertLess(first["events"], registry.INDEX_AT_EVENTS)
        # a kept copy is deletable: rebuild answers the same thing.
        with open(registry.index_path(self.ws), "w", encoding="utf-8") as f:
            f.write("{}")
        os.remove(registry.index_path(self.ws))
        second = registry.index(self.ws)
        for k in ("events", "by_op", "by_ink", "hand", "scars", "covers"):
            self.assertEqual(first[k], second[k], k)
        self.assertEqual(os.path.getsize(journal.path(self.ws)), before)

    def test_index_is_a_projection_not_a_store_for_every_projection(self):
        """widened: every name `update --rebuild` takes is derived, not kept.

        Delete the file, ask for the rebuild, and the answer is the one that
        was there — that is what makes each of these a projection and the
        journal the only store in the workshop.
        """
        import tempfile as _t
        from engine import notes, onboard, placement, shelf, status
        ws = _t.mkdtemp(prefix="sbx9proj-")
        onboard.run(ws)
        project.new(ws, "geardoor", "the store's data")
        notes.note(ws, "a finding", target_project="geardoor")
        src = os.path.join(ws, "a.txt")
        with open(src, "w", encoding="utf-8") as f:
            f.write("x\n")
        shelf.save(ws, src, note="a build")

        self.assertEqual(registry.PROJECTIONS,
                         ("place", "shelf", "canon", "index"))
        book = placement.book(ws)
        self.assertTrue(book)
        canon = os.path.join(ws, "CANON.md")
        card = os.path.join(ws, shelf.DIRNAME, "a.txt", "BUILD.md")

        for name in registry.PROJECTIONS:
            ok, lines = registry.rebuild(ws, name)
            self.assertTrue(ok, lines)
            self.assertTrue(lines[0].startswith("rewrote"), lines[0])

        # the placement book comes back byte-for-byte from the `place` events
        os.remove(placement._book_path(ws))
        registry.rebuild(ws, "place")
        self.assertEqual(set(placement.book(ws)), set(book))
        # canon and the card come back from the record, and the shelf's own
        # payload is left where it is: a rebuild reads the record, it never
        # invents an event to match a file it found.
        os.remove(canon)
        registry.rebuild(ws, "canon")
        self.assertTrue(os.path.exists(canon))
        self.assertTrue(os.path.exists(card))
        registry.rebuild(ws, "index")
        self.assertTrue(os.path.exists(registry.index_path(ws)))
        os.remove(registry.index_path(ws))
        # and the workshop agrees with the record after every one of them
        self.assertEqual(status.agreement(ws), [])

    def test_a_name_nobody_projects_refuses_and_names_the_four(self):
        ok, lines = registry.rebuild(self.ws, "everything")
        self.assertFalse(ok)
        self.assertIn("no projection named everything", lines[0])
        for name in registry.PROJECTIONS:
            self.assertIn(name, lines[0])

    def test_covers_names_the_prefix_it_folded(self):
        idx = registry.index(self.ws)
        with open(journal.path(self.ws), "rb") as f:
            raw = f.read()
        self.assertEqual(idx["covers"]["bytes"], len(raw))
        self.assertEqual(idx["covers"]["lines"], raw.count(b"\n"))
        journal.append(self.ws, {"op": "assert", "cls": "note", "body": "one more"})
        moved = registry.index(self.ws)
        self.assertNotEqual(moved["covers"]["sha256"], idx["covers"]["sha256"])
        self.assertEqual(moved["events"], idx["events"] + 1)

    def test_the_counts_are_the_record_and_nothing_else(self):
        idx = registry.index(self.ws)
        events, _ = journal.read(self.ws)
        self.assertEqual(idx["events"], len(events))
        self.assertEqual(idx["by_op"]["assert"], 5)
        self.assertEqual(idx["by_ink"]["claimed"], 5)


if __name__ == "__main__":
    unittest.main()
