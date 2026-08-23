# sandbox-os — the plugin

one installable unit that makes a Claude Code session the workshop's face.
it ships four hooks, six crew briefs, three skills, one output style, and two
commands, and its version is the core's: the tree it sits in is the tool it
shells.

## what it does

- **at session start** it prints one sentence — what needs the owner, oldest
  first — and opens a sitting on the record.
- **before a write or a shell command** the guard turns back what it can
  prove from the event: a write into the record's directory, a write into the
  host's own memory files, a write into another project's directory, a write
  into the tool's own tree. a shell command is read for write intent, so
  `cat`, `grep` and `git log` over the record all pass and a redirect into it
  does not. anything it cannot read, it lets through.
- **at the end of a turn** the sweep reads the transcript for lines that begin
  `finding:`, `ruling:`, or `correction:`, drops what is already waiting, and
  stages the rest.
- **at session end** it closes the sitting and reports how many times each
  crew seat was called.

## what it never does

it lands nothing. every durable line it causes is written by a `sandbox` verb
it shells to, and every one of those waits for a keystroke at the owner's own
terminal. the hooks mint one op — `session`, open and close — and a test runs
each hook against a throwaway workshop to prove that is all they mint.

## install

    /plugin marketplace add ~/Sandbox/system && /plugin install sandbox-os

`sandbox init` writes the same entry for you: the marketplace is the core's
own directory, and the plugin is the `./vessel/plugin` inside it, so the
plugin follows the tree the core is in.

two facts about the entry, from the host's own docs. a marketplace source is
one of github, git, url, file, directory or settings — `command` belongs to a
plugin inside a marketplace and was wired here by mistake until 9.0, where
the host dropped it, and the plugin did not load. and a plugin a marketplace
gives as a `command` in link mode loads only after the person accepts the
exact command string once at an interactive terminal, and never at all in a
session started inside the directory that command prints.
