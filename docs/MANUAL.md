# MANUAL: every verb

the terminal rule, once: **everything durable stages first, and your
keystroke at a real terminal lands it.** the machine has no k to press: a
keystroke read from the terminal itself is the only consent the gate takes,
and a test harness that borrows a terminal marks its own records
`hand: synthetic` so an audit can tell the two apart.

what lands is what you were shown. `sandbox approve` prints the pile, prints
the fingerprint of that exact pile, reads one key, and carries the same
fingerprint into the landing line, so the two can be compared afterwards.

the gate has two speeds. most durable things wait for your k first. a few
reversible acts (closing a project, an applied correction) happen at once and
are confirmed at your next `sandbox resume`, with the snapshot kept and the
revert path named, and a ship carries none of them until that confirmation.

## the verbs

<!-- verbs:begin (generated — run: python3 -m engine.selfmap --write) -->
| verb | what it does | gate | writes |
|---|---|---|---|
| `app` | install or remove an app; your k lands the install | needs your k | apps, the workshop |
| `approve` | land the drafts waiting on your k, at a real terminal | needs your k at a real terminal | the workshop, the project |
| `builds` | list what the shelf keeps | no key needed | nothing |
| `canon` | rebuild a project's canon page, or the memory page a session reads | no key needed | the workshop, the project |
| `check` | run the project's checks; a green run proves what waited on them | no key needed | the workshop |
| `doctor` | check the workshop's health, one line each | no key needed | nothing |
| `drafts` | show the notes waiting for your approval; drop one by number | no key needed | the workshop |
| `export` | write the record to one file you can hand over | no key needed | the workshop |
| `fetch` | bring a friend's build onto your shelf | needs your k | the shelf |
| `help` | this page: every verb, what it does, what it needs | no key needed | nothing |
| `import` | carry an old workshop in, whole | no key needed | the workshop, the record, the project, the shelf |
| `init` | open a workshop here and place the vessel | no key needed | the workshop, the record, settings |
| `invalidate` | strike a landed line; it stays, struck — your k lands it | needs your k | the workshop |
| `make` | open a build session, or close it on a computed diff | no key needed | the workshop |
| `note` | stage one line on the record; your k lands it | needs your k | the workshop |
| `page` | write the record as one html file | no key needed | the workshop |
| `play` | open the playground, where nothing counts | no key needed | the workshop |
| `plugin-dir` | print the directory the plugin loads from | no key needed | nothing |
| `project` | make, switch, or finish a project | no key needed | the project, the workshop |
| `recall` | ask the record before deciding twice | no key needed | nothing |
| `release` | check what a release needs before the ceremony starts | no key needed | nothing |
| `reset` | restore a placed file to what this core ships | no key needed | the workshop, the record |
| `resume` | what happened since you left, plus one k for what waited | needs your k at a real terminal | the workshop, the project |
| `save` | keep a build on the shelf | no key needed | the shelf |
| `seal` | write this core's manifest | no key needed | this core |
| `session` | open or close a working session on the record | no key needed | the workshop |
| `setup` | write the sandbox shim where your shell can find it | no key needed | the workshop |
| `share` | stage a build for someone else to fetch | no key needed | the workshop |
| `shelf-dir` | print the directory a friend adds as a marketplace | no key needed | nothing |
| `ship` | run the project's own checks; celebrate only on green | needs your k | the workshop |
| `status` | what the workshop holds and what needs you | no key needed | nothing |
| `update` | move the system forward; your own things stay | no key needed | the workshop, the record, settings |
| `use` | load a shelf build onto a project | no key needed | the project, the shelf |
| `verify` | check this core against its manifest | no key needed | nothing |
| `version` | print this core's version and which tree runs | no key needed | nothing |
<!-- verbs:end -->

## the daily loop

- arrive: `sandbox resume` prints what happened since you left, plus one k
  for what waited.
- work: `sandbox project on NAME`, then build. wrap a piece of building in
  `sandbox make --open "intent"` … `sandbox make --close NAME --summary "…"`.
  the close computes the diff and stages the summary, then re-runs your checks
  before it lands.
- capture: `sandbox note "what you found"` the moment it happens. staged
  by mistake? `sandbox drafts --drop N` retracts it and prints the dropped
  line in full, so the retraction happens in the open.
- ship: fill `## checks` in PROJECT.md, then run `sandbox ship`. your k
  ratifies those exact check lines once. the digest of them prints on every
  run, and a green re-ship over the same lines goes through without asking
  again. each line gets 120 seconds; a slower one names its own limit at
  its end, `node --test slow.mjs # timeout 300s` (1 to 3600 seconds), and
  the limit is part of the lines your k reads. when the tool stops a line
  (its limit, ctrl-c, a closed terminal) it stops what the line started, a
  server it spawned included. a process that forks twice to detach, or one a
  line leaves running after it finishes, is out of its reach.
- hand it over: `sandbox export` writes the whole record to one file, in time
  order, with `--redact` for the paths that name you and `--html` for the same
  record as a page. the file says what it is at the foot: opening it leaves
  nothing on the record.
- leave: drafts wait, and the next resume lands them on your key.

## sharing

- `sandbox save PATH` presses a build (card + payload + checksum) onto
  your shelf; `sandbox use NAME` copies it onto a project; a drifted
  payload refuses to spread.
- `sandbox share NAME --to DIR` stages a build for a shelf repo. the scrub
  runs first and git history stays home; the push is your hand.
- `sandbox fetch --from DIR [NAME]` lists or pulls: bytes verify against
  the card before your k, and the source is labeled honestly, because a
  matching hash proves the bytes are the same bytes and says nothing at all
  about the hand behind them.
- `sandbox app install DIR`, `app remove NAME` and plain `app`: add-ons
  declare their placements; code refuses anything outside the app's own room
  before your key is even asked; removal takes exactly what install placed.

## the system itself

- `sandbox update` moves the workshop to this core's version: placement
  re-sync (your edited files are skipped and named), migrations (numbered,
  idempotent), version recorded. pulling new code into the clone is your own
  hand, and update tells you honestly what it did not do for you.
- `sandbox verify` and `sandbox seal` hold this copy against its manifest.
  strict verification adds a signature over those hashes, and it turns on the
  moment you set `SANDBOX_MINISIGN_PUBKEY` to the key from the release notes.
- `sandbox reset PATH-or-NAME` returns one placed file to pristine, on your
  word. a short name (`sandbox reset CLAUDE.md`) resolves against what init
  places, even when an older core placed the file without recording it.
- `sandbox plugin-dir` prints where the plugin lives. the marketplace init
  writes points the host at this core's own tree, so the plugin follows the
  tree instead of holding a copy that goes stale.
- `sandbox doctor` reads health, skew, staleness and skipped placements;
  every failing line names its fix.

## environment

`SANDBOX_HOME` sets where the workshop lives (default `~/Sandbox`). that
directory is the custody unit: copy it wholesale and everything moves with it,
and the clone of this repo stays disposable.
