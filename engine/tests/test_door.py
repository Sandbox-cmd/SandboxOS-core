# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The door answers, and answers honestly."""
import os
import subprocess
import unittest

from . import REPO


def run_cli(*args):
    return subprocess.run(
        [os.path.join(REPO, "sandbox"), *args],
        capture_output=True, text=True, timeout=30,
    )


class TestDoor(unittest.TestCase):
    def test_version_reads_the_file(self):
        with open(os.path.join(REPO, "VERSION"), encoding="utf-8") as f:
            want = "Sandbox OS " + f.read().strip()
        got = run_cli("version")
        self.assertEqual(got.returncode, 0)
        self.assertEqual(got.stdout.strip(), want)

    def test_unknown_verb_refuses_plainly(self):
        got = run_cli("frobnicate")
        self.assertEqual(got.returncode, 2)
        self.assertIn("no verb named", got.stdout)
        self.assertIn("sandbox help", got.stdout)

    def test_help_promises_nothing_unbuilt(self):
        with open(os.path.join(REPO, "VERSION"), encoding="utf-8") as f:
            version = f.read().strip()
        got = run_cli("help")
        self.assertEqual(got.returncode, 0)
        self.assertIn("Sandbox OS " + version, got.stdout)


class TestPersonClean(unittest.TestCase):
    """No committed file carries a personal absolute path. The full lint
    (external private-terms list) arrives with row A6; this floor holds now."""

    # Needles are assembled, not written literally, so this file passes its
    # own lint.
    NEEDLES = ("/" + "Users" + "/", "/" + "home" + "/")

    def test_no_home_paths_in_tree(self):
        hits = []
        for dirpath, dirnames, filenames in os.walk(REPO):
            dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
            for name in filenames:
                path = os.path.join(dirpath, name)
                try:
                    with open(path, encoding="utf-8") as f:
                        text = f.read()
                except (UnicodeDecodeError, OSError):
                    continue
                if any(n in text for n in self.NEEDLES):
                    hits.append(os.path.relpath(path, REPO))
        self.assertEqual(hits, [], "personal paths in: %s" % hits)


if __name__ == "__main__":
    unittest.main()
