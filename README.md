# Sandbox OS

a workshop on your own machine, for the things you make with an AI. you
build; the history writes itself; nothing permanent happens without one
keypress from you.

## why this exists

most people cannot afford to experiment. an attempt has to pay right away,
so nobody can afford one that doesn't — and the people who can are the ones
who already have capital, a network, and the operating knowledge. what was
missing was never hustle. it was a place where a failed attempt costs almost
nothing, so small bets can pile up instead of one large bet nobody can
afford to lose. that is what a sandbox is for.

for the first time one person can build that place. an AI will now sit at
your terminal and build with you, on your machine, for the price of a
subscription you may already pay. that changes who gets to try. it also
arrives wearing the old habits: tools you rent on someone else's disk under
terms that change on a tuesday; chats that forget you every morning; agents
that act while you sleep and narrate their success; dashboards with stored
numbers; software that grades its own homework. the capability is new. the
clunky defaults around it are the same ones, and this tool was built to
refuse them out loud.

Sandbox OS was built by one maker who needed it — an inventor who builds
tools that build things, and wanted an AI across the table without handing
over the table. everyone else it serves is an extension of serving that
person well. the belief under it: **you should own the tools you think
with,** the way you own a good knife.

## what it is

one tree of plain python and a `sandbox` command. it opens a folder you
pick, puts your projects in it, and keeps **the record** — an append-only
history of what happened there: what you made, what changed, what held,
what you decided and why. the AI drafts — notes, summaries, findings, code —
and sets each draft aside to wait for you; nothing it drafted is on the
record until you have seen it and pressed one key at a real terminal. a
ship — the moment a project's checks are run and the result goes on the
record — happens only when your own checks pass. the record renders into
pages you can read, hand over, or archive; if you deleted this repo
tomorrow, your work would still open.

you leave every session with a project on your disk, the checks it has to
pass, and a record that remembers — so the next build starts ahead of the
last one.

## the principles, and what each one refuses

these are the convictions the tool is wired from. each one names the habit
it refuses and the part that does the refusing — a thing you can open, never
a promise.

| the principle | what it refuses | where it is wired |
|---|---|---|
| **a machine should not move without a hand on it.** it drafts; you decide. | a machine that writes your history on its own. there is no such mode in the settings, because it was never built a way to. | `sandbox approve` shows the pile, prints its fingerprint, and reads one `k` from the terminal itself; a pipe gets a refusal and an exit code. |
| **a claim wears its proof or it gets cut.** | grading its own homework. the machine may say a thing is so; it may not mark it proven. | every line goes on the record as `[claimed]`; `[receipted]` needs a file behind it, `[checked]` needs a check that ran. `sandbox check` and `sandbox ship` are the only two ways up. |
| **own the tools you think with.** | renting. no account, no sync, no server, no telemetry; the one thing that talks to the internet is the AI itself, on your own plan. | python's own library and nothing else (`grep -rhoE "^import [a-z_]+" engine/*.py`); every verb but `make` runs with the network off, and you are invited to go check. |
| **your work lives in your directory.** | lock-in. plain files in a folder you chose, readable with anything. | `~/Sandbox` (or wherever `SANDBOX_HOME` points) holds everything; this clone is disposable. `sandbox export` hands you the whole record as one file. |
| **the record fills because you worked, not because you filed.** | ceremony. there is no diary to keep up. | `sandbox make --open` and `--close` wrap a piece of building and measure what changed off your files; the close reminds you to ship; your own corrections are pulled out of the session in your words. |
| **trying is free, on purpose.** the gate is strict so the play can be fearless. | fear. a machine that grades everything makes you afraid to try, and a builder afraid to try is a builder the tool has failed. | `sandbox play` opens a room where nothing is counted, cited, or shipped. |
| **amplify the maker; never automate them away.** copilot, never autopilot. | the tool becoming the product. the only score is things made and shipped by you, never how big the tool's own memory got. | the Claude Code session is the face: one plugin carries the hooks, six crew briefs, three skills and the voice; the `sandbox` verbs are the hands. |

## the first minute

a real first sitting, captured on a fresh workshop and pasted whole. where it
prints `~`, your own home directory prints in full:

<!-- sitting:begin (re-run by engine/tests/test_readme_sitting.py) -->
```
$ ~/Sandbox/system/sandbox init
opened your workshop at ~/Sandbox
day 0. nothing on the record yet.
placed: ~/Sandbox/CLAUDE.md
deny floor: 1 rule(s) on the record's directory
transcript rule: the account of a session is denied to edits
plugin: sandbox-os 9.0.1 — read from this core's own tree, each session
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

## get it running

macOS/Linux, python 3.9+, a terminal, and Claude Code installed — only `make`
costs money, and it runs on the Claude plan you already pay for.

```
git clone https://github.com/Sandbox-cmd/SandboxOS-core ~/Sandbox/system
~/Sandbox/system/sandbox init     # your workshop at ~/Sandbox — SANDBOX_HOME moves it
~/Sandbox/system/sandbox setup    # writes a `sandbox` shim into ~/.local/bin
~/Sandbox/system/sandbox doctor   # the health check names anything missing, with its fix
```

then open a Claude Code session in `~/Sandbox` — the plugin loads from this
tree, the charter is already in front of the model, and `/make` opens a
building session. at the terminal, `sandbox help` names every verb with what
it writes and whether it needs your key. `docs/START-HERE.md` walks one sitting end to end and
leaves you holding a build of your own; `docs/MANUAL.md` has a page per verb;
`docs/OPEN.md` says what this copy still lacks.

## a session, end to end

- **arrive** — `sandbox resume` shows what waited for you; one `k` puts it
  on the record.
- **look** — `sandbox status` says what needs you, oldest first.
- **work** — `sandbox make --open "intent"` around a piece of building, and
  `sandbox make --close NAME --summary "…"` when it is done; a red check
  turns the close back.
- **capture** — `sandbox note "..."` the moment a finding surfaces. it
  waits for your key, and says so.
- **remember** — `sandbox recall QUERY`. when the record holds nothing that
  matches, it says so instead of guessing.
- **finish** — put your checks in PROJECT.md, then `sandbox ship`.
- **keep and swap** — `sandbox save PATH` puts a reusable build on your
  shelf; `sandbox share NAME --to DIR` packs one for a friend, and their key
  is the gate on their side.
- **hand it over** — `sandbox export` writes the whole record to one file.

## open any of it

every claim above names a command that opens it. run these in the workshop
that first sitting leaves behind, in any order. nothing here asks you to take
its word — that would be the habit this page is against.

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
refuses every time, and the sentence lives at `engine/gate.py`, line 35.
read it there before you believe it here.

## what stays out, on purpose

- **a dashboard.** the session you are sitting in is the face; a second one
  would be a second thing to keep in sync, so the status line and the
  refusals carry the character instead.
- **a second host.** one host (Claude Code), wired deeply, beats four wired
  thinly; the choice is written in `docs/OPEN.md` rather than left as an absence.
- **Arabic, and every other script this terminal renders badly.** the pages
  stay English until a terminal here can draw the rest.
- **Windows.** macOS and Linux are the floor; the guard, the shim and the
  paths are POSIX all the way down.
- **the cloud.** nothing runs on a schedule somewhere else, holds an account,
  or reaches a server, because a record kept on someone's machine is theirs.
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

`verify` proves the copy changed, and says which files. for the stronger
check, hand it the release key:

```
export SANDBOX_MINISIGN_PUBKEY=RWSSaKTVM7ywEE8f/jL16NcRhOFR1sAtIOd2hAD/ziMRscYAlaGxw+9j
sandbox verify
```

the same key is printed in every release's notes since 8.1.1. if this file
and the notes ever disagree, trust neither and ask. you install by cloning and update by
pulling, so `main` only ever moves to a state that verifies against that key:
work happens on branches, and main moves once per release.

## your workshop is yours

`~/Sandbox`, or wherever `SANDBOX_HOME` points, holds your projects, your
builds, your apps, and the record. back it up by copying the folder. this
clone is disposable; that folder is the thing you own.

when something looks wrong: `sandbox doctor`, then `sandbox drafts`. every
refusal in here names the door you can walk through instead.

## license

FSL-1.1-Apache-2.0 — free for everything except competing with the software,
and it converts to Apache 2.0 two years after each release.
