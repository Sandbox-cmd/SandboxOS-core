# Sandbox OS

a terminal workshop for the things you build with an AI. the machine drafts;
your keypress decides what the record keeps. you leave a session with a
project on your disk, the checks it has to pass, and an append-only record of
what actually happened.

this is a real first sitting, captured on a fresh workshop and pasted whole.
where it prints `~`, your own home directory prints in full:

<!-- sitting:begin (re-run by engine/tests/test_readme_sitting.py) -->
```
$ ~/Sandbox/system/sandbox init
opened your workshop at ~/Sandbox
day 0. nothing on the record yet.
placed: ~/Sandbox/CLAUDE.md
deny floor: 1 rule(s) on the record's directory
transcript rule: the account of a session is denied to edits
plugin: sandbox-os 9.0.0 — read from this core's own tree, each session
voice: across-the-desk is the session style unless you pick another
read-back: the wiring took
ready. nobody's tool.
$ sandbox project new hello "see how this feels"
project hello is born
$ sandbox project on hello
hello is on — bare verbs land there
$ sandbox note "the first thing worth remembering"
waiting for your approval — approve it: sandbox approve
$ sandbox approve
 1. [note] the first thing worth remembering
shown: 3194f609
press k to land this one · any other key cancels
landed 1 (shown 3194f609)
$ sandbox recall remembering
[claimed] [human] the first thing worth remembering
```
<!-- sitting:end -->

macOS/Linux, python 3.9+, a terminal, and Claude Code installed — only `make`
costs money, and it runs on the Claude plan you already pay for.

every claim below names a command that opens it, and the line that command
prints. run them in the workshop that sitting leaves behind, in any order.
nothing here asks you to take its word.

## open any of it

| the claim | open it | the line you get |
|---|---|---|
| every verb says what it does, what it writes, and whether it needs your key, before you type it | `sandbox approve --help` | `gate: needs your k at a real terminal` |
| nothing lands that you were not shown | `sandbox approve`, at a terminal | `shown: 3194f609` above the prompt, then `landed 1 (shown 3194f609)` |
| a pipe cannot approve anything | `echo k \| sandbox approve` | `landing needs your 'k' at a real terminal — run: sandbox approve`, exit 1 |
| a ship happens only when your own checks pass | `sandbox ship hello`, with `## checks` empty | `a ship with no checks is a costume — add a line under PROJECT.md's ## checks`, exit 1 |
| what got built is measured off your files, and the model's account of it is beside the measurement rather than in place of it | `sandbox make --close hello --summary "rewrote the world"`, after a session that touched no file | `attempted — nothing changed on hello (the diff is empty, and says so)` |
| every count is computed the moment it is shown | `cat ~/Sandbox/projects/hello/CANON.md` | `_3 landed facts — computed, not stored._` |
| the engine stands on python's own library and reaches no network | `grep -rhoE "^import [a-z_]+" engine/*.py \| sort -u` | fourteen names, `argparse` through `time`, every one of them stdlib |

> ### NOTHING LANDS THAT YOU WERE NOT SHOWN.

this is a claim about claims: the pile prints before the key, the digest of
that exact pile prints with it, and the landing line carries the same digest
back so the two can be compared. events the engine receipts as it works —
a project born, a session opened — are records of what happened, and they
land as they happen. `sandbox ship` prints its digest on every run, first
ship or fortieth.

the refusal under it is the one a script meets: `echo k | sandbox approve`
refuses every time, and the sentence lives at `engine/desk.py`, line 160.
read it there before you believe it here.

## get it running

```
git clone https://github.com/Sandbox-cmd/SandboxOS-core ~/Sandbox/system
~/Sandbox/system/sandbox init     # your workshop at ~/Sandbox — SANDBOX_HOME moves it
~/Sandbox/system/sandbox setup    # writes a `sandbox` shim into ~/.local/bin
~/Sandbox/system/sandbox doctor   # the health check names anything missing, with its fix
```

then the first project:

```
sandbox project new hello "try this thing out"
sandbox status
```

`docs/START-HERE.md` walks one sitting end to end and finishes with a build
of your own on the shelf. `docs/MANUAL.md` carries a page per verb, and every
verb answers `--help` at your terminal. `docs/OPEN.md` names what this copy
still lacks — read it before trusting anything here you have not run.

## a session, end to end

- **arrive** — `sandbox resume`. one `k` approves whatever waited for you.
- **look** — `sandbox status`.
- **work** — `sandbox project on NAME`, then `sandbox make --open "intent"`
  around a piece of building, and `sandbox make --close NAME --summary "…"`
  when it is done. inside a Claude Code session in `~/Sandbox`, `/make` opens
  the same session and hands you the close line to run yourself.
- **capture** — `sandbox note "..."` the moment a finding surfaces. it waits
  on your key; what lands is what you were shown.
- **remember** — `sandbox recall QUERY`. when the record holds nothing that
  matches, it says so instead of guessing.
- **finish** — put your checks in PROJECT.md, then `sandbox ship`.
- **keep and swap** — `sandbox save PATH` puts a reusable build on your
  shelf, `sandbox share NAME --to DIR` stages one for a friend, and your key
  is the gate on both ends.
- **hand it over** — `sandbox export` writes the whole record to one file you
  can read, mail, or archive.

`sandbox help` names all of them, each with what it touches.

## what stays out, on purpose

- **the room.** there is one face here, and it is the session you are already
  sitting in; a second one would be a second place to keep in sync, so the
  status line and the refusals carry the character instead.
- **a second host.** gemini, opencode and cline see none of this. one host,
  wired deeply, beats four wired thinly, and the choice is written down in
  `docs/OPEN.md` rather than left as an absence.
- **Arabic, and every other script the terminal here renders badly.** the
  pages stay English until a terminal on this machine can draw the rest.
- **Windows.** macOS and Linux are the floor, because the guard, the shim and
  the paths are POSIX all the way down.
- **the cloud.** nothing here runs on a schedule somewhere else, holds an
  account, or reaches a server, because a record kept on someone's machine is
  theirs to read.
- **grading its own work.** anything on the record wears `[claimed]` until
  something else checks it; `[receipted]` and `[checked]` are earned by a file
  or an exit code.
- **overwriting what you edited.** updates skip your changed files and name
  them; `sandbox reset PATH` returns one to pristine when you ask.

## what it runs under

`law/` holds fifteen laws, one file each — count them with `ls law | wc -l`.
`soul/` holds the six pages this workshop's character is written on:
`ls soul | wc -l`. they travel inside the signed manifest with the code, so
touching one moves the seal.

law 03 is named for *amana* — the everyday Arabic word for a thing handed to
you to keep and give back whole. as a rule it reads: the machine holds your
workshop, and only your key moves what is durable in it.

```
python3 -m unittest discover -s engine/tests -t .   # the suite, stdlib only
sandbox verify                                      # sha256 against the manifest
```

`verify` proves the copy changed, and says which files. it names no culprit —
for the stronger check, hand it the release key:

```
export SANDBOX_MINISIGN_PUBKEY=RWSSaKTVM7ywEE8f/jL16NcRhOFR1sAtIOd2hAD/ziMRscYAlaGxw+9j
sandbox verify
```

the same key is printed in every release's notes. if this file and the notes
ever disagree, trust neither and ask.

you install by cloning and you update by pulling, which means you track
`main`. so main only ever moves to a state that verifies against that key:
work happens on branches, and main moves once per release. that rule exists
because this page told you to pull.

## your workshop is yours

`~/Sandbox`, or wherever `SANDBOX_HOME` points, holds your projects, your
builds, your apps, and the record. back it up by copying the folder. this
clone is disposable; that folder is the thing you own.

when something looks wrong: `sandbox doctor`, then `sandbox drafts`. every
refusal in here names the door you can walk through instead.

## license

FSL-1.1-Apache-2.0 — free for everything except competing with the software,
and it converts to Apache 2.0 two years after each release.
