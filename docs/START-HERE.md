# start here

one sitting, end to end. you finish this page holding four things: a project
on your own disk, the checks it has to pass, a line in the record with your
key on it, and a build on your shelf you can put on the next project.

every step is a command, the exact thing you should see, and what to do when
you see something else. the machine's share of the whole page runs in well
under a second; the rest is your reading speed, so take it at yours.

## 1 · open the workshop

DO
```
~/Sandbox/system/sandbox init
~/Sandbox/system/sandbox setup
```
SEE — `opened your workshop at ~/Sandbox`, then `day 0. nothing on the
record yet.`, a `placed:` line, four lines naming what got wired, and
`ready. nobody's tool.` `setup` answers `one shim written:` with the path,
so `sandbox` alone works from here on.
IF-NOT — *"python3 is required"*: install python 3.9 or newer. want the
workshop somewhere else? `SANDBOX_HOME=/path/you/choose sandbox init`.
re-running init is always safe — it creates what is absent and touches
nothing that lives.

## 2 · the health check

DO
```
sandbox doctor
```
SEE — one line per check, then a legend. the first rows on a fresh workshop:
```
 ok   python 3.9 or newer          3.14
 ok   git on the path
 ok   the record reads             2 event(s)
 ok   no torn lines
 ok   project contracts parse
 ok   provisional acts fresh
 ok   core and workshop agree
 ok   journal and disk agree
 ok   placed files current
 ok   kept files match what ships
 ?    host: strict allowlist       no sandbox key in the settings i can read
```
then the rest of the host rows, the plugin's version, the voice row, and:
```
ok = proved · LOOK = needs you · ? = could not read
```
a `?` is a row doctor could not read — those four are your host's own
settings, and doctor names them rather than guessing at them.
IF-NOT — each failing line names its own fix in the same breath. this is the
one command to run whenever anything later looks wrong.

## 3 · your first project

DO
```
sandbox project new hello "see how this feels"
sandbox project on hello
sandbox status
```
SEE — `project hello is born`, then `hello is on — bare verbs land there`,
then `nothing needs you.` and the project listed `active` with a `*` beside
it.

the folder it made carries two pages. PROJECT.md is yours: the goal, and the
checks a ship rests on. CANON.md is regenerated from the record every time
something lands, so editing it by hand is writing on water.

## 4 · the split that runs everything

DO
```
sandbox note "the first thing worth remembering"
sandbox drafts
```
SEE — the note waits instead of landing:
```
waiting for your approval — approve it: sandbox approve
 1. waiting: [note] the first thing worth remembering
approve them at a real terminal:  sandbox approve
```

now approve it, at a real terminal:

DO
```
sandbox approve
```
SEE — the pile, its fingerprint, the prompt, and the landing:
```
 1. [note] the first thing worth remembering
shown: 3194f609
press k to land this one · any other key cancels
landed 1 (shown 3194f609)
```
`3194f609` fingerprints exactly the lines above it; the landed line carries
the same one, so what you approved and what landed can be compared.
IF-NOT — `landing needs your 'k' at a real terminal — run: sandbox approve`
means exactly that: a pipe, a script, or an agent stands outside this door,
because the key is read from the terminal itself. try
`echo k | sandbox approve` and watch it refuse with exit 1.

this split is the whole design. the machine drafts; you decide what the
record keeps.

## 5 · build a piece of it in a session

`make` keeps the books around a piece of work. it snapshots your files when
you open a session and walks them again when you close it, so what changed
is counted rather than reported.

DO — open Claude Code in the workshop, and give it the intent:
```
cd ~/Sandbox
claude
```
then, in the session: `/make "add a README to this project saying what it is
for"`
SEE — the session runs `sandbox make --open` for you and quotes what it
printed: `session open on hello — add a README to this project saying what
it is for`. it plans, builds, shows you `git diff --stat`, and finishes by
printing the close line for you to run at your own terminal.
IF-NOT — no `claude` on your PATH? open the session your way, and run
`sandbox make --open "add a README to this project saying what it is for"`
at the terminal yourself. it is the same verb the session runs, and it
prints the same line.

now close it, at your terminal:

DO
```
sandbox make --close hello --summary "wrote the README"
```
SEE — the count, the files, the staged summary, and the state of your checks:
```
confirmed — 1 file(s) changed on hello
  README.md
1 summary staged, waiting on your keypress. approve it:  sandbox approve
nothing under ## checks — a ship with nothing under it is a costume; add one line there
```
that count comes from comparing your files before and after. a session that
changed nothing says `attempted — nothing changed on hello (the diff is
empty, and says so)`, whatever its summary claims.
IF-NOT — `no make session open on hello` means the open never happened, or
this close already did; `sandbox status` shows where you stand.

now land the staged summary, the way you landed the note:

DO
```
sandbox approve
```
SEE — the same four lines as step 4, over the summary this time:
```
 1. [make-summary] make: hello: wrote the README
shown: 152c6c8a
press k to land this one · any other key cancels
landed 1 (shown 152c6c8a)
```

## 6 · give it checks, and ship

a ship here means something narrow and honest: your own checks passed.

open `projects/hello/PROJECT.md`. it ships with two headings, in this order —
and a check appended at the end of the file lands under the wrong one:

```
## checks
test -f README.md

## notes
```

DO
```
sandbox ship hello
```
SEE — your `k` on those exact check lines, then the ship:
```
 1. test -f README.md
shown: 4eb89647
press k to land this one · any other key cancels
ratified — your k is on these exact checks (4eb89647)
shipped — 1 check(s) green, on the record (journal:eid-60d16c6069)
```
IF-NOT — `a line under ## notes looks like a check — move it under ##
checks` is the appended-at-the-end mistake, named. `a ship with no
checks is a costume — add a line under PROJECT.md's ## checks` means the
section is still empty. a red check prints the failing
line and its output, and nothing ships until you fix it.

## 7 · open your receipt

this is the part worth doing slowly. everything above wrote to one file:

```
~/Sandbox/.sandbox/journal.jsonl
```

open it in any editor. one json object per line, append-only, plain text —
your note, your ratified checks, your ship, each with its origin and the
consent that landed it. nothing in this system stores a summary of that file;
every count you have seen was computed by reading it.

DO
```
sandbox recall remembering
```
SEE — `[claimed] [human] the first thing worth remembering`, read back out of
that file.
IF-NOT — `nothing landed matches — the record is honest about that.` means
the word is absent from the landed record, which is an answer rather than a
guess.

## 8 · hand the record over

DO
```
sandbox export
```
SEE — three lines: the count and the span, the redaction line, and the path
of the file it wrote:
```
11 line(s), 2026-08-22 → 2026-08-22
not redacted — 0 span(s) would go under --redact
~/Sandbox/record-2026-08-22.md
```
open it. every landed line in time order, each wearing its rung, its origin
and its receipt, and a footer that says what the thing is: `this is a file —
opening it leaves nothing on the record`. `--redact` hides the paths that
name you, `--html` writes the same record as a page, and `--to DIR` puts it
where you want it.

## 9 · leave holding a build

the project is yours; so is the shape of it. put that shape on the shelf and
the next project starts from it.

DO
```
sandbox save ~/Sandbox/projects/hello --note "the shape i want to start from next time"
sandbox builds
```
SEE — `kept: hello (session-kept) — reuse it with: sandbox use hello`, then
the shelf, one line per build with its note under it.

you now hold all four: the project, its checks, a line in the record with
your key on it, and a build you can reuse. `sandbox use NAME` puts one on a
project; `sandbox share NAME --to DIR` stages one for a friend to fetch.

## from here

- `sandbox help` names every verb with what it writes and whether it needs
  your key, and every verb answers `--help`.
- `docs/MANUAL.md` is the page-per-verb reference.
- `docs/OPEN.md` names what this copy still lacks — worth reading once,
  early.
