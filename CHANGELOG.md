# CHANGELOG

## 9.0.5 — the suite reads the same at a keyboard (2026-10-23)

9.0.4 closed the release check's stdin and left the tests themselves open:
`python3 -m unittest` typed at a terminal still ran seven of them red. a
note's origin follows stdin's `isatty` and doctor's colour follows stdout's,
so the same suite was green from a pipe and red at the owner's keyboard.

### built

- the test package stands at a pipe wherever it is started. when stdin is a
  terminal, `engine/tests/__init__.py` points it at `/dev/null` at the
  descriptor, so every child a test starts inherits the pipe as well, and it
  sets `NO_COLOR`. a test that wants a terminal already says so: it mocks
  `isatty`, presses the rig's key, or opens its own pty.
- a test can no longer read a key the owner typed for something else.
- nothing the tool does outside its tests changes.

### checked

- a new test in `engine/tests/test_notes.py` holds the pin: no terminal in
  the test process or in a child it starts, `NO_COLOR` set, and an unmocked
  note staged as the machine's.
- the suite passes from a pipe and under a pseudo-terminal, where it failed
  seven tests before.

## 9.0.4 — a session starts from NOW.md (2026-10-23)

a session started from a project's CANON.md, and the sandbox project's had
grown to 550 KB, far past what a session can read whole. phase 1 of the reset
gives every project one short page that says where it stands and what comes
next. the archive stays where it is, and `sandbox recall` reads it when a
session needs the history.

### built

- a new project is born with `NOW.md` beside its contract: the outcome, where
  it stands, the authority it works under, and the next move. its contract's
  notes open with `start here: NOW.md`.
- `sandbox project now [NAME] [--for PATH]` prints the page of the project a
  path belongs to: one under `projects/NAME/`, or the deepest declared
  `root:` that holds it. a done project claims no path. anywhere else it
  prints one line per switched-on project naming what comes next. the page
  is cut at 4000 characters.
- the session-start hook adds that page after the needs sentence, with a
  blank line between them. with no page to give, the sentence stands alone,
  as it did.
- a `--root` that is a git repository gets no briefs written into it, and the
  report line says so and names the door. on 2026-10-23 `project new sandbox
  --root ~/Sandbox/system` left two untracked pages in the release-only main.
- `sandbox status` keeps done projects out of its table and names them on one
  line, `N done: a, b, c`. the count line is unchanged.
- the charter reads a project's NOW.md first and asks `sandbox recall` for
  what came before. the consent and law 11 lines wait for phase 2.
- `sandbox release` runs the suite with stdin closed. a note's origin follows
  `isatty`, and seven tests that expect a machine origin never pinned stdin,
  so 9.0.3's suite passed from a pipe and failed at the owner's keyboard. the
  tests themselves still read the terminal and stay open.

### checked

- `engine/tests/test_project.py` holds the new page and its contract line, a
  root with `.git` as a directory or a file, `project_for_path` over a
  projects dir, two nested roots and a done project, the page cut, and the
  next lines from switched-on projects.
- `engine/tests/test_plugin_payload.py` starts a session inside a project and
  finds the page after the sentence; the two one-line tests pass unchanged.
- `engine/tests/test_resume.py` holds the done line and its absence.
- the suite passes from a pipe and through `sandbox release` under a
  pseudo-terminal, where 9.0.3's failed seven.

## 9.0.3 — a check gets the time it needs (2026-10-17)

a check line had 120 seconds, and a slow one that passed was refused as red.
one project's rehearsal check passes 10 of 10 in 170 seconds, and it held two
make closes open for days; commerceos split its own check lines four times to
fit under the limit. the same day showed a second fault. a line that ran out
of time left what it had started running: a dev server it had started
detached outlived its check, held its port, and every later run of that check
hung on the port. the runner killed only the shell.

### built

- a check line may name its own limit at its end, as a shell comment:
  `node --test slow.mjs # timeout 300s`. the shell ignores it, and the tool
  reads it in `line_timeout` in `engine/ship.py`. a line with no limit keeps
  120 seconds, and a timeout names the limit it hit. a limit runs from 1 to
  3600 seconds. a line that looks like it names one and does not read
  (`# Timeout 300s`, `# timeout 5m`, `# timeout 0s`, `# timeout 7200s`) is
  red with a line giving the shape, so the limit your key read is the one
  that runs.
- the limit is part of the line, so changing it changes the checks'
  fingerprint and the next ship asks for your key again. ship's page shows the
  first 20 lines of a long list, so a changed line further down is ratified
  without being on screen; that predates this release and stays open.
- each check line runs in its own session. when the tool stops a line (its
  limit, ctrl-c, a closed terminal, a stop signal to sandbox) it stops what
  the line started: SIGTERM to the line's process group, to every group a
  descendant moved into and to each descendant, then SIGKILL to each of those
  still standing five seconds later. descendants are found by parent link
  before the first signal, which reaches a child that started its own session
  the way node's `detached: true` does; a member of the line's group whose
  launcher already exited is reached through the group.
- while a line is being stopped, a second ctrl-c or stop signal waits until
  the stop is done, so it cannot cut the stop short before SIGKILL. an ignored
  signal stays ignored, so `nohup sandbox check` still outlives its terminal.
  with no `ps` on the machine the stop still reaches the line's own group.
- out of reach, said plainly: a process that detaches by forking twice, a
  container or launchd job a line starts, and anything a line leaves running
  after it finishes in time.
- a line that finishes in time gives the same output and exit code as before.
  it runs with no controlling terminal; a check that drives a terminal opens
  its own, and no current one reads `/dev/tty`.
- `docs/MANUAL.md` says the limit and the stop in the ship paragraph.

### checked

- fifteen tests in `engine/tests/test_ship.py`. five read the limit: its edge
  cases, a limit that does not read, a slow line green under its own limit and
  red without one, and the fingerprint moving with the limit. eight stop a line
  that left something behind: a child in the line's group, one that ignores
  SIGTERM, one that started its own session, a group member whose launcher
  exited, ctrl-c, a second ctrl-c during the stop, a stop signal to sandbox,
  and a machine with no `ps`; one more keeps an ignored hangup ignored. the
  last one runs a line that finishes in time and finds it untouched. each of
  the nine stop and signal cases was red before its fix, in the test run or
  in a probe of the same case.
- the home-path floor in `engine/tests/test_door.py` reads what would ship: in
  a git checkout, the tracked files and the untracked ones git would commit.
  its own docstring always said "no committed file", and its walk read every
  file on disk, so a host's ignored `.claude/settings.local.json` (written
  2026-09-05) turned the suite red on this machine and would have stopped the
  release. outside a checkout it still walks the whole tree, and an untracked
  file carrying a home path still fails it.
- the README's import count reads fifteen: `signal` joins the list.
- no project's check lines change, and no ratification moves.

## 9.0.2 — written like a person, for a person (2026-08-23)

the writing convention entered the soul whole. the em dash was the piece a
reader noticed first, and the ruling that followed put the rest of it into one
position and behind one check.

the ruling, verbatim from the record:

```
[claimed] [machine] ruling R27 (owner, 2026-08-23): the writing convention is
the whole of how the workshop writes, voices, narrates and talks to a person,
and it enters the soul and the lint in full — the em dash was one element of
many. the six dimensions and the core from the voices research
(~/eighth/shelf/builds/voices: framework.md, tells.md, research.md; plain
hands) become a soul position with its checks; voicelint gates prose pages on
it; every page a person reads is rebuilt to it, the README from the ground up.
owner's words: 'dont just remove the em-dashes, now that we know what was
wrong lets rebuild it. and lets also make the change for the rule in all
places not just for the em dashes but for the entire scope expanding from that
one specific part as its only 1 element of many in how we write, voice,
narrate and talk.'
```

### built

- `soul/voice.md` gains position 9, "written like a person, for a person": the
  core as checkable rules, the six dimensions of the tone framework set as this
  house's own numbers, and the two boundaries stated out loud. it applies to
  every page a person reads. it stops at an engine output line, where the em
  dash is a field separator and a one-line status is a label.
- the forbidden table gains nine rows out of the AI-tell catalog the ruling
  names: the flat adverbs, the significance words, the two connectors of the
  five-paragraph mold, one paragraph opener, two more hype adjectives, the
  metaphor uses of two scenery nouns, and one dead opener. every phrase reaches
  the table with its reason, the way every phrase before it did, and the
  all-scope list runs 58 now.
- check E in `engine/voicelint.py` reads the 24 prose pages. three gates: the em
  dash outside quoted engine output, the four contrast constructions, and three
  consecutive sentences within two words of each other. three counts print: the
  rule of three, the pace, the filler density. one `prose:` row per page, then a
  summary line.
- an exemption marker, `<!-- voice: contrast ok: why -->`, takes one line out of
  one rule. a marker with no reason rules nothing and reports itself, which is
  the rule every row of `EXEMPTIONS` already obeys. `soul/voice.md` carries the
  first one, over conviction 4's own name.
- `PROSE_DEBT` in `engine/tests/test_voice.py` freezes what 21 pages owe the new
  gate, by exact count. the rule is real from today; the pages are rebuilt after
  it. a row that grows is a regression, and a rebuilt page drops its row in the
  same commit as its words.
- the two projections carry position 9 in their own words.
  `vessel/plugin/output-styles/across-the-desk.md` gains a rhythm section and
  keeps its 65-line budget. the voicer's pass runs to seven steps, with the
  shape and the six settings written into `vessel/plugin/crew.json` and rendered
  from there.
- `README.md`, `soul/voice.md` and the style pass the new gate today. thirteen
  fixtures under `engine/tests/voice_fixtures/` hold each rule to a failing page
  and a passing one.
- the three pages a stranger walks are rebuilt to position 9, and their rows in
  the ceiling table drop to zero. `docs/START-HERE.md` came off 34 gates with
  its nine steps intact. `engine/tests/test_start_here.py` still walks every
  command block on the page at a pty and then down a pipe, and the tutorial's
  step words keep their shape on a colon. `docs/OPEN.md` came off 11, every debt
  still carrying its `closes:` line and its J row. `docs/MANUAL.md` came off 17
  in the prose around the generated verb table, which stays byte for byte what
  `engine/selfmap.py` writes.
- check E stops at the changelog's history. it reads the section being written
  (this one) and blanks every release below it, because a shipped section is
  what that release said and re-cutting those words now would edit the past. the
  rule is `changelog_history` in `engine/voicelint.py`, and a fixture pair holds
  it: an em dash in the open section gates, and the same mark down in the
  history does not.

## 9.0.1 — the audits read back (2026-08-23)

the first release after the ninth body, the same day. three audits read the
tree, the live workshop and the program's own pages against each other, and
everything below is one of their findings closed — plus the README written
again from the manifesto: why this exists, what it is, the principles and
what each one refuses, then the first minute.

### built

- a struck `build-kept` line leaves the shelf reading: doctor's
  journal-vs-disk reader and the registry's build fold skip a line the owner
  struck with `invalidate`, and the line itself stays on the record. found
  re-pressing commerceos on the shelf, after a mis-named save.
- `status --line` counts the ship debt of the project it names. it printed a
  workshop-wide sum beside one project's name — `37 closes since ship` while
  doctor read 0 for the same project — and it folds the one `needs()` list
  now, like the other two renderers.
- doctor leaves an orphaned plugin cache out of its style copies. a cache
  directory marked `.orphaned_at`, or one whose marketplace is off the host's
  `known_marketplaces.json`, sits outside what `sandbox update` walks. a row
  prescribing a verb that stops short of it is a door onto a wall.
- two host receipts, `host: plugin marketplace` and `host: plugin on`. the
  marketplace entry pointing at this tree and the plugin turned on under it
  decide whether a session loads this core at all; absent, they read LOOK
  with `sandbox init`, and unreadable they read `?`.
- doctor's exit is the repair block's alone, all the way down: an open make
  past a week is a LOOK and no longer red, so a three-week-old make stops
  teaching the owner to ignore the exit code. the rows that still decide it
  are the record and the disk disagreeing, a placed or kept file drifted,
  and a core and a workshop on different versions.
- `sandbox page` takes export's flags. it had no entry in the flag table, so
  the one door refused `--redact`, `--project`, `--since` and `--to` before
  `page` could hand them on to export.
- `sandbox export` prints its path with `~` for the home, the way every
  other path this core prints does.
- `.claude-plugin/marketplace.json` is inside the seal. it names the plugin
  source a host loads out of this tree, so a change to it changes what runs
  on somebody else's machine.
- the two skills that cited a `references/banned-words.txt` cite
  `soul/voice.md`'s forbidden-phrases table and `python3 -m engine.voicelint`,
  which reads it. the file existed nowhere, and the check that grepped it
  could never fail.
- the git hook is placed in this tree: `sandbox release --hook` writes
  `.git/hooks/commit-msg`, so the wall's fast no is a file rather than a
  claim about one.
- one unreachable refusal in `engine/ship.py` now says what the reachable one
  says; the ops tuple's comment counts eleven ops, `check` and `export` both
  born with 9.0; and `update --rebuild` takes its list from
  `registry.PROJECTIONS` instead of a second hand-typed one.
- `soul/surfaces.md`: three ruled caps exemptions rather than two; row 21
  says the statusline is produced outside the core by the owner's own script;
  row 24 is marked unbuilt; row 29's budget is the fourteen words its own
  exemplar runs to; rows 16 and 28 carry what ships. `soul/lineage.md` counts
  nine bodies.
- the README is re-derived from the manifesto, frame first: why this exists
  and what it is, then the sitting, then the bill, then the claims.
- `docs/OPEN.md` retires the doctor-exit item R24 ruled, and names five debts
  it was carrying silently.

### known, not fixed

on a work branch the reseal after each commit leaves `manifest.json.minisig`
signing 9.0.0's manifest against a manifest that has moved. plain
`sandbox verify` reads clean; strict verify (`SANDBOX_MINISIGN_PUBKEY` set)
refuses. the 9.0.1 release re-signs. `docs/OPEN.md` carries it as a debt.

### for scripts

R26's placeholder sweep: the engine printed the spec's `<name>` shape in ten
places and now prints the ruled caps. the lint exempts `WHO` and `BUILD`
beside `NAME`, `PATH`, `DIR`, `ID`, `K`, `N` and `VALUE`. old → new, exact:

- `engine/status.py` — `sandbox reset <path> re-baselines` → `sandbox reset
  PATH re-baselines`
- `engine/status.py` — `restore on your word: sandbox reset <name>` →
  `restore on your word: sandbox reset NAME`
- `engine/status.py` — `%s says %r — sandbox reset <name>` → `%s says %r —
  sandbox reset NAME`
- `engine/status.py` — `sandbox share %s --to <dir>` → `sandbox share %s
  --to DIR`
- `engine/verbs.py` — `project new <name> [goal] [--root <dir>] · on <name> ·
  off <name> · done <name>` → `project new NAME [goal] [--root DIR] · on NAME
  · off NAME · done NAME`
- `engine/verbs.py` — `sandbox note "pull-witnessed: <who> <build>"` →
  `sandbox note "pull-witnessed: WHO BUILD"`
- `engine/verbs.py` — `what would work: git switch -c <name> && git commit` →
  `what would work: git switch -c NAME && git commit`
- `engine/verbs.py` — the `fetch` flag table's `--expect-key <key>` →
  `--expect-key K`
- `engine/verbs.py` — the `update` flag table's `--rebuild
  <place|shelf|canon|index>` → `--rebuild place|shelf|canon|index`
- `engine/integrity.py` — `work belongs on a branch: git switch -c <name>,
  then start again` → `... git switch -c NAME, then start again`
- `engine/onboard.py` — `retire them when you like: rm -r
  ~/.claude/skills/<name>` → `... rm -r ~/.claude/skills/NAME`

four more printed lines moved with the fixes above:

- `engine/status.py` — `%d closes since ship` → `%d close since ship` at one,
  `%d closes since ship` above one
- `engine/status.py` — the voice row's `, %d style copy(s) match` is dropped
  when this machine holds no copy
- `engine/ship.py` — the unreachable `ratify` refusal prints the sentence
  `ship` already prints: `a ship with no checks is a costume — add a line
  under PROJECT.md's ## checks`
- `engine/apps.py` — `source: %s — UNVERIFIED (the hash proves consistency,
  not who made it)` → `source: UNVERIFIED — %s is not the catalog. the hash
  proves the bytes are the same bytes, not who wrote them.`

### retired tests

- `test_five_files_each_wearing_lineage` — reads as
  `test_six_files_each_wearing_lineage`; `soul/` holds six pages, and
  `surfaces.md` was read by none of test_soul's checks.

## 9.0.0 — one home, one key, one plugin (2026-08-23)

the ninth body. two discovery runs closed on 8.2.3 the same day and were
built as one release: one tree at `~/Sandbox/system` that the shim follows;
one real key read at the terminal with the fingerprint of what was shown;
one plugin that carries the hooks, six briefs, three skills, the voice and
two commands; the shelf as a marketplace with its own signing key; `export`,
with `page` as its html alias; `make` riding the session; `ship` as the
celebration; the soul re-derived and a lint that reaches every printed
string. the loud line, scoped to claims: NOTHING LANDS THAT YOU WERE NOT
SHOWN. `law/` is untouched.


### four rulings, built (2026-08-23)
- R23 `UNVERIFIED` is the fourth caps signal word (FAIL, LOOK, DRAFTS, UNVERIFIED); the lint's `CAPS_ALLOWED` and `soul/voice.md` position 8 carry it; the caps debt is empty.
- R24 doctor's exit is the repair block's alone: a LOOK on a `host:` row is named and the run stays green (`test_a_host_look_never_changes_the_exit`).
- R25 the git hook moves from `pre-commit` to `commit-msg` — `vessel/git/commit-msg`; `sandbox release --hook` places it there; the file's text is unchanged but its placement line.
- R26 usage placeholders stay `NAME`/`PATH`/`DIR`; the spec's `<name>` form is superseded.

this section also carries the one thing a
release cannot reconstruct later: which of 8.2.3's checks stopped running,
and under what name they run now. `engine/tests/carry_ledger.py` reads
8.2.3's test names straight out of the tag and refuses any retirement this
list does not name.

### retired tests

- `test_open_build_close_computes_the_diff` — reads as
  `test_open_edit_close_computes_the_diff`; the make session is the same.
- `test_build_with_a_fake_builder_runs_and_closes` and
  `test_build_without_a_builder_hands_you_the_prompt` — the verb carries no
  builder at all now, held by `test_no_headless_builder` and
  `test_the_verb_carries_no_builder_at_all`.
- `test_approve_headless_lands_nothing` — reads as
  `test_approve_headless_refuses_with_the_verb_in_it`, which also pins the
  exit code the old one left loose.
- `test_resume_headless_shows_but_touches_nothing` and
  `test_resume_with_key_lands_and_confirms` — read as
  `test_resume_headless_refuses_with_its_own_name_and_exits_one` and
  `test_resume_with_key_lands_and_confirms_under_one_hash`.
- `test_human_at_tty_lands_with_computed_ink` — reads as
  `test_human_origin_stages_too`; the rung is computed at the landing.
- `test_synthetic_hand_says_its_name` — reads as
  `test_the_synthetic_terminal_still_says_its_name`, beside
  `test_the_rig_key_is_always_stamped_synthetic`.
- `test_record_write_denied`, `test_bash_naming_the_record_denied`,
  `test_core_tree_fenced_from_workshop_sessions`,
  `test_cross_project_write_denied_same_project_passes`,
  `test_auto_memory_write_routed_to_the_gate` and
  `test_malformed_input_fails_open` — the guard moved into the plugin and its
  refusals were rewritten in the first person; the same six fences are held
  by `test_a_write_into_the_record_is_turned_back`,
  `test_writing_the_record_is_turned_back`,
  `test_a_write_into_the_system_tree_is_turned_back`,
  `test_a_write_into_another_project_names_both`,
  `test_a_write_into_the_hosts_memory_is_routed_to_the_key` and
  `test_malformed_events_decide_nothing`.
- `test_dead_hooks_pruned_live_ones_kept` — reads as
  `test_the_8x_guard_wiring_is_pruned_and_foreign_hooks_stand`.
- `test_agent_count_is_whatever_vessel_ships` — the crew ships in the plugin
  and is placed nowhere, held by
  `test_the_crew_ships_in_the_plugin_and_init_places_none_of_it`.
- `test_no_cut_word_in_any_engine_or_vessel_file` — the cut-list is read from
  `soul/voice.md` now, held by `test_no_forbidden_phrase_in_any_text`.
- `test_catalog_pin_upgrades_trust_and_tamper_is_named` — reads as
  `test_a_pin_upgrades_trust_and_tamper_is_named`.
- `test_person_data_refuses_the_share` — split in two:
  `test_a_private_term_still_refuses` and
  `test_a_deny_listed_file_still_refuses`.
- `test_page_renders_self_contained_with_asof` — the page stopped wearing an
  "as of" when it stopped being a mirror of workshop state (R8); the file's
  own claims are held by `test_the_page_asks_the_network_for_nothing` and
  `test_the_page_carries_the_footer_and_no_live_claim`.
- `test_page_escapes_what_it_renders` — reads as
  `test_the_page_escapes_every_field_it_renders`.
- `test_clean_build_stages_with_honest_notes` — reads as
  `test_a_card_from_a_stock_home_shares_and_exits_zero`, beside
  `test_the_staged_card_says_which_workshop_not_whose`.

### the stranger's four pages, re-derived (X4, X5, X6)

no 8.2.3 test name was retired or renamed here — the doc pins kept their
names and changed what they hold, which the carry ledger cannot see, so it is
written down:

- `test_readme_loud_line_is_true` held the exact words
  `A PIPE CANNOT APPROVE ANYTHING`. under R12 it holds
  `NOTHING LANDS THAT YOU WERE NOT SHOWN.` and one more behaviour: a key
  minted over one pile lands nothing when the pile moved under it. the pipe
  refusal keeps its paragraph and its line citation beneath the shout, so
  what it always proved is still proved.
- `test_readme_install_block_obeys_its_three_laws` required the block to end
  in `./sandbox doctor` after a bare `git clone`. it now requires exactly one
  clone, into `~/Sandbox/system`, still with the bill named above it and the
  health check at the end.
- `test_version_is_read_not_written` reads the README with its `sitting`
  block cut out: the version inside a transcript was printed rather than
  typed, and `test_readme_sitting` re-runs it against this build.
- `test_voice.TestNegation`'s `STACKED_DEBT` and `NAKED_DEBT` are empty. they
  carried `README.md: 1` and `docs/OPEN.md: 2` stacked, `docs/OPEN.md: 2`
  naked; the four pages were rewritten and the sentences are gone, so a new
  entry in either table is a regression rather than a debt.

new in the same pass: `engine/tests/test_readme_sitting.py` (the first
screen's transcript is re-run in a throwaway workshop) and
`engine/tests/test_start_here.py` (all nine steps walked at a pty and down a
pipe, step 5's Claude Code session skipped by name and its documented
terminal fallback run in its place), plus twelve pins in `test_doc_claims.py`
for the first-screen order, the cost line, the seven claim rows, the `law/`
and `soul/` counts, the *amana* gloss, and OPEN.md's `closes:` per debt.

### for scripts (X9)

the final voice sweep moved no token's case: `FAIL`, `LOOK` and `DRAFTS`
stand where the ruling put them, `UNVERIFIED` is the fourth signal word
(R23, and `soul/surfaces.md`'s open list is empty), and the usage placeholders
(`NAME`, `PATH`, `DIR`, `ID`) keep their caps — the manual and the README
spell them the same way, so the lint exempts them by name instead.

what did move is the wording of fifteen printed lines. old → new, exact:

- `engine/desk.py` — `an assertion needs a body` → `a note needs words of
  its own`
- `engine/desk.py` — `a claim never marks its own ink — computed at landing`
  → `a claim never marks itself — the mark is computed at landing`
- `engine/registry.py` — `fact: ink must be one of %s` → `fact: the mark
  must be one of %s`
- `engine/export.py` — `a redacted export is a reading copy, and import
  would land a self with holes in it. run export --portable on its own, or
  hand the .md file over by itself.` → `a redacted export is a reading copy;
  import needs every line. run export --portable by itself.`
- `engine/integrity.py` — `i placed the pre-commit hook at %s — it asks this
  verb whether a commit on main is a release commit` → `i placed the
  commit-msg hook at %s — it asks this verb before any commit on main`
  (R25 moved the hook in the same release)
- `engine/make.py` — `%d red — no close: FAIL %s. fix them, then: sandbox
  make --close %s — or change the line under '## checks' in PROJECT.md; your
  next ship re-reads your k on it` → `%d red — no close: FAIL %s. fix them,
  then: sandbox make --close %s` (R11: one door, and it is the check)
- `engine/make.py` — `no checks under ## checks — …` → `nothing under ##
  checks — a ship with nothing under it is a costume; add one line there`
- `engine/share.py` — `no shelf key is set — set %s to a key of its own, or
  share it unsigned` → `no shelf key is set — point %s at its own key, or
  share unsigned`
- `engine/share.py` — `%s names the key this core signs itself with — the
  shelf takes a second key, so a leaked one never speaks for the core` →
  `%s signs this core — the shelf takes a second key, so a leak stops there`
- `engine/share.py` — `i could not read the public half of that key — set %s
  to its .pub file` → `i could not read that key's public half — set %s to
  its .pub file`
- `engine/shelf.py` — `the card at the source is torn — a build is one card
  and exactly one payload` → the same line with `exactly` dropped
- `engine/shelf.py` — `the payload for %s no longer matches its card —
  refusing to spread a build that drifted` → `%s no longer matches its card
  — i refuse to spread a build that drifted`
- `engine/ship.py` — `a ship with nothing under it is a costume — put one
  command per line under ## checks in PROJECT.md` → `a ship with no checks
  is a costume — add a line under PROJECT.md's ## checks`
- `engine/succession.py` — `this workshop already has a landed record of its
  own — import only fills an empty one, and never merges selves` → `this
  workshop already has a record — import fills an empty one and never merges
  selves`
- `engine/verbs.py` — `shared %d, no pull witnessed yet — when a friend
  tells you, stage it: sandbox note "pull-witnessed: <who> <build>"` →
  `shared %d, no pull witnessed yet — stage one: sandbox note
  "pull-witnessed: <who> <build>"`

`README.md` and `docs/START-HERE.md` carry the ship and make lines verbatim;
both pages moved in the same change, so what the page shows is what the tool
says.

## 8.2.3 — the class closed, the ceremony finished (2026-08-09)

three findings landed the same morning on 8.2.2, and every one traced to a
class closed at one instance. this release closes the classes.

- unknown flags refuse at the one door, for every verb: `dispatch` holds
  each verb's flag table, so no verb can ever swallow a `--flag` as
  content again. `note --help` once staged a draft whose whole body was
  the flag; now it refuses with exit 2, and so does everything else.
- `drafts --drop N` retracts a waiting draft — the exit the accidental
  staging never had. the dropped body prints in full, so the retraction
  happens in the open; torn staging lines stay on disk untouched.
- the release ceremony ends at the Releases page, not at the push: the
  wall's fifth move is `publish`, with notes the wall itself writes from
  the CHANGELOG plus the key line — the README's "the same key is printed
  in every release's notes" is now true by construction. the wall also
  refuses when the CHANGELOG has no section for the version, or no key is
  findable.
- doctor sees the drift a green check used to hide: a placement
  destination the book never recorded, holding content older than what
  ships, is named — this is how the live guard sat three releases old
  while `update` said "kept (yours)" and doctor said "placed files
  current", both honest about their own scope. a never-recorded copy that
  matches what ships is adopted into the book on sync.
- `sandbox reset` reaches those files: a short name resolves against the
  payload, and the book is not required — a destination init places is
  restorable on your word even when an older core placed it silently.
- a gate refusal exits 1: piping into `approve` still refuses in words,
  and now a script reading the exit status is told the truth too. the
  seventh body had this right; the regression retires.
- `make --close` over an empty diff says "attempted", never "confirmed" —
  the verdict word stops grading itself generously in exactly the place
  this system claims it does not.

## 8.2.2 — the stranger's first meeting, opened (2026-07-31)

the two pages a stranger reads first were rebuilt against what this body
actually does, and every claim on them was run before it was written.

- the README is re-derived under the ruled framing: it leads with what
  you leave a session with, pairs seven claims 1:1 with the command that
  opens each, and names `soul/` and `law/` as riding inside the seal.
  the paid-`claude` caveat moves above the clone line, and the reason
  main only ever holds a verifiable state is stated in public.
- `docs/START-HERE.md` walks one sitting end to end and finishes with
  the reader opening their own journal line — the receipt, not a
  promise about one. the old page claimed two strings the engine never
  printed; the whole walkthrough was dry-run in a throwaway workshop.
- a ship with no checks now says so in the tool's own voice: *"a ship
  with nothing under it is a costume"* — the better sentence moved from
  a nearly unreachable path to the one every stranger meets, and it
  still names its door.
- `recall` refuses a typo'd flag instead of searching it as text.
- three pins on the docs: line citations must resolve to a real refusal,
  the install block must name the bill before the clone and end in the
  health check, and the README's loud line is tested as behaviour —
  `land_all` gets four bad consents and must land nothing every time.

## 8.2.1 — the plugin tells the truth (2026-07-31)

the plugin's first live install — the never-met-a-live-session debt paid
out on the machine that shipped it, before any stranger's.

- the guard hook leaves the plugin (ruled): its command pointed one
  directory above the plugin root, a file no installed copy carries, and
  a missing guard reads as BLOCK — every write in every new session. the
  guard stays placement-delivered: `sandbox init` wires it into the
  workshop it protects, and sessions outside the workshop stay unfenced.
- the plugin's descriptions now name only what it ships: the voice.
- the release wall speaks all four moves — sign, commit the signature,
  tag, push — so the ceremony can never again be summarized one short.
- the cut-list grows from ten entries to twenty-four (the discovery
  format's closed list, minus this repo's one named exception) and the
  doc lint now reads README.md, which lived outside its walk.

## 8.2.0 — one soul, many projections (2026-07-31)

the instruction layer rebuilt from its foundation: what the machine is
told and what it believes can no longer drift apart unseen.

- `soul/` is born — the ten axioms with their anchors, the seven
  convictions with their organs and projection map, the voice, the
  partnership, and the eight bodies' lineage. public, sealed, tested.
- the workshop contract becomes the charter: 60 lines, identity and
  convictions instead of a rule list, placed by init as before.
- one output style, `across the desk`, ships in the plugin and lands in
  every workshop at init; `plain.md` retires with its silent
  keep-coding-instructions bug.
- the whole crew ships: six briefs, each its worker's entire world —
  role, scope, report shape, two convictions — pinned to the model its
  judgment needs (sonnet where literalism is the job, opus where taste is).
- the engine learns the layer: init places the style and writes the
  session voice (your own pick always wins) · `sandbox reset` resolves
  pristine copies from the real payload · the guard fences agent-memory
  at any depth — the ungated-memory lesson, closed at its third door ·
  `sandbox help` prints one honest line per verb.
- the layer is tested like code: 16 new tests hold the budgets, the
  banned words, the dead paths, the model pins, and the two hand-carried
  version numbers — one of which was already drifted when the pin first
  ran, which is the argument for the pin.
- the deny floor emits one Edit rule and heals workshops carrying the
  old four (the launch-warning fix, folded into this release).
- docs catch up: the wider-crew debt retires as done, README teaches
  both forms of make and points at the honest register.

## 8.1.2 — the fences learn from the move (2026-07-30)

everything here was found live, on the owner's own migration day.

- `sandbox release` — the ceremony's wall: refuses until the suite, verify,
  a fresh signature, and a committed tree all hold, then hands you the tag
  and push commands. born from the same miss twice.
- init prunes hooks pointing at gone paths — a moved workshop no longer
  leaves a dead guard blocking every session.
- import: a root living outside the old workshop stays a `root:`; only
  trees inside the old workshop move in. moved roots relocate by suffix.

## 8.1.1 — succession (2026-07-30)

- `sandbox import PATH` — a past body's workshop comes in whole: the
  journal byte-verbatim (the old genesis stays the genesis — one
  continuous self), a path-map so old receipts open at new addresses,
  chosen projects live with their checks (ratifications honestly void,
  one fresh k each), carts become builds, your own agents ride along.
  A lived-in workshop refuses to merge selves.
- `sandbox setup` — one shim, pointing at this copy.

## 8.1.0 — the constitution rides the body (2026-07-30)

- make grows its AI half: `sandbox make "intent"` runs the builder
  (SANDBOX_CLAUDE_CMD overrides; without one, the full prompt lands in the
  project for your own hands), diff computed either way.
- the catalog: index.json pins every app by hash; `app install --catalog`
  verifies the pin and says so; a catalog whose bytes disagree with its own
  index is named loudly. directory placements ('.../') let big apps declare
  one line instead of a thousand.
- the face's first tokens: one earned accent, only at a real terminal,
  never under NO_COLOR. the full design pass stays a named debt.

- the fifteen laws, ratified in sitting, now live in `law/` — one page
  each, clause text hash-pinned by the suite: amending a law means editing
  its pin in the same commit, and only the owner's pen amends.
- the crew ships: checker and challenger board every fresh instance at
  init, placed with provenance.
- the release chain is live: signed manifest, strict verify, the public
  key in the README and every release note.


## 8.0.0 — the eighth body (2026-07-30)

born release-ready. the whole system rebuilt on a constitution argued from
scratch (fifteen laws, ratified 2026-07-30), with the seam as its founding
addition: what ships belongs to everyone; what is the owner's stays the
owner's, held by mechanism.

- the record: append-only journal, torn lines scar and never kill, every
  event addressable as a receipt.
- the registry: a typed read over the record — projects, builds, apps,
  notes, rulings (law vs taste, newest word wins), checks, sessions.
- the gate, two speeds: the owner's keystroke lands everything durable;
  reversible acts may run now and confirm at the next arrival, snapshot
  kept, never auto-reverted over later work.
- verbs as declared action types: reads, writes, gate speed, emitted event
  — parity-linted against the code.
- the guard: the record walled, auto-memory routed to the staged-note
  path, cross-project writes fenced, the engine fenced from workshop
  sessions.
- placement provenance: updates refresh what you never touched, skip and
  NAME what you edited, remove pristine orphans, re-baseline convergent
  edits. `reset` returns a file to pristine on your word.
- update: version and migration high-water recorded in the workshop;
  skew named plainly; migrations numbered and idempotent; the rehearsal
  (workshop at N meets core N+1) runs in the suite.
- sharing: builds travel with checksums (scrubbed on the way out,
  hash-verified before your key on the way in, origin never launders);
  apps install with a compat gate and a placement allowlist enforced in
  code, and remove exactly what they placed.
- person-clean: no personal path or private term ships; publishing exports
  fresh trees that never carry git history.
- faces: a plain-spoken CLI and a self-contained living page.
