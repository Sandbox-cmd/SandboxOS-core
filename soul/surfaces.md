# surfaces — one voice, a budget per room

lineage: written new 2026-08-22 for the second wave, from voice.md's
positions, gov.uk's error-message rules, clig's error section, voice.md
(efeoncepro)'s surfaces[] and mailchimp's voice-vs-tone frame. taste
stratum: dated positions, newest word wins, no pin. rows 22 to 30 were
added 2026-08-22 for 9.0's new surfaces, from the sandbox-next specs.

**row 0 — clear beats voice.** every row below is the same voice at a
budget; where character and clarity pull apart, clarity wins (law 15).

| # | surface | max words | case | first person | opens with | avoid — and why | exit | exemplar |
|---|---|---|---|---|---|---|---|---|
| 1 | status line — a render of state | 14 | lowercase | no: it reports state, not an act | the count or the project | a count with nothing to do about it — a number nobody can act on is noise (clig) | 0 | `2 drafts wait on your key — sandbox approve` |
| 2 | done line — a verb's success | 18 | lowercase | yes: the machine's own act | the past-tense verb of the act | "confirmed" or "verified" over an empty result — the word would grade itself (law 1; `make.py:130-132`) | 0 | `i kept geardoor on the shelf — reuse it: sandbox use geardoor` |
| 3a | refusal, usage — the verb was mistyped | 16 | lowercase | no | the verb's name | an apology — it does not help fix the call (gov.uk); the fix is the line | 2 | `note needs words: sandbox note "what you found"` |
| 3b | refusal, gate — the act needs a hand | 22 | lowercase | no: the gate is stating what it needs | the act that is waiting | "please" or "invalid" — one implies a choice, the other names no cause (gov.uk); say what it needs | 1 | `landing needs your k at a real terminal` |
| 3c | refusal, guard — a write turned back | 24 | lowercase | yes, once: "i" is the one that refused | what is refused, then the door | an insider noun (wall, pen, room) — the reader is mid-mistake and a word they must decode is a second mistake | — (the harness shows the reason) | `i won't write to the record — it takes writes only through your key. stage this instead: sandbox note` |
| 4 | doctor check line | 4 + 14 | lowercase label; `LOOK` is the one caps word here — doctor's accent, kept by ruling (gate 3, 2026-08-22) | no | the check's name as a noun phrase | a red line without the command that fixes it — a diagnosis with no door is a worry (clig §errors) | 0 / 1 | `LOOK  placed files current       you edited CLAUDE.md; updates skip it until: sandbox reset CLAUDE.md` |
| 5 | help line — one verb | 12 | lowercase | no | the verb name, then an active verb | the write scopes as the description — `writes: workshop, state` is a lint fact; the person asked what the verb does for them | 0 | `note       stages a finding for your approval · needs your k` |
| 6a | note shape — the staging message | 14 | lowercase | yes | the disposition | "submitted" or "queued" — service words for a desk that is yours | 0 | `i staged it — it waits for your key: sandbox approve` |
| 6b | note shape — the body that lands | 40 | lowercase; the owner's words verbatim, typo and all | no (open 2) | the class word, then the fact | a paraphrase of the owner's correction — the record is permanent and a bad shape is forever (propagation.md) | — | `make: core: help renders each verb's blurb before its gate word` |
| 6c | note shape — the CANON.md line | 1 line | lowercase after the brackets | no | `[ink] [origin]` | an ink the writer chose — ink is computed at landing (`desk.py:21-34`) | — | `- [receipted] [machine] make: core: help renders each verb's blurb before its gate word` |
| 7 | report block — init, import, update, share | 16 per line | lowercase | yes, for the act; no, for what the person must do | the verb of the act | ALL-CAPS alarm words — `READ-BACK FAILED` shouts what the exit code already says (ruling 2) | 0 / 1 | `i placed 8 files and wired the guard; the read-back holds. ready.` |
| 8 | PROJECT.md + CANON.md header | 1 line per field | lowercase keys | no | the field name | a placeholder goal — a contract with no goal is a costume (`ship.py:82`) | — | `goal: the owner's sentence, verbatim` · `*projected from the record — edits here are overwritten at the next approval.*` |
| 9 | BUILD.md card | 1 line per field | lowercase keys | no | the field name | an origin that launders (`shelf.py:7-9`) — whose hand pressed it is the card's whole point | — | `origin: your hand` · `used on geardoor 2026-08-22` |
| 10 | CHARTER.md (the playground) | 20 | lowercase | no | the room's name | a gate or a count — the room exists so trying is free (law 04) | — | `free ground. nothing here is counted, cited, or shipped — try things.` |
| 11 | PROMPT.md — retired in 9.0: `make` rides the session (M1); the charter's close is the one text a builder reads | 0 | — | — | — | — | — | — |
| 12 | the record as a page — `export --html`, which `page` now runs | 14 per line | lowercase, headings included | no | the heading noun | a claim that the page is live — it is a file written once, so a heading in the present tense promises a mirror nobody is keeping (R8) | — | `this is a file — opening it leaves nothing on the record` |
| 13 | release ceremony block | 16 per line | lowercase; the commands verbatim | yes, for the two moves the wall ran; no, for the owner's three | a numbered move verb | claiming a move it did not make — tag, push and publish are the owner's hands (`integrity.py:125-126`) | 0 / 1 | `i verified moves 1 and 2; 3 to 5 are your hands:` |
| 14 | changelog entry + release notes | 60 per bullet | lowercase | no: the release speaks of the tool | the thing that changed, then what it does now | a selling adjective — the cut-list, and a stranger reads the notes on GitHub before the tool | — | `- sandbox help reads as sentences: each verb says what it does before what it needs.` |
| 15 | commit subject | 10 (≤ 60 chars) | lowercase; no period | no | `scope:` then a verb phrase | "update", "fix", "wip" — a subject that names no change is a line nobody can open in a year | — | `help: each verb says what it does before what it needs` |
| 16 | plugin + marketplace description | 20 | lowercase after the name | no | the product name, then what is installed | "voice" with no noun — a stranger in the picker does not know what the workshop is | — | `Sandbox OS — one output style and six crew briefs for Claude Code, versioned with the core` |
| 17 | doc sentence | 30 | lowercase | "you" yes; "i" no | the subject of the claim | a claim without its command — the README's rule for itself (`README.md:8`) | — | `run it; the line you should see is under it, and what to do if you see something else.` |
| 18 | reply | 25 for the first line | lowercase | yes | the outcome or the ask | a preamble — the answer is the first line (`across-the-desk.md:19-20`) | — | `the lint is green; one thing to decide — keep FAIL as the one loud word, or lowercase it?` |
| 19 | a brief's `## output` | the format's own lines | lowercase labels | no: a format, not a conversation | the label | prose where a format was given — the caller parses, it does not read | — | `checks: 3 run, 3 green — python3 -m unittest discover, exit 0.` |
| 20 | a subagent's report | 25 for the first line | lowercase | sparingly: "i ran", "i could not run" | the verdict or the ask | an account of its own effort — the caller relays the finding, not the work (`checker.md:63-65`) | — | `gap: the page promises a saved build; nothing on the page saves one.` |
| 21 | the statusline | 8 per line | lowercase; the `DRAFTS` pill keeps its caps — the die-cut is its shape, kept by ruling (gate 3, 2026-08-22) | no | the count or the alert | a pill that shows when nothing is needed — the loud line is earned once (voice.md) | — | `2 DRAFTS ▏ context 88% — wrap up soon` |
| 22 | the SessionStart needs line | 30 | lowercase | no: it reports what waits, not an act | the count of things that need you | a door the hook could walk through itself — the session shows, the verb lands, and no hook ever lands (experience §4.1) | — | `two things need you — 1 draft (finding: the scrub refuses its own card) waits on your k · commerceos make ADJUDICATED1 open 21 d.` |
| 23 | the Stop sweep's one line | 8 | lowercase | no: the sweep counts; it judges nothing | the count of what it staged | "saved" or "recorded" — a sweep stages, and what lands is the owner's key | — | `3 findings staged — sandbox drafts` |
| 24 | `sandbox vessel` — the plugin read back | 12 per line | lowercase labels; doctor's three verdict words | no: it reports what is wired | the label, one word | `ok` on a fence it could not read — an unproven fence is `could not prove`, and saying otherwise is the 07-31 scar again | 0 | `lands    nothing. the key is yours.` |
| 25 | the export and page footer | 12 | lowercase | no: the file speaks about itself | what the thing is | a live-mirror claim — the file is a render, and opening it writes nothing (R8) | — | `this is a file — opening it leaves nothing on the record` |
| 26 | `fetch` — the source line | 30 | lowercase; `UNVERIFIED` is the fourth signal word (R23, 2026-08-23) | no: it states the card's provenance, not the machine's act | `source:` | a verdict the signature cannot carry — a hash proves bytes, and only a key proves a hand | 0 | `source: UNVERIFIED — no signature on this card. you are trusting the shelf you fetched from, not a key. it still lands on your k.` · `source: signed by RWSS… — matches the key you expected` |
| 27 | `approve` — the shown block and its key prompt | 16 per line | lowercase | no: the pile speaks for itself; the landing line after the key is the machine's act | the count of what is about to land | a count with nothing shown behind it — the 07-28 scar landed 34 when 10 were on the screen | 0 | `shown: 3f9a1c4e   press k to land this one · any other key cancels` · `landed 1 (shown 3f9a1c4e)` |
| 28 | `ship` — the ratified digest line | 14 | lowercase | no: the ratification is the owner's key, not the machine's act | `ratified`, the verb of what the key did | shipping without it — the digest names the exact checks the key was on, and it was computed and dropped until 9.0 | 0 | `ratified — your k is on these exact checks (<digest>)` |
| 29 | doctor's legend line | 10 | lowercase; `LOOK` by row 4's exemption | no: it defines the marks | `ok`, the first mark it glosses | a mark with no gloss — a stranger reads `?` as a fault rather than a gap in what doctor can see | 0 | `ok = proved · LOOK = needs you · ? = could not read` |
| 30 | `make --close` on red — the refusal | 20 | lowercase; `FAIL` quotes the check line's own mark | no: the checks refused, and the make stays open | the count of red checks | an `--anyway` door — a close over a red check is a claim the check contradicts (R11) | 1 | `2 red — no close: FAIL <check line>. fix them, then: sandbox make --close` |

rows 22 to 30 are **9.0, proposed** — written 2026-08-22 from
`sandbox-next`'s experience spec and its gate, doctor-status, export-page,
shelf, vessel-plugin and make-ship parts, for the surfaces 9.0 adds. rows 1
to 21 carry the second wave's cold read; these nine do not yet, and the
owner's cold read is what closes them.

how the columns are read: max words is a ceiling the lint counts; case is
lowercase-first unless the cell says otherwise, and FAIL is the one word
allowed in caps (ruled 2026-08-22) beside its two ruled exemptions, doctor's
LOOK and the statusline's DRAFTS (gate 3, 2026-08-22); first person is "i"
and only where the cell allows; the opening verb is checked as a smell, not
a gate; the avoid cell is a forbidden move with its reason, and the lint
holds the mechanical half (please / sorry / invalid in a refusal, caps
outside FAIL, a cut word anywhere); the exit code is checked at the verb;
the exemplar must pass its own row.

open, on this page: the list is empty. the one item it carried was ruled:

1. **`UNVERIFIED` in fetch's source line** (row 26) — RULED R23 (owner,
   2026-08-23): a fourth signal word beside FAIL, LOOK, DRAFTS, because it
   marks a card without a signature, and the reader is about to trust it. `engine/voicelint.py` `CAPS_ALLOWED` carries the four.
