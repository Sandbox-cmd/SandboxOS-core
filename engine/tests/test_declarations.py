# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Declaration parity: the table and the declarations never drift apart."""
import unittest

from engine import verbs


class TestDeclarationParity(unittest.TestCase):
    def test_every_verb_declared_every_declaration_implemented(self):
        self.assertEqual(sorted(verbs.TABLE), sorted(verbs.DECLARATIONS))

    def test_declarations_are_wellformed(self):
        for name, d in verbs.DECLARATIONS.items():
            self.assertIn(d["gate"], verbs.GATES, name)
            self.assertTrue(d["emits"] is None or d["emits"] in verbs.OPS, name)
            for w in d["writes"]:
                self.assertIn(w, verbs.SCOPES, name)

    def test_the_lint_fires(self):
        """Parity case: an undeclared verb is CAUGHT, not absorbed."""
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

    def test_state_scope_reserved_for_desk_family(self):
        """No band-A verb writes the record's own directory."""
        for name, d in verbs.DECLARATIONS.items():
            self.assertNotIn("state", d["writes"],
                             "%s claims the record's directory" % name)


if __name__ == "__main__":
    unittest.main()
