# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""declaration parity: the table and the declarations never drift apart."""
import ast
import os
import unittest

from engine import verbs

from . import REPO


class TestDeclarationParity(unittest.TestCase):
    def test_every_verb_declared_every_declaration_implemented(self):
        self.assertEqual(sorted(verbs.TABLE), sorted(verbs.DECLARATIONS))

    def test_declarations_are_wellformed(self):
        for name, d in verbs.DECLARATIONS.items():
            self.assertIn(d["gate"], verbs.GATES, name)
            self.assertTrue(d["emits"] is None or d["emits"] in verbs.OPS, name)
            for w in d["writes"]:
                self.assertIn(w, verbs.SCOPES, name)
            self.assertTrue(d["blurb"], name)

    def test_every_blurb_fits_the_one_row_it_gets(self):
        """the blurb is the field a person reads before they type. It is a
        fragment, so lowercase and no period; twelve words, so help's row
        stays inside a terminal; and none of the engine's own scope nouns,
        which is the vocabulary the blurb exists to replace."""
        for name, d in verbs.DECLARATIONS.items():
            b = d["blurb"]
            self.assertTrue(b[0].islower(), "%s: %r" % (name, b))
            self.assertFalse(b.endswith("."), "%s: %r" % (name, b))
            self.assertLessEqual(len(b.split()), 12, "%s: %r" % (name, b))
            for token in ("state", "settings"):
                self.assertNotIn(" %s" % token, " " + b,
                                 "%s says %r — that is verbs.py's word" % (name, token))

    def test_the_lint_fires(self):
        """parity case: an undeclared verb is CAUGHT, not absorbed."""
        try:
            verbs.TABLE["smuggled"] = lambda ws, argv: 0
            self.assertNotEqual(sorted(verbs.TABLE), sorted(verbs.DECLARATIONS))
        finally:
            del verbs.TABLE["smuggled"]

    def test_declaration_builder_refuses_nonsense(self):
        with self.assertRaises(AssertionError):
            verbs.declaration(gate="vibes")
        with self.assertRaises(AssertionError):
            verbs.declaration(emits="celebration")
        with self.assertRaises(AssertionError):
            verbs.declaration(writes=("wherever",))
        # A verb cannot ship nameless: no blurb, no door.
        with self.assertRaises(AssertionError):
            verbs.declaration()
        with self.assertRaises(AssertionError):
            verbs.declaration(blurb="Lists what the shelf keeps")
        with self.assertRaises(AssertionError):
            verbs.declaration(blurb="list what the shelf keeps.")
        with self.assertRaises(AssertionError):
            verbs.declaration(blurb=" ".join(["word"] * 13))

    def test_the_marketplace_source_is_a_kind_the_host_reads(self):
        """the R14 entry names this core's tree as the marketplace, and the
        marketplace file there names the plugin by a relative path.

        The host takes github, git, url, file, directory or settings for a
        marketplace — `command` is a source a marketplace gives one of its
        PLUGINS, and the entry that carried it here never loaded. This pins
        the kind, so the wiring cannot go back to a word the host drops.
        """
        import json
        from engine import onboard
        source = onboard.marketplace_source()
        self.assertIn(source["source"],
                      ("github", "git", "url", "file", "directory", "settings"))
        root = source["path"]
        p = os.path.join(root, ".claude-plugin", "marketplace.json")
        with open(p, encoding="utf-8") as f:
            market = json.load(f)
        self.assertEqual(market["name"], onboard.MARKETPLACE)
        entry = [x for x in market["plugins"] if x["name"] == onboard.PLUGIN_NAME]
        self.assertEqual(len(entry), 1, market["plugins"])
        self.assertTrue(os.path.isdir(os.path.join(root, entry[0]["source"])),
                        entry[0]["source"])

    def test_state_scope_reserved(self):
        """only init (placing the vessel beside the record) may claim the
        record's directory; every other verb is fenced out."""
        for name, d in verbs.DECLARATIONS.items():
            if name in ("init", "update", "reset", "import"):  # placement + succession
                continue
            self.assertNotIn("state", d["writes"],
                             "%s claims the record's directory" % name)


class TestEveryOpIsMinted(unittest.TestCase):
    """declared, never produced — the scar this closes.

    Three names sat in OPS for two bodies with nothing behind them, so the
    registry read `session` off an empty list and `invalidate` and `halt`
    described moves no verb could make. A name in OPS now names something the
    engine does, or it is parked here with the reason it stays.
    """

    # halt is reserved: 16 rows in the seventh body still say it, so removing
    # the name would make those rows unreadable, and 9.0 has no organ that
    # halts anything. It is parked, not forgotten.
    PARKED = {"halt": "the seventh body's rows still use it; no organ halts yet"}

    @staticmethod
    def minted():
        """every op an engine dict literal puts on the record."""
        out = {}
        engine = os.path.join(REPO, "engine")
        for name in sorted(os.listdir(engine)):
            if not name.endswith(".py"):
                continue
            path = os.path.join(engine, name)
            with open(path, encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    for k, v in zip(node.keys, node.values):
                        if (isinstance(k, ast.Constant) and k.value == "op"
                                and isinstance(v, ast.Constant)
                                and isinstance(v.value, str)):
                            out.setdefault(v.value, set()).add(name)
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "setdefault" and len(node.args) == 2
                        and isinstance(node.args[0], ast.Constant)
                        and node.args[0].value == "op"
                        and isinstance(node.args[1], ast.Constant)):
                    out.setdefault(node.args[1].value, set()).add(name)
        return out

    def test_every_declared_op_has_a_call_site_or_a_reason(self):
        minted = self.minted()
        for op in verbs.OPS:
            if op in self.PARKED:
                self.assertNotIn(op, minted,
                                 "%s is parked and something mints it — "
                                 "unpark it here" % op)
                self.assertTrue(self.PARKED[op].strip(), op)
                continue
            self.assertIn(op, minted, "%s is declared and nothing mints it" % op)

    def test_nothing_mints_an_op_the_table_never_declared(self):
        for op, where in self.minted().items():
            self.assertIn(op, verbs.OPS, "%s mints %r, which OPS never names"
                          % (sorted(where), op))


if __name__ == "__main__":
    unittest.main()
