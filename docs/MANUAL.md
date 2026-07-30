# MANUAL — every verb

the terminal rule, once: **at a real terminal, your keystroke lands things;
headless, they become drafts waiting for your approval.** the machine can
never press your k. a test harness that fakes a terminal marks its own
records `hand: synthetic` so an audit can always tell.

the gate has two speeds: most durable things wait for your k first;
a few reversible acts (closing a project, an applied correction) happen
immediately and are confirmed at your next `sandbox resume` — snapshot
kept, revert path named, and nothing rides into a ship unconfirmed.

## the verbs

<!-- verbs:begin (generated — run: python3 -m engine.selfmap --write) -->
| verb | gate | writes |
|---|---|---|
| `app` | needs your k | apps, workshop |
| `approve` | needs your k at a real terminal | workshop, project |
| `builds` | runs freely | nothing |
| `doctor` | runs freely | nothing |
| `drafts` | runs freely | nothing |
| `fetch` | needs your k | shelf |
| `help` | runs freely | nothing |
| `import` | runs freely | workshop, state, project, shelf |
| `init` | runs freely | workshop, state, settings |
| `make` | runs freely | workshop |
| `note` | needs your k | workshop |
| `page` | runs freely | workshop |
| `play` | runs freely | workshop |
| `project` | runs freely | project, workshop |
| `recall` | runs freely | nothing |
| `release` | runs freely | nothing |
| `reset` | runs freely | workshop, state |
| `resume` | needs your k at a real terminal | workshop, project |
| `save` | runs freely | shelf |
| `seal` | runs freely | core |
| `setup` | runs freely | workshop |
| `share` | runs freely | workshop |
| `ship` | needs your k | workshop |
| `status` | runs freely | nothing |
| `update` | runs freely | workshop, state, settings |
| `use` | runs freely | project, shelf |
| `verify` | runs freely | nothing |
| `version` | runs freely | nothing |
<!-- verbs:end -->

## the daily loop

- arrive: `sandbox resume` — since you left, plus one k for what waited.
- work: `sandbox project on NAME`, then build; wrap AI-assisted or heavy
  passes in `sandbox make --open "intent"` … `make --close --summary "…"`
  — the diff is computed, the summary staged.
- capture: `sandbox note "what you found"` the moment it happens.
- ship: fill `## checks` in PROJECT.md, `sandbox ship` — your k ratifies
  those exact check lines once; green re-ships need no ceremony.
- leave: nothing required. drafts wait; the next resume lands them.

## sharing

- `sandbox save PATH` presses a build (card + payload + checksum) onto
  your shelf; `sandbox use NAME` copies it onto a project; a drifted
  payload refuses to spread.
- `sandbox share NAME --to DIR` stages a build for a shelf repo — the
  scrub runs first, git history never rides, the push is your hand.
- `sandbox fetch --from DIR [NAME]` lists or pulls: bytes verify against
  the card before your k, and the source is labeled honestly — a matching
  hash proves internal consistency, not who made it.
- `sandbox app install DIR` / `app remove NAME` / `app` — add-ons declare
  their placements; code refuses anything outside the app's own room
  before your key is even asked; removal takes exactly what install placed.

## the system itself

- `sandbox update` — moves the workshop to this core's version: placement
  re-sync (your edited files are skipped and named), migrations (numbered,
  idempotent), version recorded. pulling new code into the clone is your
  hand; update tells you honestly what it did not do for you.
- `sandbox verify` / `sandbox seal` — the copy against its manifest.
  strict verification (a signature, not just hashes) turns on when you set
  `SANDBOX_MINISIGN_PUBKEY` to the key from the release notes.
- `sandbox reset PATH` — return one placed file to pristine, on your word.
- `sandbox doctor` — health, skew, staleness, skipped placements; every
  failing line names its fix.

## environment

`SANDBOX_HOME` — where the workshop lives (default `~/Sandbox`). that
directory is the custody unit: copy it wholesale and everything moves; the
clone of this repo is disposable.
