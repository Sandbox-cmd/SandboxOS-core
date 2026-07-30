# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Person-clean: the scrub bites, the export never carries history."""
import os
import subprocess
import tempfile
import unittest

from engine import clean


def make_tree():
    src = tempfile.mkdtemp(prefix="sbx8c-")
    with open(os.path.join(src, "good.md"), "w") as f:
        f.write("plain public words\n")
    return src


class TestScan(unittest.TestCase):
    def test_floor_needle_hits(self):
        src = make_tree()
        with open(os.path.join(src, "leak.md"), "w") as f:
            f.write("see /" + "Users" + "/someone/secret\n")
        report = clean.scan(src)
        self.assertFalse(report["clean"])
        self.assertEqual(report["hits"][0][0], "leak.md")

    def test_private_terms_from_outside_the_tree(self):
        src = make_tree()
        with open(os.path.join(src, "bio.md"), "w") as f:
            f.write("the owner's company files\n")
        terms = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False)
        terms.write("# private\ncompany files\n")
        terms.close()
        os.environ[clean.TERMS_ENV] = terms.name
        try:
            report = clean.scan(src)
            self.assertTrue(report["terms_loaded"])
            self.assertFalse(report["clean"])
        finally:
            del os.environ[clean.TERMS_ENV]

    def test_absent_terms_said_honestly(self):
        os.environ.pop(clean.TERMS_ENV, None)
        report = clean.scan(make_tree())
        self.assertFalse(report["terms_loaded"])  # floor only, and it says so
        self.assertTrue(report["clean"])

    def test_denied_and_unscannable_named(self):
        src = make_tree()
        with open(os.path.join(src, "creds.env"), "w") as f:
            f.write("SECRET=1\n")
        with open(os.path.join(src, "data.bin"), "wb") as f:
            f.write(b"\xff\xfe\x00\x01binary")
        report = clean.scan(src)
        self.assertIn("creds.env", report["denied"])
        self.assertIn("data.bin", report["unscannable"])
        self.assertFalse(report["clean"])  # denied files fail the verdict


class TestFreshExport(unittest.TestCase):
    def test_git_never_rides(self):
        src = make_tree()
        subprocess.run(["git", "init", "--quiet", src], check=True)
        subprocess.run(["git", "-C", src, "add", "-A"], check=True)
        dest = tempfile.mkdtemp(prefix="sbx8e-")
        report = clean.fresh_export(src, dest)
        self.assertTrue(report["clean"])
        self.assertFalse(os.path.exists(os.path.join(dest, ".git")))
        self.assertTrue(os.path.exists(os.path.join(dest, "good.md")))

    def test_stale_destination_refused(self):
        src = make_tree()
        dest = tempfile.mkdtemp(prefix="sbx8e-")
        with open(os.path.join(dest, "stale.md"), "w") as f:
            f.write("old export\n")
        with self.assertRaises(ValueError):
            clean.fresh_export(src, dest)

    def test_exported_tree_is_what_gets_scanned(self):
        src = make_tree()
        with open(os.path.join(src, "leak.md"), "w") as f:
            f.write("/" + "home" + "/someone\n")
        dest = tempfile.mkdtemp(prefix="sbx8e-")
        report = clean.fresh_export(src, dest)
        self.assertFalse(report["clean"])


if __name__ == "__main__":
    unittest.main()
