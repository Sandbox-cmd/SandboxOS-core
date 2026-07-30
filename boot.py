# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""Boot: put THIS copy's root at the head of sys.path, then hand to the CLI.

A fork always runs its own engine — never a stale installed copy.
"""
import os
import sys

if __name__ == "__main__":
    root = os.path.dirname(os.path.abspath(__file__))
    if sys.path[0] != root:
        sys.path.insert(0, root)
    from engine.cli import main
    sys.exit(main(sys.argv[1:]))
