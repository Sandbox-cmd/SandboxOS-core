# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""The one door. A routing table, no logic — every verb is one organ.

Verbs arrive band by band (backlog: band A skeleton first). Until an organ
exists, the door says so plainly rather than pretending.
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def version_line():
    with open(os.path.join(ROOT, "VERSION"), encoding="utf-8") as f:
        return "Sandbox OS " + f.read().strip()


def main(argv):
    verb = argv[0] if argv else "help"
    if verb in ("version", "--version"):
        print(version_line())
        return 0
    if verb in ("help", "--help"):
        print(version_line())
        print("a maker's operating system for your own machine.")
        print()
        print("this copy is early — the engine is being built band by band.")
        print("verbs land with receipts; none is promised before its check is green.")
        return 0
    print("no verb named %r yet — this copy is early. try: sandbox help" % verb)
    return 2
