# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the one door. A routing table, no logic — every verb is one organ.

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


def home_line():
    """the second line of `version`: which tree is running, and its state.
    One home is a ruling (2026-07-23, 2026-08-22); this line is how a person
    sees whether the shim and the work agree."""
    import subprocess
    home = os.path.expanduser("~")
    shown = ROOT
    if shown.startswith(home + os.sep):
        shown = "~" + shown[len(home):]
    parts = []
    try:
        run = lambda *a: subprocess.run(["git", "-C", ROOT] + list(a), capture_output=True, text=True, timeout=5)
        b = run("rev-parse", "--abbrev-ref", "HEAD")
        if b.returncode == 0:
            parts.append(b.stdout.strip())
            st = run("status", "--porcelain")
            parts.append("clean" if st.returncode == 0 and not st.stdout.strip() else "dirty")
            t = run("describe", "--tags", "--abbrev=0")
            if t.returncode == 0 and t.stdout.strip():
                parts.append(t.stdout.strip())
    except (OSError, subprocess.SubprocessError):
        pass
    if not parts:
        parts.append("no git")
    return "from %s — %s" % (shown, ", ".join(parts))


def main(argv):
    from . import verbs
    verb = argv[0] if argv else "help"
    if verb.startswith("--"):
        verb = verb.lstrip("-")
    return verbs.dispatch(workshop(), verb, argv[1:])
