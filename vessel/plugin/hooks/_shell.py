# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""what the three record-facing hooks share: the tree, the verb, the project.

A hook writes nothing durable itself. Everything it wants kept goes through a
`sandbox` verb, so the record is written by engine code from an event (law 11)
and the landing still waits for the owner's key. The core it shells is the one
the plugin ships beside — two directories up from this file — so a session can
never drive a version of the tool the plugin was not built against.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.environ.get("CLAUDE_PLUGIN_ROOT") or os.path.dirname(HERE)
CORE = os.path.dirname(os.path.dirname(os.path.abspath(PLUGIN_ROOT)))
STATE = ".sandbox"


def event():
    """the hook's own JSON, or {} when nothing readable arrived."""
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def workshop(ev=None):
    home = os.environ.get("SANDBOX_HOME", "").strip()
    if home:
        return os.path.abspath(os.path.expanduser(home))
    return os.path.join(os.path.expanduser("~"), "Sandbox")


def sandbox(args, ws=None):
    """run one verb. Returns (exit code, stdout). Never raises at the caller."""
    exe = os.path.join(CORE, "sandbox")
    if not os.path.exists(exe):
        return 127, ""
    env = dict(os.environ)
    if ws:
        env["SANDBOX_HOME"] = ws
    try:
        run = subprocess.run([exe] + list(args), capture_output=True, text=True,
                             timeout=20, env=env, cwd=ws or None)
    except (OSError, subprocess.SubprocessError):
        return 127, ""
    return run.returncode, run.stdout


def project_of(path, ws):
    """projects/<name>/… → name, else None."""
    if not path:
        return None
    base = os.path.join(os.path.abspath(ws), "projects") + os.sep
    here = os.path.abspath(path)
    if not here.startswith(base):
        return None
    return here[len(base):].split(os.sep)[0] or None


def staged_bodies(ws):
    """what already waits on the owner's key, read and never written."""
    p = os.path.join(ws, STATE, "staging.jsonl")
    out = []
    try:
        with open(p, "rb") as f:
            for raw in f:
                line = raw.decode("utf-8", "replace").strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line).get("body") or "")
                except ValueError:
                    continue
    except OSError:
        return out
    return out


def transcript(ev):
    """[event] from the session's transcript file, torn lines skipped."""
    p = ev.get("transcript_path") or ""
    out = []
    try:
        with open(os.path.expanduser(p), "rb") as f:
            for raw in f:
                line = raw.decode("utf-8", "replace").strip()
                if not line:
                    continue
                try:
                    out.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return out
    return out
