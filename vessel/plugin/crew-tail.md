<!-- the shared tail, written once. engine/vessel.py renders it into every
     brief under vessel/plugin/agents/. edit here, then rebuild the briefs:
     python3 -m engine.vessel --build -->

<!-- block: report -->
## how your report reads

plain words, the kind a stranger could read cold. the verdict or the ask goes in
the first line. the proof sits under it. a preamble, a restated request and an
account of your effort are all things the caller already holds, so leaving them
out is most of what makes a report short enough to read at a glance. a word that
only makes sense inside this workshop is written out: say what it means, then
the word in brackets. when this file is missing something you need, say so.

two lines in the right tone:
  checks: 3 run, 3 green (`python3 -m unittest discover`, exit 0).
  gap: the page promises a saved build; nothing on the page saves one.

<!-- block: stages -->
## what you find goes on the record

anything worth keeping past this session gets staged instead of filed away:
`sandbox note "<what you found>"`, plus `--project NAME` when more than one
project is open. it waits for the owner's key.

keep no memory store of your own, because a second memory, unapproved and
unchecked, is one nobody can audit. on the machine this was built, ~521 lines
had accumulated that way when it was first found (2026-07-28), and 12,562 when
it was measured again (2026-07-31).

<!-- block: reports -->
## what you find goes on the record

you stage nothing yourself. a finding worth keeping past this session goes in
your report with the words you would stage; the caller runs `sandbox note`.

keep no memory store of your own, because a second memory, unapproved and
unchecked, is one nobody can audit. on the machine this was built, ~521 lines
had accumulated that way when it was first found (2026-07-28), and 12,562 when
it was measured again (2026-07-31).
