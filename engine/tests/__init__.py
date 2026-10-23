# SPDX-License-Identifier: FSL-1.1-Apache-2.0
"""the suite's harness: scratch workshops only, never a living one.

Grows with the bands. Every test drives the real `./sandbox` door where it
can; a green suite nobody ran is a costume.

The key is read from the terminal itself now, so a test says which of the two
it is standing in: `pressing("k")` hands the rig's character to the gate and
every consent minted under it wears `hand: synthetic`; `no_terminal()` is the
pipe — nothing can answer, whatever the machine running the suite is sitting
at.
"""
import contextlib
import os
import sys
from unittest import mock

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _stand_at_a_pipe():
    """the suite reads the same wherever it is started: a pipe, never a hand.

    a note's origin follows stdin's isatty and doctor's colour follows
    stdout's, so the suite was green from a pipe and seven tests red at the
    owner's keyboard (2026-10-23, 9.0.3's tree included). stdin becomes
    /dev/null at the descriptor, so every child a test starts inherits it
    too, and NO_COLOR keeps the rows plain. a test that wants a terminal
    already says so: it mocks isatty, presses the rig's key, or opens its
    own pty. this also means no test can read a key the owner meant for
    something else.
    """
    if os.isatty(0):
        fd = os.open(os.devnull, os.O_RDONLY)
        os.dup2(fd, 0)
        os.close(fd)
        sys.stdin = open(0, closefd=False)
    os.environ["NO_COLOR"] = "1"


_stand_at_a_pipe()


@contextlib.contextmanager
def pressing(char="k"):
    """the rig's one key, for the length of the block."""
    from engine import gate
    old = os.environ.get(gate.TEST_KEY_ENV)
    os.environ[gate.TEST_KEY_ENV] = char
    try:
        yield
    finally:
        if old is None:
            os.environ.pop(gate.TEST_KEY_ENV, None)
        else:
            os.environ[gate.TEST_KEY_ENV] = old


@contextlib.contextmanager
def no_terminal():
    """no hand at the door — the pipe, the script, the agent."""
    with mock.patch("engine.gate.at_a_terminal", return_value=False):
        yield


@contextlib.contextmanager
def elsewhere_home():
    """an empty home for the length of the block.

    doctor reads the host's own settings and its style copies; a suite that
    read the machine it happens to run on would be green on one laptop and
    red on the next, so the tests that call doctor stand in a home with
    nothing in it and every host receipt reads `?`.
    """
    import tempfile
    d = tempfile.mkdtemp(prefix="sbx9home-")
    old = os.environ.get("HOME")
    os.environ["HOME"] = d
    try:
        yield d
    finally:
        if old is None:
            os.environ.pop("HOME", None)
        else:
            os.environ["HOME"] = old


def quiet(*_line):
    """the `out` a test hands a verb that prints as it goes.

    The lines a verb shows are pinned where they are read; a test that is
    after something else keeps its own output clean.
    """


def key(shown=None):
    """one consent, minted through the one door the engine uses."""
    from engine import gate
    with pressing("k"):
        return gate.mint_consent(shown=shown)
