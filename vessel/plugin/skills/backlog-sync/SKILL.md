---
name: backlog-sync
description: Reconcile a pull-based backlog.md against the landed record so it stops drifting — mark finished work done, fold in rulings and findings, add new work (each with a job row + a runnable check), cut dead items with a reason, and refresh the "as of" date stamp. stage every change; the owner's keypress is what lands it. Use whenever a backlog.md may be behind the record: right after rulings land, right after a `sandbox make --close`, when new work gets picked up, when `sandbox doctor` reports "backlog ... N landed notes past its 'as of' — re-sync", or when someone says the backlog is stale / out of date / needs a re-sync / "sync the backlog" / "living backlog". Works on any project whose backlog.md carries an "as of <date>" stamp (commerceos is the reference shape; its legacy cartridge layout still applies until it migrates).
---

# backlog-sync: the backlog is a mirror of the record

a pull-based `backlog.md` mirrors the landed record. it is no second source
of truth. left alone it drifts, calling finished work "future" and ruled
decisions "open". this flow makes it a checked mirror again: it wears an
honest "as of <date>" stamp, and re-syncing pulls everything the record has
learned since that date back into the file.

the record is honest by construction, append-only, with the owner landing
every entry. the backlog is honest only while fresh. your job: read what the
record has landed, compute what the backlog is missing, stage the fix, and
stop. **you never land. the owner's keypress lands.** say so when you finish.

## the laws you work under (they outrank convenience)

- **read the record, and guess at nothing.** every change you stage traces to
  a landed entry you actually read. a backlog item marked done because you
  "think it's done" is a lie wearing a checkmark. cite the landed note or make
  event, or leave the change unstaged. an uncited edit is the drift this flow
  exists to undo.
- **plain words.** every line you write into the backlog is understood on
  first read by someone who never met the project. no coined vocabulary and
  no hype: the forbidden-phrases table in `soul/voice.md` is out of bounds,
  and `python3 -m engine.voicelint PATH` is what reads it, so say the plain
  thing and let the check confirm it.
- **the pull rules are the file's own law, so obey them.** a new item is
  pullable only when it names its **job row** and its **check** (a runnable
  command whose output a person reads). a row missing its job row waits
  outside the file. a row missing its check goes under OPEN, because the
  pull-ready table is a promise that each row can be picked up cold.
- **stage, and leave the landing.** you edit `backlog.md` and stage one
  `sandbox note`. the owner's keypress is what makes any of it durable, so
  the verbs that read his key are his to type and never yours.

## the flow

### 1. find the backlog and its project

the backlog is `backlog.md` at the project root: the project's directory
inside the workshop, or the repo its `root:` line points at (in PROJECT.md;
the commerceos cartridge is the one legacy holdout, and its `AGENTS.md` names
it). otherwise the project name is the directory's name.

you need two things: the path to `backlog.md`, and the **project name** the
record is keyed by.

### 2. read the "as of" stamp

near the top the backlog carries a freshness stamp, e.g.:

    _as of: 2026-07-12 — catalog re-framed as a feature system; A8 done._

read the date (`YYYY-MM-DD`), which is the last time this mirror was trued
to the record. everything the record landed **after** that date is what may be
missing. if there is no stamp, treat the whole record as unread and add a
stamp at the end.

### 3. read the record since that date

the record is the source, and you read it two ways; do both of them, because
they cover different gaps:

- **the project's page:** read `projects/<name>/CANON.md`. it is the record
  folded into one readable page: every landed make, decision, finding and
  session digest, newest last, and this is your primary read.
- **targeted queries:** `sandbox recall "<terms>" --project <name>` for
  specific threads, e.g. `sandbox recall "delist ruling" --project
  commerceos`. recall matches note bodies, so query the words a decision or
  finding would use.

from what you read since the stamp date, pull out four kinds of change:

1. **work that finished:** `make:` events and "done" notes naming a backlog
   id or the thing an item was going to build.
2. **decisions / rulings that landed:** `note: decision:` / `RULED` entries.
   a ruling can close an item, re-scope it, or open new ones.
3. **findings that change scope:** `note: finding:` entries that resize,
   re-scope, or invalidate an item (a re-baseline, a real number, a conflict
   caught).
4. **new work picked up:** anything the record shows as started or committed
   to that has no row in the backlog yet.

verify by reading and never by file-exists. a `make:` event saying a check
ran green is your evidence a thing is done; the presence of a source file
proves nothing.

### 4. reconcile against the backlog and the specs

hold the record's changes against the current `backlog.md` and the specs
(`spec/*.md`, `spec/parts/*.md`). compute the diff, which is four moves:

- **mark done:** an item whose work the record shows finished, with its check
  green. move it to the done state block, keep its id and one line of what
  proved it.
- **change status:** an item the record re-scoped, resized, or reordered.
  rewrite its row to match; if a ruling changed its dependencies or size, fix
  those columns.
- **add new:** work the record picked up that has no row. each new row
  carries `id · title · serves (job row) · size · deps · check`. if you can
  name the job row and a runnable check, it's a pull-ready row. if you cannot
  yet, add it under an OPEN heading with what it still needs, because a
  checkless row in the pull-ready table is a promise the file cannot keep.
- **cut:** an item the record shows is dead (superseded by a ruling, folded
  into another item, no longer wanted). remove the row and keep one line
  saying why, so the reason survives. the file already has a "slotting
  in/out" section for this, so put the cut line there or in the row's place.

**a discovery that contradicts a spec updates the spec first.** if the record
landed a fact or ruling the spec still gets wrong, that is a spec fix, or a
flag for one. it is never a silent backlog edit. note the mismatch.

if the record since the stamp changed **nothing** the backlog is missing,
that is a real and good outcome. do not invent churn to look busy. refresh
the stamp date, because the mirror was re-checked and found true, and say the
backlog was already current.

### 5. stage the changes, and never land

1. **edit `backlog.md`** with the diff from step 4.
2. **refresh the "as of" stamp** to today's date with a short, plain summary
   of what changed. this is the mirror wearing its new freshness mark.
3. **stage one note:** `sandbox note "backlog sync <project>: <one line: what
   moved to done, what was added, what was cut>"`. one line, plain, naming
   the project.
4. **stop, and say it plainly:** the changes are staged, and they become
   durable when the owner lands them at his own terminal. `sandbox drafts` is
   where they wait until then.

## what a good sync run stages (example)

a run on a backlog stamped `as of: 2026-07-05`, where the record since then
landed one make ("A8 done, audit scores 7/7") and one ruling ("delist all
29"), stages roughly:

- `backlog.md`: A8's row moved into the done block ("A8 done, audit scores
  7 of 7 dimensions, per make eid-…"); a new pull-ready row for the delist
  executor with its job row + check; the delist question row marked RULED;
  the stamp refreshed to today with "A8 done; delist ruled".
- one staged note: `backlog sync commerceos: A8 → done; delist ruled (29);
  added the state-executor row (serves O2, check: approved delist executes
  and verify-renders).`

then: "staged, and waiting. `sandbox drafts` shows them; your keypress at the
terminal lands them."

## the doctor's nudge, and why this exists

`sandbox doctor` reads the mirrors on every run. for each active project
whose `backlog.md` wears an "as of" stamp, it counts the landed notes dated
after that stamp and, when any exist, prints:

    backlog ................ 3 landed notes past its "as of" — re-sync (backlog-sync)

that line is the trigger to run this flow. doctor counts and nudges, and it
leaves the backlog alone. truing the mirror is this flow's job, and landing
the result is the owner's. the two together are the anti-drift loop: the
record advances, doctor notices the mirror fell behind, this flow re-trues
it, the owner lands.
