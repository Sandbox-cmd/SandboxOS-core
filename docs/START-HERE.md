# start here

one sitting, end to end. you finish this page holding three things: a project
on your own disk, the checks it has to pass, and a line in the record with
your key on it — openable in a text editor, still true in a year.

every step is a command, the exact thing you should see, and what to do when
you see something else. the machine's share of the whole page runs in well
under a second; the rest is your reading speed, so take it at yours.

## 1 · open the workshop

DO
```
./sandbox init
```
SEE — `opened your workshop at ~/Sandbox`, then `day 0. nothing on the
record yet.`, then a `placed:` line for each file it laid down.
IF-NOT — *"python3 is required"*: install python 3.9 or newer. want the
workshop somewhere else? `SANDBOX_HOME=/path/you/choose ./sandbox init`.
re-running init is always safe — it creates what is absent and touches
nothing that lives.

## 2 · the health check

DO
```
sandbox doctor
```
SEE — a short table, every line `ok`, starting with `python >= 3.9`.
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
then the project listed `active` with a `*` beside it.

the folder it made carries two pages. PROJECT.md is yours: the goal, and the
checks a ship rests on. CANON.md is not — it is regenerated from the record
every time something lands, so editing it by hand is writing on water.

## 4 · the split that runs everything

DO
```
sandbox note "the first thing worth remembering"
sandbox drafts
```
SEE — the note does not land. it answers `waiting for your approval`, and
`drafts` shows it sitting there.

now approve it, at a real terminal:
```
sandbox approve
```
SEE — it lands with your key.
IF-NOT — `landing needs your 'k' at a real terminal` means exactly that: a
pipe, a script, or an agent cannot approve for you. that is not a setting.
try `echo k | sandbox approve` and watch it refuse.

this split is the whole design. the machine drafts; you decide what the
record keeps.

## 5 · build something with the AI

this is the one step that costs money, and not to us — `make` shells out to
the `claude` command, so it wants a Claude subscription. **every other step
on this page runs with the network off.** if you do not have one, skip to 6;
nothing below depends on it.

DO
```
sandbox make "add a README to this project saying what it is for"
```
SEE — the session opens, the builder runs, and on close you get
`confirmed — N file(s) changed on hello` followed by the files themselves.
that count is computed by comparing your files before and after. it is not
the model's summary of what it did.

## 6 · give it checks, and ship

a ship here means something narrow and honest: your own checks passed.

open `projects/hello/PROJECT.md` and put one command per line under
`## checks` — anything that exits 0 when things are well:

```
## checks
echo the thing works
```

DO
```
sandbox ship hello
```
SEE — the first ship asks for your `k` on those exact check lines:
`these checks are new or changed since your last k`. press it, and you get
`shipped — 1 check(s) green, on the record`, with a journal id.
IF-NOT — `nothing to ship on — PROJECT.md has no checks` means the section is
still empty. `the checks are red — no ship` prints the failing line and its
output; nothing ships until you fix it.

## 7 · open your receipt

this is the part worth doing slowly. everything above wrote to one file:

```
~/Sandbox/.sandbox/journal.jsonl
```

open it in any editor. one json object per line, append-only, plain text —
your note, your ratified checks, your ship, each with its origin and the
consent that landed it. nothing in this system stores a summary of that file;
every count you have seen was computed by reading it.

that file is the thing you actually own. the clone you installed from is
disposable — back up the workshop folder and you have kept all of it.

DO
```
sandbox recall remembering
```
SEE — your note, read back out of that file. when the record has nothing it
says so rather than guessing.

## 8 · from here

- `sandbox page` renders your whole workshop to `page.html` and asks the
  network for nothing.
- `sandbox save PATH --note "why"` keeps a reusable build on your shelf;
  `sandbox builds` lists them and `sandbox use NAME` puts one on a project.
- `sandbox help` names every verb with what it writes and whether it needs
  your key.
- `docs/MANUAL.md` is the page-per-verb reference. `docs/OPEN.md` says what
  this copy does not do yet — worth reading once, early.
