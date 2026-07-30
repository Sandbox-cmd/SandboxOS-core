# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The one door. A routing table, no logic — every verb is one organ.

Dispatch flows through the verb table (engine/verbs.py), where each verb
carries its declaration. The door itself only resolves the workshop and
hands off.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOME_ENV = "SANDBOX_HOME"


def workshop():
    home = os.environ.get(HOME_ENV, "").strip()
    if home:
        return os.path.abspath(os.path.expanduser(home))
    return os.path.join(os.path.expanduser("~"), "Sandbox")


def version_line():
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
        return "Sandbox OS " + f.read().strip()


def main(argv):
    from . import verbs
    verb = argv[0] if argv else "help"
    if verb.startswith("--"):
        verb = verb.lstrip("-")
    return verbs.dispatch(workshop(), verb, argv[1:])
