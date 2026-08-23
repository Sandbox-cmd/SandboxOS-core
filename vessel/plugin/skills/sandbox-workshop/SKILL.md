---
name: sandbox-workshop
description: Operate Hameed's SandboxOS workshop (~/Sandbox) — the maker's loop with an honest record. Use whenever working inside ~/Sandbox or its projects, when the user mentions the workshop, the shelf, saved builds, the record, notes waiting for approval, shipping, or sandbox verbs, or when a session should capture corrections/decisions durably. Teaches the setup ceremony and where things live.
---

# sandbox-workshop — operating the maker's loop

SandboxOS is Hameed's local maker's operating system: projects under
`~/Sandbox/projects/`, a shelf of saved builds, and an append-only record
where a machine's draft stages and the owner's keystroke lands it. the tool
is the `sandbox` command — a shim at `~/.local/bin/sandbox` running the one
tree at `~/Sandbox/system`, whose `docs/MANUAL.md` carries a page per verb.

## the one canonical text
the charter is `~/Sandbox/CLAUDE.md` — placed and kept current by
`sandbox init`, and loaded automatically inside the workshop. it carries the
identity, the convictions, and the commands to reach for. follow it, because
a second copy of it here would be the one that goes stale. this skill carries
what it leaves out:

## the setup ceremony (no workshop yet? this is job one)
when `${SANDBOX_HOME:-$HOME/Sandbox}/.sandbox/journal.jsonl` is absent, offer
to set it up conversationally and run it yourself: ask where the workshop
lives → `./sandbox setup` + `sandbox init` → `sandbox doctor` → offer
`sandbox import PATH [--projects a,b,c]` to carry a prior workshop in → then
stop and hand him the one keystroke: `sandbox resume`, one `k`. staging is
yours; landing is his.

## quick reach (the details live in the charter and `sandbox help`)
`sandbox builds` before building what the shelf already holds —
`sandbox use NAME` copies a saved build onto a project, and `sandbox save
PATH` makes a new one. the plugin's Stop hook sweeps each turn for lines that
begin `finding:`, `ruling:`, or `correction:` and stages them, so a finding
survives the turn either way; staging it in the moment still reads better,
because you choose the words. old record lines may say channel, cart, or
bench — history's names for project and saved build, and this copy answers
only what `sandbox help` lists.

## the crew (placed at `~/Sandbox/.claude/agents/`, each brief its seat's
whole world — model and effort pinned in its frontmatter)
surveyor and checker (before new work · before any "done") · keeper (when a
project parks or ships) · voicer and producer (before anything a person reads
or lives in ships) · challenger (before a hard-to-reverse move). delegate at
those moments, and let none of them land: the key is the owner's.

## working on the tool itself
the tree is `~/Sandbox/system`, and the shim points at it. the covenant:
`python3 -m unittest discover -s engine/tests -t .` green → `./sandbox
verify` → `./sandbox seal` — and when files under `vessel/` changed,
`sandbox update` re-syncs the workshop's copies, skipping and naming the ones
you edited. what is open lives in `docs/OPEN.md`; the laws live under `law/`
(experience: 08-inhabited-surface, voice: 15-plain-first).
