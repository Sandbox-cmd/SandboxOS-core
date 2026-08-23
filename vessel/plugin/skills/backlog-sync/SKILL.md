---
name: backlog-sync
description: Reconcile a pull-based backlog.md against the landed record so it stops drifting — mark finished work done, fold in rulings and findings, add new work (each with a job row + a runnable check), cut dead items with a reason, and refresh the "as of" date stamp. stage every change; the owner's keypress is what lands it. Use whenever a backlog.md may be behind the record: right after rulings land, right after a `sandbox make --close`, when new work gets picked up, when `sandbox doctor` reports "backlog ... N landed notes past its 'as of' — re-sync", or when someone says the backlog is stale / out of date / needs a re-sync / "sync the backlog" / "living backlog". Works on any project whose backlog.md carries an "as of <date>" stamp (commerceos is the reference shape; its legacy cartridge layout still applies until it migrates).
---

# backlog-sync — the backlog is a mirror of the record

A pull-based `backlog.md` is a mirror of the landed record, not a second
source of truth. Left alone it drifts: it keeps calling finished work
"future" and calls ruled decisions "open". This flow makes it a checked
mirror again — it wears an honest "as of <date>" stamp, and re-syncing pulls
everything the record has learned since that date back into the file.

The record is honest by construction (it is append-only, the owner lands
every entry). The backlog is honest only while fresh. Your job: read what
the record has landed, compute what the backlog is missing, stage the fix,
and stop. **You never land — the owner's keypress lands.** Say so when you
finish.

## the laws you work under (they outrank convenience)

- **Read the record, and guess at nothing.** Every change you stage traces
  to a landed entry you actually read. A backlog item marked done because you
  "think it's done" is a lie wearing a checkmark. Cite the landed note or make
  event, or leave the change unstaged — an uncited edit is the drift this
  flow exists to undo.
- **Plain words.** Every line you write into the backlog is understood on
  first read by someone who never met the project. No coined vocabulary,
  and no hype — the forbidden-phrases table in `soul/voice.md` is out of
  bounds, and `python3 -m engine.voicelint PATH` is what reads it; say
  the plain thing.
- **The pull rules are the file's own law — obey them.** A new item is
  pullable only when it names its **job row** and its **check** (a runnable
  command whose output a person reads). A row missing its job row waits
  outside the file; a row missing its check goes under OPEN, because the
  pull-ready table is a promise that each row can be picked up cold.
- **Stage, and leave the landing.** You edit `backlog.md` and stage one
  `sandbox note`. The owner's keypress is what makes any of it durable, so
  the verbs that read his key are his to type, not yours.

## the flow

### 1. find the backlog and its project

The backlog is `backlog.md` at the project root — the project's directory
inside the workshop, or the repo its `root:` line points at (in PROJECT.md;
the commerceos cartridge is the one legacy holdout, its `AGENTS.md` names
it). Otherwise the project name is the directory's name.

You need two things: the path to `backlog.md`, and the **project name** the
record is keyed by.

### 2. read the "as of" stamp

Near the top the backlog carries a freshness stamp, e.g.:

    _as of: 2026-07-12 — catalog re-framed as a feature system; A8 done._

Read the date (`YYYY-MM-DD`). That is the last time this mirror was trued to
the record. Everything the record landed **after** that date is what may be
missing. If there is no stamp, treat the whole record as unread and add a
stamp at the end.

### 3. read the record since that date

The record is the source. Read it two ways — do both, they cover different
gaps:

- **The project's page:** read `projects/<name>/CANON.md`. It is the record
  folded into one readable page — every landed make, decision, finding, and
  session digest, newest last. This is your primary read.
- **Targeted queries:** `sandbox recall "<terms>" --project <name>` for
  specific threads — e.g. `sandbox recall "delist ruling" --project
  commerceos`. Recall matches note bodies, so query the words a decision or
  finding would use.

From what you read since the stamp date, pull out four kinds of change:

1. **work that finished** — `make:` events and "done" notes naming a
   backlog id or the thing an item was going to build.
2. **decisions / rulings that landed** — `note: decision:` /
   `RULED` entries. A ruling can close an item, re-scope it, or open new
   ones.
3. **findings that change scope** — `note: finding:` entries that resize,
   re-scope, or invalidate an item (a re-baseline, a real number, a conflict
   caught).
4. **new work picked up** — anything the record shows as started or
   committed to that has no row in the backlog yet.

Verify by reading, not by file-exists: a `make:` event that says a check ran
green is your evidence a thing is done, not the presence of a source file.

### 4. reconcile against the backlog and the specs

Hold the record's changes against the current `backlog.md` and the specs
(`spec/*.md`, `spec/parts/*.md`). Compute the diff — four moves:

- **mark done** — an item whose work the record shows finished (with its
  check green). Move it to the done state block, keep its id and one line of
  what proved it.
- **change status** — an item the record re-scoped, resized, or reordered.
  Rewrite its row to match; if a ruling changed its dependencies or size,
  fix those columns.
- **add new** — work the record picked up that has no row. Each new row
  carries: `id · title · serves (job row) · size · deps · check`. If you
  can name the job row and a runnable check, it's a pull-ready row. If you
  cannot yet, add it under an OPEN heading with what it still needs — a
  checkless row in the pull-ready table is a promise the file cannot keep.
- **cut** — an item the record shows is dead (superseded by a ruling,
  folded into another item, no longer wanted). Remove the row and keep one
  line saying why, so the reason survives (the file already has a "slotting
  in/out" section for this — put the cut line there or in the row's place).

**A discovery that contradicts a spec updates the spec first** — if the
record landed a fact or ruling the spec still gets wrong, that is a spec fix
(or a flag for one), not a silent backlog edit. Note the mismatch.

If the record since the stamp changed **nothing** the backlog is missing,
that is a real and good outcome. Do not invent churn to look busy. Refresh
the stamp date (the mirror was re-checked and found true) and say the
backlog was already current.

### 5. stage the changes — never land

1. **Edit `backlog.md`** with the diff from step 4.
2. **Refresh the "as of" stamp** to today's date with a short, plain
   summary of what changed — this is the mirror wearing its new freshness
   mark.
3. **Stage one note:** `sandbox note "backlog sync <project>: <one line —
   what moved to done, what was added, what was cut>"`. One line, plain,
   naming the project.
4. **Stop, and say it plainly:** the changes are staged, and they become
   durable when the owner lands them at his own terminal — `sandbox drafts`
   is where they wait until then.

## what a good sync run stages (example)

A run on a backlog stamped `as of: 2026-07-05` where the record since then
landed one make ("A8 done, audit scores 7/7") and one ruling ("delist all
29") stages roughly:

- `backlog.md`: A8's row moved into the done block ("A8 done — audit scores
  7 of 7 dimensions, per make eid-…"); a new pull-ready row for the delist
  executor with its job row + check; the delist question row marked RULED;
  the stamp refreshed to today with "A8 done; delist ruled".
- one staged note: `backlog sync commerceos: A8 → done; delist ruled (29);
  added the state-executor row (serves O2, check: approved delist executes
  and verify-renders).`

Then: "staged, and waiting — `sandbox drafts` shows them; your keypress at
the terminal lands them."

## the doctor's nudge, and why this exists

`sandbox doctor` reads the mirrors on every run. For each active project
whose `backlog.md` wears an "as of" stamp, it counts the landed notes dated
after that stamp and, when any exist, prints:

    backlog ................ 3 landed notes past its "as of" — re-sync (backlog-sync)

That line is the trigger to run this flow. Doctor counts and nudges, and it
leaves the backlog alone — truing the mirror is this flow's job, and landing
the result is the owner's. The two together are the anti-drift loop: the
record advances, doctor notices the mirror fell behind, this flow re-trues
it, the owner lands.
