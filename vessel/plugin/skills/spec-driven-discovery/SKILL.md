---
name: spec-driven-discovery
description: Hameed's ratified product-development format — from an idea or existing material to build-ready specs, a pull-based backlog, and a build running on checks. Acquire knowledge in parallel, frame with JTBD, diverge and converge on direction, collect owner rulings (interactive, or deferred when headless), write build + experience specs, draft per-part specs in parallel with a unification pass, adversarially challenge the specs, then backlog and build. Use whenever Hameed says "spec-driven discovery", "run the discovery format", "spec this like commerceos", "re-spec this", "let's discover then plan", "re-envision this", or whenever starting substantial work on a system that has prior material (docs, code, records, a live deployment) or needs a direction picked before building. Also use when he asks to "acquire the knowledge then plan" or wants a project plan with specs per part. Do not use for small single-file tasks, pure conversations, or work a single plan-mode plan covers — this is for systems with multiple parts or at least two material sources.
---

# spec-driven discovery — from idea to product

state: v2 — 2026-07-11, landed · receipt: the improvement note on the
discovery-format project's record · history at the end.
as of 2026-08-22 — v2 plus two landed amendments (below); the paths speak v8.

A working format proven on the CommerceOS re-spec and hardened on the
sandbox-site re-envision (both 2026-07-11). It moves from "an idea, or material
somewhere" to "a product being built without drift", keeping every decision the
owner's.

Nine movements, in order. Each produces something written to a file before the
next begins. A movement may shrink (see sizing) or be skipped only by saying so
out loud with the reason, because a skipped movement that nobody names is a
gap the next movement inherits blind. the order holds: jobs before parts, a
frame before a direction, rulings before a backlog (in headless, movement 4's
OPEN list with marked recommendations satisfies that last gate — the backlog
marks its [owner] items).

## the two modes

Name the run's mode at the start and write it as the first line of
`spec/inventory.md`; it governs every ruling gate.

- **interactive** — the owner is at the terminal. Collect rulings live at each
  gate (the interactive question tool — today AskUserQuestion — crisp options,
  trade-offs stated, recommendation marked and listed first). He converges from
  divergence sketches in seconds; show sketches, not essays.
- **headless** — the owner is away, or the run is autonomous. Never stall,
  never self-rule: write every owner decision as OPEN [owner] with a marked
  recommendation, proceed treating recommendations as provisional, and put the
  rulings-needed list at the top of `backlog.md`. A judge panel may proxy a
  convergence; the artifact must say a panel picked, not the owner. A headless
  run ends at movement 8: the build begins only on a frame and build-gating
  rulings that are RULED — this guards the recorded scar of three frame-level
  rejections in a row.

What RULED means — three roles, in order: the owner's word makes the ruling
(said in-session, captured verbatim); the staged note is its receipt; his
keystroke landing it makes it durable. Until the keystroke, the spec wears
RULED-pending-land. Outside the workshop, RULED = a dated entry in
DECISIONS.md. A recommendation alone is never RULED, and the machine can
never rule.

Inside ~/Sandbox: load the sandbox-workshop skill before movement 1. The four
terms this file leans on: **the record** (the append-only journal of what
happened), **staged** (machine-drafted, waiting for approval), **landed**
(approved by the owner's keystroke at a real terminal — nothing is permanent
before this), **ratified** (checks the owner approved as a project's ship gate).

## the laws (they outrank everything in this file)

These came from the owner's corrections. Each law carries its check — a law
you can't check is a vibe.

- **Plain words.** Coined vocabulary, philosophy and hype all fail the same
  test: every sentence is understood on first read. Check: run
  `python3 -m engine.voicelint spec/` for zero hits —
  the forbidden-phrases table in `soul/voice.md` is the one list, so amend
  that table rather than the check — plus judgment for freshly coined words
  a table cannot hold.
- **Holistic, both directions.** A mechanism designed around one past failure
  fits that failure and nothing else, so an old lesson arrives as
  *configuration* of a general mechanism rather than as its shape. Check: for
  every part that watches or evaluates, the spec names the opportunity it
  raises as well as the failure it guards.
- **Nothing stays a blackbox.** Check: every part's `## renders` names a
  surface a person actually looks at; "logs to a file nobody opens" fails.
- **Everything carries its proof.** Check: every claim in any spec is marked
  RULED / proposed / OPEN; every backlog item carries a runnable check; verify
  rendered, never files-exist — each `## checks` entry names the surface where
  its result is seen, and while nothing renders yet, the check is the command
  whose output a person reads.
- **Decisions are the owner's.** Surface them, recommend, encode once when
  ruled — per the modes above.
- **Scars are configuration.** Movement 1 reads the failure register. Check:
  each scar relevant to this system appears as a named check at the movement
  it guards — never as a new mechanism of its own.

## where files go

Root = the project's directory inside the workshop; its own root outside.

    spec/inventory.md      movement 1 — the honest inventory; first line names the mode
    spec/jtbd.md           movement 2 — the jobs file others cite; lens reports
                           (when they ran) sit in it as an appendix
    spec/frame/            movement 3 — the whole divergence record, incl. judge scores
    DECISIONS.md           movement 4 — dated rulings (outside the workshop; inside
                           it, rulings live on the record and specs wear RULED marks)
    spec/build.md          movement 5
    spec/experience.md     movement 5
    spec/parts/<name>.md   movement 6
    spec/challenge.md      movement 7 — findings and what they changed
    backlog.md             movement 8 — a headless run opens it with the
                           rulings-needed list
    FORMAT-NOTES.md        the format-learns capture, outside the workshop only

Record findings the moment they land — a staged note inside the workshop, a
dated line in the relevant spec file outside. Never batch them to the end.

## 1. acquire

Sweep everything that exists before reasoning anything twice.

- Fan out parallel read-only scouts (subagents), one per material source:
  docs/inherited context, each codebase, archives, the record (workshop only).
  Also read live systems directly (a store, a deployment, an engine — run its
  real commands); documents can't tell you their current state, and they lie
  about behavior.
- Each scout returns a structured knowledge map: what it is, decisions already
  made, real numbers, state/maturity, gaps. Demand verbatim quotes for
  decisions and numbers.
- The failure register is a first-class source: inside the workshop, the
  lessons and corrections on the record; outside, closed issues, reverts,
  post-mortems, rejected drafts. When none exists, write "no failure register
  — first scar starts it" in the inventory and move on.
- Chase pointers scouts surface (a path in a doc, a repo nobody mentioned) —
  the authoritative source is often one hop past the obvious one.
- Synthesize: one honest inventory (`spec/inventory.md`) + the lessons the
  material teaches. Name what's dead (abandoned prototypes) and what's salvage.

## 2. jobs (the JTBD lens)

The ratified reasoning frame. Do this before naming any part.

1. Name the **job executors** — people, not software. Agents, dashboards,
   pipelines are hired things, never job owners.
2. Write each executor's **main job** as one sentence: When I…, I want…,
   so I can…
3. Break it into **job steps**, each a row: when / I want / so I can +
   **measurable desired outcomes**. Example row, the grammar to copy:
   *when a build session ends | I want the receipt written without me writing
   it | so I can trust my own counts in a year → outcome: counts computed from
   the journal at render, never stored → hired: the record → layer: mechanism.*
4. Map every job row: job → hired solution → **layer**:
   - generic **mechanism** (the reusable system — would instance #2 take it
     unchanged?)
   - instance **config + data** (tuned or supplied per instance)
   - **rented rail** (bought, not built)
5. Derive parts from jobs. A part that cannot name its job row is cut.

When the system will face strangers (intended exposure, not just current — a
public surface, a product with real users), run parallel situational lenses
first — first contact, evaluation, adoption, return, culture; situations, not
personas — and merge them into the one jobs table, keeping the lens reports as
the jobs file's appendix. Keep `spec/jtbd.md` as the foundation others cite.

## 3. frame (diverge, then converge)

Fires when positioning, value proposition, or creative direction is not yet
ruled. When it already is (CommerceOS was), skip it out loud: "frame skipped —
direction ruled on <date>".

- Generate N candidates from genuinely distinct seed angles — N from the
  problem, not habit; 3–5 covers most systems; one candidate may be "evolve
  the incumbent" as the control. A candidate is a sketch: one page — the idea
  in two sentences, what the person does in the first minute, and the
  axis-diff from the incumbent (subject / structure / register / look).
- Converge by mode. Interactive: show the owner the sketches; he picks in
  seconds. Headless: an independent judge panel — three judges, no shared
  context, each scoring every candidate on the named criteria: job fit, the
  laws, checkability of claims, energy (power, not austerity — the recorded
  bar). Scores and rationales land in `spec/frame/`; the winner ships
  as a recommendation with the pick itself OPEN [owner] at the top of the
  rulings-needed list.
- Keep the entire divergence record in `spec/frame/` — losers carry graftable
  ideas, and the record is what lets the owner overrule without re-running.

Why this movement exists: the frame is the recorded failure point — the site
arc took three frame-level rejections in a row while execution kept improving.
One divergence pass is cheaper than one rebuild.

## 4. rulings

Collect every decision only the owner can make, per the modes. Encode each
ruling once, immediately: update the spec, mark it RULED with the date (or
RULED-pending-land inside the workshop), record it where rulings live. What
isn't ruled stays visibly OPEN [owner] or OPEN [design] with a proposal on
file — never silently resolved.

## 5. two specs

From the jobs table, write two specs that reference it:

- **build spec** (`spec/build.md`) — what to build, where it lives, what each
  part solves; parts overview with mechanism-vs-config marked; salvage posture
  toward prior work; slices (each proves a job live, each carries a check);
  standing constraints.
- **experience spec** (`spec/experience.md`) — the surfaces where each job
  happens, for every person who touches the system; interaction grammar;
  principles; what it is NOT. Only where a person actually touches it. Every
  experience principle names its check — a principle no review can fail is
  decoration.

In a headless run, a spec built on a provisional frame opens with one line:
"assumes OPEN ruling <id>" — the assumption rides visibly or not at all.

## 6. part specs, in parallel

One deep spec per part, drafted by parallel subagents, unified by the
orchestrator alone.

Every drafter gets: the jobs file + parent specs to read, the named real
sources for its part (prior specs, code to mine read-only), the rulings from
movement 4 (RULED and RULED-pending-land) plus the OPEN list, the laws, and
this exact template:

    # part: <name>
    serves: <job rows>
    state: draft v1 — <date>. OPEN items marked.
    ## purpose
    ## owns          (data/objects it is sole writer of)
    ## exposes       (what other parts/surfaces consume)
    ## consumes      (what it needs from others)
    ## mechanism vs config
    ## behavior      (numbered core flows, concrete)
    ## renders       (its self-report — the no-blackbox contract)
    ## checks        (runnable, meaningful — the proof)
    ## v0 salvage    (what to mine from prior work, what to leave behind)
    ## open          (OPEN [owner] / OPEN [design], each with a proposal)

Then the **unification pass**, never skipped, by the orchestrator alone:
- voice sweep (`python3 -m engine.voicelint spec/`), template compliance
- seam check: ownership conflicts (two writers of one thing), circular or
  missing cross-references, contradictions with the parent specs
- fold refinements back UP into the parent spec so no file disagrees
- slot newly-uncovered decisions into the backlog or the OPEN lists

State the honest residual: parallel drafters share no context; the owner's
cold read is the real unification check.

## 7. challenge (adversarial verification)

Before any backlog, independent challengers attack the specs, each from a
named lens:

- **truth** — every claim tested against the live system: run the commands;
  documents lie, engines don't. Every named component, count, and behavior
  either verified or marked proposed.
- **the cold read** — a stranger (or the real user) walks the specced
  experience and names where they stall, bounce, or need a manual.
- **the scars** — the failure register from movement 1, applied check by check.

Findings: [blocker / major / minor] + cite the spec's own text + the concrete
fix. A repair pass applies them; `spec/challenge.md` records what changed.
Sizing shrinks this to one challenger, and the floor is one. Why it always
runs: on the sandbox-site re-spec this movement caught build-breaking errors
— a chapter specced against engine behavior that was never built, an invented
count, and a simulated keypress on a page whose whole claim was that a
keypress cannot be faked.

## 8. backlog

One pull-based program backlog (`backlog.md`), lanes parallel where
dependencies allow.

- Every item: id · title · serves (job row) · size (S/M/L) · deps · check.
- **Pull rules written into the file:** a row pulls once it carries its job
  row and its check · pulling opens a tracked unit of work (a make session
  inside the workshop; a branch or PR outside); done means the check ran ·
  a discovery slots in as its own item, because a side-quest inside open work
  is how a lane loses its estimate · a discovery contradicting a spec
  updates the spec first · WIP cap (default 3; the owner may re-rule it) ·
  owner-gated items marked [owner], parked not blocking.
- Name the strategic pull order and which lanes run in parallel now.
- Keep an owner-attention list, value-ordered, calendar items flagged.

Keeping it true (added 2026-07-12): the backlog is a mirror of the record and
drifts silently — finished work keeps reading as "future", ruled decisions as
"open". The operational re-sync is the `backlog-sync` skill: it reads the
record since the backlog's "as of" stamp, stages the diff (done / re-scope /
add-with-job-row-and-check / cut-with-reason), refreshes the stamp, and stages
a note — never landing. Run it after rulings land, after a `sandbox make
--close`, when new work is picked up, or when `sandbox doctor` flags the
backlog past its stamp. It carries movement 8's pull rules and the return
loop's walk-the-change-downhill into a repeatable pass.

## 9. build, on the workshop loop

The format ends where the workshop begins; it does not reinvent the build.
Inside ~/Sandbox: each backlog item pulls into a work session (`sandbox make
--open` … `--close`), its check joins the project's `## checks`, done means
the check ran, and ships happen on ratified green with the owner's keystroke.
Outside the workshop: the same shape with the project's own gate — CI, review,
whatever is real — named in `backlog.md`; if no gate exists, creating one is
the first backlog item.

## the return loop

The format is iterative by design: the owner reads cold, corrections are
captured verbatim the moment they land, specs update before code, items slot
in and out. When a movement's output changes (a ruling reverses, a job row is
cut), walk the change downhill: jobs → frame → specs → parts → backlog. What
the owner reads on return, in order: the rulings-needed list (top of
`backlog.md`), then `spec/challenge.md`'s what-changed, then the backlog's
owner-attention list.

## the format learns

The format itself is under its own law — it grows by use, with receipts.

- During any run, friction or insight about the format is staged the moment
  it shows: `sandbox note "format: <movement>: <learning> [run: <project>]"`.
  Outside the workshop: a dated line in `FORMAT-NOTES.md` at the project root.
- Recurring friction becomes `sandbox note "improvement: format: <what
  recurs> -> <proposed amendment text>"`.
- How this file changes — two legal paths, nothing else:
  1. **Ruled in-session:** the owner said yes to the amendment in the session.
     Apply it at once — append a dated amendment section (`## amendment:
     <name> (YYYY-MM-DD, owner-ruled, supersedes on conflict)`), set the state
     line to RULED-pending-land, stage the improvement note as the receipt.
     When the note lands, drop the pending mark and stage `format: amendment
     applied: <name>`. If the owner refuses the note, revert the file and say
     so. (voice.md's amendments were applied exactly this way.)
  2. **Proposed only:** nobody ruled. The improvement note waits; this file
     does not change until the owner's keystroke lands it.
  The machine alone never amends. Outside the workshop, the owner's dated OK
  line in `FORMAT-NOTES.md` is the ruling.
- Satisfaction is recorded as the owner's verbatim words about the movement
  that felt off — never a score nobody measured. Absence of a note is not a
  claim of satisfaction.
- When amendments pile up, a fold pass (prompted by the keeper, the workshop's
  curator agent) rewrites them into the body; the history block keeps lineage.
- The `discovery-format` project is the home: cross-file purely-format notes
  there; the keeper checks this file's state line against the latest landed
  `format:` note and flags drift. The state line is honesty, not enforcement —
  a fork between this file and the record is found by reading, so read.
- Known-open: 2–3 eval prompts for the format (so amendments can be
  regression-checked, not vibed) — next amendment candidate.

## sizing it

The full nine movements suit a system with multiple parts and real prior
material. For something smaller, shrink honestly rather than skipping kinds
of thinking: one scout instead of many; jobs as one table; frame as two
candidates and the owner's pick (or skipped out loud when direction is truly
ruled); build + experience as one file; parts as sections of the build spec;
challenge as one truth pass that runs the real commands; the backlog as a
checklist with checks. The order and the laws stay.

Worked example — a two-part CLI tool: one scout reads the repo and its issues;
jobs is one table with four rows; frame is skipped out loud (the direction is
the CLI itself); three rulings collected in one question; one spec file; two
part sections; one challenger runs every documented command against the
binary; the backlog is nine checklist items, each with its check.

## amendment: the experience build (2026-07-18, owner-ruled, supersedes on conflict)

state: landed — the owner said yes in-session on the portfolio-analyst
run; its improvement note now sits on the landed record (pending mark
dropped 2026-07-21).

Born from a recorded failure: on the portfolio-analyst run, the
engineering surfaces (data-verification pages) were styled and presented
as the product, while the experience spec sat unbuilt. The owner's
words: "you just reskined what was clearly just an engineering debug
html... What we did was foundation and engineering and infra not the
product... This needs its own spec."

The amendment, three parts:

1. **The experience build is its own lane.** Movement 8's backlog
   separates product slices from infrastructure slices. An infra slice
   may carry a debug surface to verify data; that surface is an
   instrument, never the product, and styling it never satisfies a
   product slice. The product slices build the experience spec's actual
   surfaces, with their own checks.
2. **The product cold-read gate.** No user-facing surface ships without
   a cold read against the experience spec and the frame — the same gate
   discipline movement 7 gives correctness, applied to product. Inside
   the workshop the producer agent (the crew's product pass) runs it;
   outside, a named reviewer does.
3. **The product spec.** When the experience spec's surfaces are
   nontrivial (an app, a site — anything a person lives in), movement 6
   includes a product part-spec: information architecture, the surfaces
   and their states, interaction grammar made concrete, the technical
   foundation the experience needs (not what the infra happens to
   offer), drawing on whatever design research the run gathered.

## amendment: the method — find · show · rule · keep (2026-07-22, owner-landed fold, replaces the braid)

state: landed — the fold proposal landed on the discovery-format project's
record by the owner's keystroke; the braid amendment is retired and its
lessons live here in plain words. Full text with the run's receipts:
`projects/discovery-format/method.html`.

Design work inside any run is four ordinary verbs, in order. Each was
earned by a recorded failure on the sandbox-site run (2026-07-21), where
three build-waves (22 finished pages) produced no decision and four cheap
artifacts produced all of them.

- **find** — before making anything: what is already true inside (the
  record, the ratified law, the owner's own words on disk — the run's
  worst miss was inventing principles while `soul/ground-truth.md` sat
  unread) and outside (real work from the world, fetched and link-checked
  into `projects/design-system/taste/references.md`). Self-reference is
  the mode-collapse center; gather before inventing.
  **And read the record as chronology, not scripture** (owner-ruled
  2026-07-22): a landed entry is never taken at face value — extract the
  intent, desire, and principle beneath it and how the direction moved
  entry to entry, and form an independent view from that whole arc. A
  landed decision is the best answer *at its time*, held revisitable:
  when intent has outgrown it, propose the supersession as a new note —
  the record keeps both, the owner's key still decides. Solutions stay
  unfixed; value, intent, and principles are the core; ideating is
  discovering outcomes and experimenting, then settling on what matches
  best. A landed k blindly followed is an empty fact.
  **The state test — mechanical, before building on any prior artifact**
  (added after the failure it names, 2026-07-22): classify what you are
  standing on — a trial (made while exploring; includes anything from a
  round whose launch note says ideation/exploration/study), an
  an interpretation (a corrected reading of the owner's thought — it fixes
  a misreading rather than closing a question), or a ruled direction (a
  convergence event exists: the owner's pick, in his words, on the
  record). **Building on anything requires finding its convergence
  event. No pick found = it is a trial = material for divergence, never
  a foundation.** The failure that minted this: an ideation round's
  corrected trial got promoted to "the standing motif" by the reader,
  written into a backlog row as law, and a full surface was built on it
  — minutes after the chronology ruling landed. "Correct interpretation"
  is not "chosen direction"; the words are different because the states
  are.
- **show** — the cheapest artifact that makes a decision possible, and a
  gate at every step: structure wireframes (B&W, ugly on purpose) before
  register boards, boards before comps, comps before builds. Structure
  diverges before costume. Expensive rounds are narrow rounds.
- **rule** — boards, not essays; the owner picks by eye in seconds. The
  correction is the artifact: capture it verbatim before continuing.
  A mood pick is a palette, never a fence; after a liked round, go
  deeper into it, not sideways into new concepts.
- **keep** — where the next run will actually open it: taste rulings and
  register libraries to the design-system project (TASTE.md,
  references.md), format learnings to the format's home, findings to the
  run's project. Where a ruling can become a runnable check, make it one
  — the site run turned its laws into two lint suites, and they caught
  drift the same day.

The five tests, cheap enough to apply to every line:
1. Could a different feature serve this principle? (If not, it is a
   mechanism wearing a belief's costume.)
2. Does this line name a consequence? (Forces nothing → cut it.)
3. Did I find this or invent it? (No source is an instruction to look.)
4. Would a stranger understand it on first read? (Coined vocabulary
   hides absent thinking, from you first.)
5. Is this cheap enough to throw away? (Cost buys attachment; attachment
   kills real choice.)

Verification law, learned twice: verify rendered was never enough — a
green screenshot can lie when fallbacks are plausible. Verify the assets
loaded (computed styles, a request log) and let a lint fail when a
linked resource is unreachable. And the builder never edits the check it
disagrees with — it reports the disagreement.

Retired vocabulary (do not reintroduce): the braid, feel rows, registers,
the chord, the tier ladder, lettered movements, forced-distinct
preregistered divergence. Say the plain thing or nothing.

## history

- **v1 — 2026-07-11.** Born from the CommerceOS re-spec: seven movements
  (acquire, jobs, rulings, two directions — the build + experience specs
  together — part specs, backlog, return loop).
- **v2 — 2026-07-11.** Hardened by the sandbox-site re-envision run, a
  skill-craft audit, and two adversarial verification passes on this file
  itself. Added: the two modes (interactive-only rulings was a blocker —
  headless runs stalled or self-ruled; headless now ends at movement 8),
  RULED defined by its three roles, the file map, movement 3 frame
  (divergence/convergence — the re-envision run proved it; the skill had no
  front for idea-stage work), movement 7 challenge (its adversarial pass
  caught build-breaking spec errors), movement 9 build-on-the-workshop-loop
  (idea to product, not idea to backlog), the format-learns loop with the
  two legal amendment paths, checks on every law, the one forbidden-phrases
  table, the example job row, the worked sizing example. Removed: CommerceOS
  residue ("one scout instead of eight").
