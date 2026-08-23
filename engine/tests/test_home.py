# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""one home: the tree a person clones is the tree that runs, and a fresh
machine gets there with one block. These pins hold the 2026-08-22 ruling."""
import os
import shutil
import subprocess
import tempfile
import unittest

from engine import integrity
from engine.cli import ROOT


class TestOneHome(unittest.TestCase):
    def test_root_is_this_copy(self):
        self.assertEqual(integrity.root(), ROOT)
        self.assertTrue(os.path.exists(os.path.join(integrity.root(), "sandbox")))

    def test_install_block_from_an_empty_machine(self):
        """git clone <repo> <home>/system && <home>/system/sandbox init —
        the README's one block, run against this tree as the remote."""
        tmp = tempfile.mkdtemp(prefix="sbx-home-")
        try:
            home = os.path.join(tmp, "Sandbox")
            system = os.path.join(home, "system")
            os.makedirs(home)
            r = subprocess.run(["git", "clone", "-q", ROOT, system], capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            env = dict(os.environ, HOME=tmp, SANDBOX_HOME=home, SANDBOX_SHIM_DIR=os.path.join(tmp, "bin"))
            r = subprocess.run([os.path.join(system, "sandbox"), "init"], capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertIn("ready. nobody's tool.", r.stdout)
            r = subprocess.run([os.path.join(system, "sandbox"), "version"], capture_output=True, text=True, env=env)
            lines = r.stdout.strip().splitlines()
            self.assertEqual(len(lines), 2)
            self.assertIn("system", lines[1])
            r = subprocess.run([os.path.join(system, "sandbox"), "doctor"], capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stdout)
            r = subprocess.run([os.path.join(system, "sandbox"), "setup"], capture_output=True, text=True, env=env)
            self.assertEqual(r.returncode, 0, r.stdout)
            with open(os.path.join(tmp, "bin", "sandbox"), encoding="utf-8") as f:
                self.assertIn(os.path.join(system, "sandbox"), f.read())
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
