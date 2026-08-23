# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""doctor: three blocks, three verdicts, and a run that leaves no trace.

The checks decide the exit code, `ready:` never does, and `?` never does.
The last test here is the one the whole part rests on: doctor and the status
line are looking, and looking is not making (law 12), so the workshop is
hashed whole before and after and the two hashes are held equal.
"""
import hashlib
import json
import os
import tempfile
import time
import unittest
from unittest import mock

from engine import face, journal, onboard, project, registry, shelf, status

from . import elsewhere_home


def days_ago(n):
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() - n * 86400))


def plant_open_make(ws, name, intent, when):
    p = os.path.join(ws, journal.STATE_DIR, "make-open-%s.json" % name)
    with open(p, "w", encoding="utf-8") as f:
        json.dump({"intent": intent, "root": ws, "listing": {}, "opened": when}, f)
    return p


def plant_card(ws, name):
    """a build on the shelf that no `build-kept` event ever named."""
    d = os.path.join(ws, shelf.DIRNAME, name)
    os.makedirs(d)
    with open(os.path.join(d, "payload.txt"), "w", encoding="utf-8") as f:
        f.write("x\n")
    with open(os.path.join(d, "BUILD.md"), "w", encoding="utf-8") as f:
        f.write("# %s\nkept: %s\nfrom: /nowhere\nsha256: 0\norigin: session-kept\n"
                "\n## used\n" % (name, journal.now()))
    return d


def hash_tree(root):
    """every file under the workshop, by path and content."""
    out = {}
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d != "__pycache__"]
        for n in sorted(filenames):
            p = os.path.join(dirpath, n)
            try:
                with open(p, "rb") as f:
                    out[os.path.relpath(p, root)] = hashlib.sha256(f.read()).hexdigest()
            except OSError:
                out[os.path.relpath(p, root)] = "unreadable"
    return out


def find(lines, needle):
    return [l for l in lines if needle in l]


class DoctorCase(unittest.TestCase):
    def setUp(self):
        self.ws = tempfile.mkdtemp(prefix="sbx9dr-")
        onboard.run(self.ws)

    def doctor(self):
        """doctor in an empty home: the host receipts read `?` on every machine."""
        with elsewhere_home():
            return status.doctor(self.ws)


class TestTheOpenSeam(DoctorCase):
    def test_a_fresh_workshop_is_green(self):
        ok, lines = self.doctor()
        self.assertTrue(ok, "\n".join(lines))

    def test_an_open_make_past_a_week_is_the_look_line(self):
        """rule R16: named at any age, LOOK past 7 days.

        A#9: and green — R24 gives the exit to the repair rows, and a make
        left open is work in progress rather than a workshop out of
        agreement with itself. A three-week-old make used to keep doctor
        red, which is how an owner learns to stop reading the exit code.
        """
        plant_open_make(self.ws, "geardoor", "ADJUDICATED1 — a withdrawal",
                        days_ago(21))
        ok, lines = self.doctor()
        self.assertTrue(ok, "\n".join(lines))
        row = find(lines, "open makes")[0]
        self.assertTrue(row.strip().startswith("LOOK"), row)
        self.assertIn("21 d", row)
        self.assertIn("sandbox make geardoor --close", row)

    def test_an_open_make_under_a_week_is_named_and_green(self):
        plant_open_make(self.ws, "geardoor", "a fresh pass", days_ago(2))
        ok, lines = self.doctor()
        self.assertTrue(ok, "\n".join(lines))
        row = find(lines, "open makes")[0]
        self.assertIn("2 d", row)


class TestJournalVersusDisk(DoctorCase):
    def test_a_card_with_no_event_names_the_side_that_is_ahead(self):
        plant_card(self.ws, "tuner")
        ok, lines = self.doctor()
        self.assertFalse(ok)
        row = find(lines, "repair required")[0]
        self.assertIn("the disk is ahead", row)
        self.assertIn("tuner", row)
        self.assertIn("sandbox update --rebuild shelf", row)
        self.assertNotIn("sandbox repair", row)

    def test_a_struck_keep_leaves_the_shelf_reading(self):
        """9.0.1: a build-kept line the owner struck with `invalidate` stays on
        the record and stops counting — the shelf is read as the strike left
        it, so a mis-named save is repairable without a card."""
        kept = journal.append(self.ws, {"op": "assert", "cls": "build-kept",
                                        "origin": "machine", "build": "stray",
                                        "body": "kept: stray", "ink": "receipted",
                                        "receipt": "nowhere"})
        ok, lines = self.doctor()
        self.assertFalse(ok)
        self.assertIn("stray", find(lines, "the record is ahead")[0])
        struck_id = kept["id"] if isinstance(kept, dict) and kept.get("id") else \
            json.loads(open(journal.path(self.ws), encoding="utf-8").read()
                       .strip().splitlines()[-1])["id"]
        journal.append(self.ws, {"op": "invalidate", "of": struck_id,
                                 "origin": "human", "body": "a mis-named save"})
        ok, lines = self.doctor()
        self.assertEqual(find(lines, "stray"), [], "\n".join(lines))
        self.assertTrue(ok, "\n".join(lines))
        world = registry.project(self.ws)
        self.assertNotIn("stray", [b["name"] for b in world.get("build", [])])

    def test_a_forgotten_placement_book_names_the_record(self):
        os.remove(os.path.join(self.ws, journal.STATE_DIR, "place.json"))
        ok, lines = self.doctor()
        self.assertFalse(ok)
        row = find(lines, "repair required")[0]
        self.assertIn("the record is ahead", row)
        self.assertIn("sandbox update --rebuild place", row)

    def test_the_rebuild_puts_the_book_back_and_doctor_goes_quiet(self):
        os.remove(os.path.join(self.ws, journal.STATE_DIR, "place.json"))
        ok, lines = registry.rebuild(self.ws, "place")
        self.assertTrue(ok, lines)
        self.assertIn("rewrote the placement book", lines[0])
        ok, lines = self.doctor()
        self.assertTrue(ok, "\n".join(lines))
        self.assertEqual(find(lines, "repair required"), [])


class TestTheHostReceipts(DoctorCase):
    def test_a_planted_settings_file_is_proved_and_named(self):
        d = tempfile.mkdtemp(prefix="sbx9set-")
        p = os.path.join(d, "settings.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"sandbox": {"network": {"strictAllowlist": True}},
                       "permissions": {"deny": ["Edit(//a/b/.claude/projects/**)"]},
                       "worktree": {"baseRef": "fresh"},
                       "disableAllHooks": False,
                       "extraKnownMarketplaces": {
                           onboard.MARKETPLACE: {
                               "source": onboard.marketplace_source()}},
                       "enabledPlugins": {onboard.plugin_key(): True}}, f)
        with open(p, encoding="utf-8") as f:
            sources = [("~/.claude/settings.json", json.load(f))]
        rows = status.settings_receipts(self.ws, sources)
        self.assertEqual([v for _l, v, _d in rows], [face.OK] * 6)
        for _label, _verdict, detail in rows:
            self.assertIn("~/.claude/settings.json", detail)

    def test_the_plugin_wiring_is_two_receipts_and_each_names_its_door(self):
        """a workshop whose plugin quietly stopped loading says so (B#10).

        The marketplace entry and the `enabledPlugins` line are what decide
        whether a session loads this core at all; both are read back off the
        file init wrote them to, and an absent one is a LOOK with the verb
        that writes it — never the exit code, because they are host rows.
        """
        rows = status.settings_receipts(
            self.ws, [("~/.claude/settings.json", {"disableAllHooks": False})])
        by = {l: (v, d) for l, v, d in rows}
        self.assertEqual(by["host: plugin marketplace"][0], face.LOOK)
        self.assertIn("sandbox init", by["host: plugin marketplace"][1])
        self.assertEqual(by["host: plugin on"][0], face.LOOK)
        self.assertIn("sandbox init", by["host: plugin on"][1])

        good = {"extraKnownMarketplaces": {
                    onboard.MARKETPLACE: {"source": onboard.marketplace_source()}},
                "enabledPlugins": {onboard.plugin_key(): True}}
        rows = status.settings_receipts(self.ws, [("~/.claude/settings.json", good)])
        by = {l: (v, d) for l, v, d in rows}
        self.assertEqual(by["host: plugin marketplace"][0], face.OK)
        self.assertIn("directory", by["host: plugin marketplace"][1])
        self.assertNotIn(os.path.expanduser("~"),
                         by["host: plugin marketplace"][1])
        self.assertEqual(by["host: plugin on"][0], face.OK)

        rows = status.settings_receipts(self.ws, [("~/.claude/settings.json", None)])
        by = {l: (v, d) for l, v, d in rows}
        self.assertEqual(by["host: plugin marketplace"][0], face.GAP)
        self.assertEqual(by["host: plugin on"][0], face.GAP)

    def test_an_orphaned_plugin_cache_is_not_a_row_doctor_can_fix(self):
        """the doctor row prescribes `sandbox update`, and update walks no
        cache the host has orphaned — so the copy is not a row at all (B#5)."""
        with elsewhere_home() as home:
            cache = os.path.join(home, ".claude", "plugins", "cache",
                                 "gone", "sandbox-os", "9.0.0")
            styles = os.path.join(cache, "output-styles")
            os.makedirs(styles)
            with open(os.path.join(styles, status.STYLE_FILE), "w",
                      encoding="utf-8") as f:
                f.write("an older copy\n")
            # 1: no known_marketplaces.json at all — every cache counts.
            self.assertTrue([w for w, _s in status.style_copies(self.ws)
                             if "gone" in w])
            # 2: the host still holds the marketplace — it counts.
            km = os.path.join(home, ".claude", "plugins",
                              "known_marketplaces.json")
            with open(km, "w", encoding="utf-8") as f:
                json.dump({"gone": {}}, f)
            self.assertTrue([w for w, _s in status.style_copies(self.ws)
                             if "gone" in w])
            # 3: the marketplace is off the host's list — it is not a row.
            with open(km, "w", encoding="utf-8") as f:
                json.dump({"other": {}}, f)
            self.assertEqual([w for w, _s in status.style_copies(self.ws)
                              if "gone" in w], [])
            # 4: back on the list, but marked orphaned — still not a row.
            with open(km, "w", encoding="utf-8") as f:
                json.dump({"gone": {}}, f)
            with open(os.path.join(cache, status.ORPHAN_MARK), "w") as f:
                f.write("2026-08-23\n")
            self.assertEqual([w for w, _s in status.style_copies(self.ws)
                              if "gone" in w], [])
            ok, lines = status.doctor(self.ws)
        self.assertTrue(ok, "\n".join(lines))
        self.assertEqual(find(lines, "sandbox update --rebuild gone"), [])

    def test_could_not_prove_is_never_ok(self):
        """a setting nobody could read is a gap, never a green fence."""
        rows = status.settings_receipts(self.ws, [("~/.claude/settings.json", {})])
        self.assertIn(face.GAP, [v for _l, v, _d in rows])
        self.assertNotIn(face.OK, [v for _l, v, _d in rows])

    def test_the_transcript_rule_this_core_ships_turns_the_row_green(self):
        """the row read `?` while there was no rule to hold a host to. init
        writes one now, so the same reader that reported the gap reports the
        fence — one reader, two answers, and the second is earned."""
        self.assertIsNotNone(status.transcript_rule())
        self.assertEqual(status.transcript_rule(), onboard.TRANSCRIPT_DENY)
        rows = status.settings_receipts(
            self.ws, [("~/.claude/settings.json",
                       {"permissions": {"deny": [onboard.TRANSCRIPT_DENY]}})])
        row = [r for r in rows if r[0] == "host: transcript rule"][0]
        self.assertEqual(row[1], face.OK)
        self.assertIn(onboard.TRANSCRIPT_DENY, row[2])

    def test_a_host_with_no_transcript_rule_is_the_look(self):
        rows = status.settings_receipts(
            self.ws, [("~/.claude/settings.json", {"permissions": {"deny": []}})])
        row = [r for r in rows if r[0] == "host: transcript rule"][0]
        self.assertEqual(row[1], face.LOOK)
        self.assertIn("sandbox init", row[2])

    def test_an_initialised_workshop_proves_its_own_transcript_rule(self):
        """the workshop's settings are one of the three files the one reader
        reads, so init's own write is what doctor proves."""
        rows = status.settings_receipts(self.ws)
        row = [r for r in rows if r[0] == "host: transcript rule"][0]
        self.assertEqual(row[1], face.OK)

    def test_a_shadowed_skill_is_a_ready_row_and_never_the_exit(self):
        """rule R13: the plugin ships the three skills and the owner's copies
        retire — by his hand. doctor names them and stays green."""
        with elsewhere_home() as home:
            os.makedirs(os.path.join(home, ".claude", "skills", "sandbox-workshop"))
            ok, lines = status.doctor(self.ws)
        self.assertTrue(ok, "\n".join(lines))
        row = find(lines, "shadowed by the plugin")[0]
        self.assertIn("sandbox-workshop", row)
        self.assertIn("rm -r ~/.claude/skills/sandbox-workshop", row)
        self.assertIn("ready:", lines)

    def test_hooks_turned_off_is_the_look(self):
        rows = status.settings_receipts(
            self.ws, [("~/.claude/settings.json", {"disableAllHooks": True})])
        row = [r for r in rows if r[0] == "host: hooks on"][0]
        self.assertEqual(row[1], face.LOOK)

    def test_a_host_look_never_changes_the_exit(self):
        """rule R24 (owner, 2026-08-23): the repair block decides the exit; a
        LOOK on a host row is named and the run stays green."""
        rows = status.settings_receipts(
            self.ws, [("~/.claude/settings.json", {"disableAllHooks": True})])
        self.assertTrue(any(r[1] == face.LOOK and r[0].startswith("host:")
                            for r in rows))
        ok = all(v is not False and v != face.LOOK
                 for l, v, _n in rows if v is not None and not l.startswith("host:"))
        self.assertTrue(ok)
        with elsewhere_home() as home:
            os.makedirs(os.path.join(home, ".claude"))
            with open(os.path.join(home, ".claude", "settings.json"), "w") as f:
                f.write('{"disableAllHooks": true}')
            ok, lines = status.doctor(self.ws)
        self.assertTrue(find(lines, "host: hooks on"), "\n".join(lines))
        self.assertTrue(ok, "\n".join(lines))

    def test_the_gap_never_changes_the_exit(self):
        ok, lines = self.doctor()
        self.assertTrue(ok)
        self.assertTrue(find(lines, "?"), "\n".join(lines))
        self.assertTrue(find(lines, "could not read:"))

    def test_every_endpoint_is_listed_and_none_is_opened(self):
        sources = [("~/.claude/settings.json", {
            "hooks": {"Stop": [{"hooks": [{"command":
                       "curl http://127.0.0.1:8765/hook/claude"}]}]},
            "permissions": {"allow": ["WebFetch(domain:docs.anthropic.com)"]},
            "mcpServers": {"x": {"url": "https://mcp.example.com/sse"}}})]
        addrs = [a for _w, a in status.endpoints(self.ws, sources)]
        self.assertIn("docs.anthropic.com", addrs)
        self.assertIn("https://mcp.example.com/sse", addrs)
        self.assertTrue(any(a.startswith("127.0.0.1") for a in addrs), addrs)

    def test_no_socket_is_opened_on_any_doctor_path(self):
        """law 7, proved rather than promised."""
        import socket

        def refuse(*a, **kw):
            raise AssertionError("doctor opened a socket")

        with mock.patch.object(socket, "socket", refuse), \
                mock.patch.object(socket, "create_connection", refuse):
            ok, lines = self.doctor()
        self.assertTrue(ok, "\n".join(lines))
        self.assertTrue(find(lines, "endpoints"))


class TestThePins(DoctorCase):
    def test_the_plugin_pin_names_the_drift_and_refuses_nothing(self):
        with mock.patch.object(status, "plugin_version", return_value="8.0.0"):
            ok, lines = self.doctor()
        row = find(lines, "plugin version")[0]
        self.assertIn("8.0.0", row)
        self.assertIn("sandbox update", row)
        self.assertFalse(ok)   # named in the report; the hook still never blocks

    def test_the_plugin_version_is_never_a_refusal_to_answer(self):
        with mock.patch.object(status, "plugin_version", return_value=None):
            _ok, lines = self.doctor()
        row = find(lines, "plugin version")[0]
        self.assertTrue(row.strip().startswith("?"), row)

    def test_the_voice_row_reads_the_placed_files(self):
        ok, lines = self.doctor()
        self.assertTrue(ok, "\n".join(lines))
        self.assertTrue(find(lines, "voice"))

    def test_a_planted_cut_word_turns_the_voice_row(self):
        # the word is taken from the soul's own table rather than typed here:
        # a fixture that types a cut word is a page carrying one.
        from engine import voicelint
        word = voicelint.forbidden_phrases()[0].phrase
        with open(os.path.join(self.ws, "CLAUDE.md"), "a", encoding="utf-8") as f:
            f.write("\nthis pass was %s.\n" % word)
        ok, lines = self.doctor()
        self.assertFalse(ok)
        row = find(lines, "voice")[0]
        self.assertIn("CLAUDE.md", row)

    def test_a_stale_style_copy_is_named(self):
        with elsewhere_home() as home:
            d = os.path.join(home, ".claude", "output-styles")
            os.makedirs(d)
            with open(os.path.join(d, status.STYLE_FILE), "w", encoding="utf-8") as f:
                f.write("an older copy\n")
            ok, lines = status.doctor(self.ws)
        self.assertFalse(ok)
        row = find(lines, "voice")[0]
        self.assertIn("output-styles", row)
        self.assertIn("sandbox update", row)


class TestWhatIsReady(DoctorCase):
    def test_ready_rows_never_touch_the_exit(self):
        ok, lines = self.doctor()
        self.assertTrue(ok, "\n".join(lines))
        self.assertIn("ready:", lines)
        self.assertTrue(find(lines, "export: never run"))

    def test_a_build_that_never_left_the_machine_is_an_opportunity(self):
        root = os.path.join(self.ws, "a.txt")
        with open(root, "w", encoding="utf-8") as f:
            f.write("x\n")
        shelf.save(self.ws, root, note="a build")
        ok, lines = self.doctor()
        self.assertTrue(ok, "\n".join(lines))
        row = find(lines, "never left this machine")[0]
        self.assertIn("sandbox share a.txt", row)


    def test_a_green_project_with_no_ship_after_it_is_r6_s_nag(self):
        project.new(self.ws, "geardoor", "the store's data")
        close = {"op": "make", "phase": "close", "project": "geardoor",
                 "origin": "machine", "body": "a pass"}
        journal.append(self.ws, close)
        # the close is stamped now; doctor nags only past a week, so the row
        # is absent today and present when the same close is 8 days old. the
        # event's own stamp is what moves — a second call to now() could land
        # on the next second and replace nothing (a flake seen at the release).
        _ok, lines = self.doctor()
        self.assertEqual(find(lines, "no ship after them"), [])
        p = journal.path(self.ws)
        with open(p, encoding="utf-8") as f:
            text = f.read()
        stamped = json.loads(text.strip().splitlines()[-1])["ts"]
        with open(p, "w", encoding="utf-8") as f:
            f.write(text.replace(stamped, days_ago(8)))
        ok, lines = self.doctor()
        self.assertTrue(ok, "\n".join(lines))
        row = find(lines, "no ship after them")[0]
        self.assertIn("sandbox ship geardoor", row)

    def test_a_crew_seat_is_counted_from_the_session_close(self):
        journal.append(self.ws, {"op": "session", "phase": "close",
                                 "key": "s1", "origin": "machine",
                                 "agents": {"checker": 2, "voicer": 1}})
        ok, lines = self.doctor()
        self.assertTrue(ok, "\n".join(lines))
        row = find(lines, "crew:")[0]
        self.assertIn("2 seat(s) on the record", row)
        self.assertIn("30 days", row)


class TestTheFooter(DoctorCase):
    def test_the_legend_prints_once(self):
        _ok, lines = self.doctor()
        legend = find(lines, "ok = proved")
        self.assertEqual(len(legend), 1)
        self.assertEqual(legend[0], "ok = proved · LOOK = needs you · ? = could not read")

    def test_the_index_footer_names_its_threshold(self):
        _ok, lines = self.doctor()
        row = find(lines, "index: journal")[0]
        self.assertIn("of 50,000", row)
        self.assertIn("folded in", row)
        self.assertIn(" ms", row)


class TestDoctorWritesNothing(DoctorCase):
    def test_doctor_writes_nothing(self):
        """looking is not making: the workshop is byte-for-byte what it was.

        The index is the one thing that could have been written here — doctor
        asks registry for the fold without the keeping, so a workshop under
        the threshold gains no file and a workshop over it gains none either.
        """
        project.new(self.ws, "geardoor", "the store's data")
        plant_open_make(self.ws, "geardoor", "a pass", days_ago(21))
        plant_card(self.ws, "tuner")
        before = hash_tree(self.ws)
        with elsewhere_home():
            status.doctor(self.ws)
            status.line(self.ws)
            status.status(self.ws)
            status.needs(self.ws)
        after = hash_tree(self.ws)
        self.assertEqual(before, after)
        self.assertFalse(os.path.exists(registry.index_path(self.ws)),
                         "doctor kept an index under the threshold")


if __name__ == "__main__":
    unittest.main()
