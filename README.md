# Sandbox OS

a workshop on your own machine, for the things you make with an AI. it keeps the
record of what happened there, and nothing reaches that record until you press a
key.

## why this exists

most people cannot afford to experiment. an attempt has to pay right away, so
nobody can afford one that doesn't. the people who can are already carrying
capital, a network and the operating knowledge: how to structure the entity,
price the work, spec the build, find the maker, get paid, stay legal. that last
one is the gate. the gates are made of information, and information is most of
what a failed attempt costs you.

hustle was not the missing piece. what was missing was a place where a failed
attempt costs almost nothing, so small survivable bets can compound. the shape on
offer everywhere else is one large bet nobody can afford to lose. that is what a
sandbox is for.

for the first time one person can build that place. an AI will sit at your
terminal and build with you, on your own machine, for the price of a
subscription you may already pay. that changes who gets to try. it also arrives,
of course, wearing the old habits. tools you rent on someone else's disk, under
terms that change on a tuesday. chats that forget you every morning. agents that
act while you sleep and then narrate their success. dashboards with stored
numbers. software that grades its own homework. the capability is a year old and
the defaults around it are decades old, so this tool was built to refuse them out
loud.

Sandbox OS was built by one maker who needed it: an inventor who builds tools
that build things, and wanted an AI across the table without handing over the
table. everyone else it serves is an extension of serving that person well. the
belief under it is one sentence. **you should own the tools you think with,** the
way you own a good knife. rented thinking ends when the terms change.

## what it is

one tree of plain python and a `sandbox` command. it opens a folder you pick and
puts your projects in it. what it keeps there is **the record**, an append-only
history of what happened: what you made, what changed, what held, and what you
decided and why. the AI drafts into it (notes, summaries, findings, code) and
sets each draft aside to wait for you. a draft becomes a line on the record once
you have seen it and pressed one key at a real terminal. a ship is the moment a
project's own checks run and the result goes on the record, and it happens only
on green. the record renders into pages you can read or hand over, and if you
deleted this repo tomorrow, your work would still open and your next build would
start ahead of the last one.

## the principles, and what each one refuses

these are the convictions the tool is wired from. each row names a habit and the
part of the machine that refuses it; everything in the third column opens.

| the principle | the habit it refuses | the part that refuses it |
|---|---|---|
| **a machine should not move without a hand on it.** | a machine that writes your history while you sleep. there is no such mode in the settings, because it was never built a way to have one. | `sandbox approve` shows the pile, prints its fingerprint, and reads one `k` from the terminal itself; a pipe gets a refusal and an exit code. |
| **a claim wears its proof or it gets cut.** the machine may say a thing is so. marking it proven takes a check that ran. | grading its own homework. | every line goes on the record as `[claimed]`; `[receipted]` needs a file behind it, `[checked]` needs a check that ran. `sandbox check` and `sandbox ship` are the only two ways up. |
| **own the tools you think with.** | renting. no account, no sync, no server, no telemetry; the one thing that talks to the internet is the AI itself, on your own plan. | python's own library and nothing else (`grep -rhoE "^import [a-z_]+" engine/*.py`); every verb but `make` runs with the network off, and you are invited to go check. |
| **your work lives in your directory.** | lock-in. plain files in a folder you chose, readable with anything you like. | `~/Sandbox` (or wherever `SANDBOX_HOME` points) holds everything; this clone is disposable. `sandbox export` hands you the whole record as one file. |
| **the record fills because you worked.** | ceremony. there is no diary to keep up and nothing to file. | `sandbox make --open` and `--close` wrap a piece of building and measure what changed off your files; the close reminds you to ship; your own corrections come back out of the session in your words. |
| **trying is free, on purpose.** the gate is strict so the play can be fearless. | fear. a machine that grades everything makes you afraid to try, and a builder afraid to try is a builder the tool has failed. | `sandbox play` opens a room where nothing is counted or shipped. |
| **amplify the maker.** | the tool becoming the product. the day this place becomes the thing you show people, it has failed. | the Claude Code session is the face: one plugin carries the hooks, six crew briefs, three skills and the voice; the `sandbox` verbs are the hands. |

## the first minute

a real first sitting, captured on a fresh workshop and pasted whole. a test
re-runs every line of it against this build, so it goes red the day it stops
being true. where it prints `~`, your own home directory prints in full.

<!-- sitting:begin (re-run by engine/tests/test_readme_sitting.py) -->
```
$ ~/Sandbox/system/sandbox init
opened your workshop at ~/Sandbox
day 0. nothing on the record yet.
placed: ~/Sandbox/CLAUDE.md
deny floor: 1 rule(s) on the record's directory
transcript rule: the account of a session is denied to edits
plugin: sandbox-os 9.0.5 — read from this core's own tree, each session
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

macOS/Linux, python 3.9+, a terminal and Claude Code installed. only `make`
costs money, and it runs on the Claude plan you already pay for.

```
git clone https://github.com/Sandbox-cmd/SandboxOS-core ~/Sandbox/system
~/Sandbox/system/sandbox init     # your workshop at ~/Sandbox — SANDBOX_HOME moves it
~/Sandbox/system/sandbox setup    # writes a `sandbox` shim into ~/.local/bin
~/Sandbox/system/sandbox doctor   # the health check names anything missing, with its fix
```

then open a Claude Code session in `~/Sandbox`. the plugin loads from this tree
with the charter already in front of the model, and `/make` opens a building
session. at the terminal, `sandbox help` names every verb with what it writes and
whether it needs your key. `docs/START-HERE.md` walks one sitting end to end and
leaves you holding a build of your own; `docs/MANUAL.md` has a page per verb, and
`docs/OPEN.md` says what this copy still lacks.

## a session, end to end

`sandbox resume` opens the day with what waited for you and one `k` for the part
of it that needs your key, and `sandbox status` follows it with what needs you,
oldest first. wrap real building in `sandbox make --open "intent"` and close it
with `sandbox make --close NAME --summary "what happened"`. the close measures
the diff off your files, so a summary that outruns the diff gets marked as
attempted. a red check turns the close back.

`sandbox note "..."` the moment a finding surfaces; it waits for your key and says
so on the same line. `sandbox recall QUERY` asks the record before you decide
anything twice, and when nothing there matches it says so and guesses nothing.
put your checks under `## checks` in PROJECT.md, then `sandbox ship`. `sandbox
export` writes the whole record to one file you can hand to a person. `sandbox
save PATH` keeps a reusable build on your shelf, and `sandbox share NAME --to DIR`
packs one for a friend, whose own key is the gate on their side.

the share half is, to be fair, the thinnest claim on this page. so far only the
maker has ever pulled from a shelf, and `docs/OPEN.md` carries it as an open debt
until a stranger's fetch lands.

## open any of it

every claim above names a command that opens it. run them in the workshop that
first sitting leaves behind, in any order. nothing here asks you to take its word,
which would be the habit this whole page is against.

| the claim | open it | the line you get |
|---|---|---|
| every verb says what it does, what it writes, and whether it needs your key, before you type it | `sandbox approve --help` | `gate: needs your k at a real terminal` |
| nothing lands that you were not shown | `sandbox approve`, at a terminal | `shown: 3194f609` above the prompt, then `landed 1 (shown 3194f609)` |
| a pipe cannot approve anything | `echo k \| sandbox approve` | `landing needs your 'k' at a real terminal — run: sandbox approve`, exit 1 |
| a ship happens only when your own checks pass | `sandbox ship hello`, with `## checks` empty | `a ship with no checks is a costume — add a line under PROJECT.md's ## checks`, exit 1 |
| what got built is measured off your files, and the model's account of it sits beside that measurement | `sandbox make --close hello --summary "rewrote the world"`, after a session that touched no file | `attempted — nothing changed on hello (the diff is empty, and says so)` |
| every count is computed the moment it is shown | `cat ~/Sandbox/projects/hello/CANON.md` | `_3 landed facts — computed, not stored._` |
| the engine stands on python's own library and reaches no network | `grep -rhoE "^import [a-z_]+" engine/*.py \| sort -u` | fifteen names, `argparse` through `time`, every one of them stdlib |

> ### NOTHING LANDS THAT YOU WERE NOT SHOWN.

that is a claim about claims. the pile prints before the key, the digest of that
exact pile prints with it, and the landing line carries the same digest back, so
you can hold the two side by side. events the engine receipts as it works (a
project born, a session opened) are records of something that already happened,
so they go on the record as they happen, while `sandbox ship` prints its digest
on every run, first ship or fortieth.

the refusal under all of it is the one a script meets: `echo k | sandbox approve`
refuses every time, and the sentence it prints lives at `engine/gate.py`, line 35.
go read it there before you believe it here.

## what stays out, on purpose

- a dashboard. the session you are sitting in is the face, so the status line and
  the refusals carry the character and there is no second surface to keep true.
- a second host. gemini, opencode and cline see none of this, because one host
  wired deeply beats four wired thinly; `docs/OPEN.md` is where that trade gets
  re-argued the day it stops paying.
- Arabic, and every other script this terminal renders badly. the pages stay
  English until a terminal here can draw the rest.
- Windows. macOS and Linux are the floor, and the guard, the shim and the paths
  are POSIX all the way down.
- the cloud. nothing here runs on a schedule somewhere else, holds an account,
  or reaches a server, because a record kept on someone else's machine is theirs.
- overwriting what you edited. an update skips your changed files and names them;
  `sandbox reset PATH` puts one back to pristine when you ask.

if what you want is a tool that works while you sleep and hands you a summary
over coffee, this is the wrong one. no flag in it turns it into the right one.

## what it runs under

`law/` holds fifteen laws, one file each; count them with `ls law | wc -l`, and
`soul/` holds the six pages this workshop's character is written on: `ls soul | wc -l`.
both travel inside the signed manifest with the code, so touching one moves the
seal.

law 03 is named for *amana*, the everyday Arabic word for a thing handed to you
to keep and give back whole. as a rule it reads: the machine holds your
workshop, and only your key moves what is durable in it.

```
python3 -m unittest discover -s engine/tests -t .   # the suite, stdlib only
sandbox verify                                      # sha256 against the manifest
```

`verify` says whether this copy changed, and names the files that did. for the
stronger check, hand it the release key:

```
export SANDBOX_MINISIGN_PUBKEY=RWSSaKTVM7ywEE8f/jL16NcRhOFR1sAtIOd2hAD/ziMRscYAlaGxw+9j
sandbox verify
```

the same key is printed in the notes of every release since 8.1.1, and if this
file and the notes ever disagree, trust neither and ask. you install by cloning
and update by pulling, so `main` only ever moves to a state that verifies against
that key: work happens on branches, and main moves once per release.

## your workshop is yours

`~/Sandbox`, or wherever `SANDBOX_HOME` points, holds your projects, your builds,
your apps, and the record. back it up by copying the folder. this clone is
disposable; that folder is the thing you own. when something looks wrong, run
`sandbox doctor` and then `sandbox drafts`. every refusal in here names a door
you can walk through instead.

## license

FSL-1.1-Apache-2.0: free for everything except competing with the software,
and it converts to Apache 2.0 two years after each release.
