# Sandbox OS

a terminal workshop for the things you build with an AI. the machine drafts;
your keypress decides what the record keeps. what you leave a session with is
not a transcript — it is a project on your disk, the checks it has to pass,
and an append-only record of what actually happened.

every claim on this page names the command that opens it. run them in any
order. nothing here asks you to take its word.

## open any of it

| the claim | open it |
|---|---|
| every verb says what it writes, and whether it needs your key, before you type it | `./sandbox help` |
| nothing durable lands without your keypress at a real terminal | `echo k \| ./sandbox approve` — it refuses, and says why |
| a ship happens only when your project's own checks pass | `./sandbox ship` with no checks in PROJECT.md |
| what got built is measured off your files, never taken from the model's word | `./sandbox make --close` prints the diff it computed, not the summary it was handed |
| every count is computed the moment it is shown | any number on a CANON page — nothing stores it, so nothing can forge it |
| the laws ride inside the seal, not beside it | `./sandbox verify` — fifteen files in `law/`, five in `soul/` |
| no dependencies, no network | `grep -rhoE "^(import\|from) [a-z_]+" engine/*.py \| sort -u` |

> ### A PIPE CANNOT APPROVE ANYTHING.

not a policy you can switch off — the shape of the thing. try it before you
install anything: `echo k | ./sandbox approve` refuses every time, and the
refusal itself lives at `engine/desk.py`, line 124. read it there before you
believe it here.

## get it running

you need a terminal, macOS or Linux, and python 3.9 or newer — the health
check grades that one itself. one thing here costs money and it is not this
repo: the `make` verb shells out to the `claude` command, so building with an
AI wants a Claude subscription. every other verb runs with the network off.

```
git clone https://github.com/Sandbox-cmd/SandboxOS-core
cd SandboxOS-core
./sandbox init      # your workshop at ~/Sandbox — SANDBOX_HOME moves it
./sandbox doctor    # the health check names anything missing, with its fix
```

then the first project:

```
sandbox project new hello "try this thing out"
sandbox status
```

`docs/START-HERE.md` walks one sitting end to end and finishes with your own
receipt open in an editor. `docs/MANUAL.md` carries a page per verb.
`docs/OPEN.md` says plainly what
this copy does not do yet — read that one before you trust anything here you
have not run.

## a session, end to end

- **arrive** — `sandbox resume`. one `k` approves whatever waited for you.
- **look** — `sandbox status`.
- **work** — `sandbox project on NAME`, then `sandbox make "intent"`, or
  `--open` … `--close` around something longer.
- **capture** — `sandbox note "..."` the moment a finding surfaces. it waits
  on your key; nothing gets written behind your back.
- **remember** — `sandbox recall QUERY`. when the record has nothing it says
  so, rather than guessing.
- **finish** — put your checks in PROJECT.md, then `sandbox ship`.
- **keep and swap** — `sandbox save PATH` puts a reusable build on your
  shelf. github.com/Sandbox-cmd/SandboxOS is where people trade them, with
  checksums on the cards and your key still the gate.

`sandbox help` names all of them, each with what it touches.

## what it will not do

- no account, no server, no telemetry, no network in any default path.
- one bill, and it is not to us — `make` shells out to `claude`.
- macOS and Linux, at a real terminal. a pipe cannot approve anything, ever.
- one person's machine. this is not a team tool.
- it will not overwrite what you edited. updates skip your changed files and
  name them; `sandbox reset PATH` returns one to pristine.
- it will not grade its own work. anything on the record wears `[claimed]`
  until something else checks it.

## what it runs under

`law/` holds fifteen laws, one file each. `soul/` holds the five pages this
workshop's character is written on. they are not notes about the code — they
travel inside the seal with it, so touching one moves the manifest:

```
python3 -m unittest discover -s engine/tests -t .   # the suite, stdlib only
./sandbox verify                                    # sha256 against the manifest
```

`verify` proves the copy changed, not who changed it. releases are signed —
for the stronger check, hand it the release key:

```
export SANDBOX_MINISIGN_PUBKEY=RWSSaKTVM7ywEE8f/jL16NcRhOFR1sAtIOd2hAD/ziMRscYAlaGxw+9j
./sandbox verify
```

the same key is printed in every release's notes. if this file and the notes
ever disagree, trust neither and ask.

you install by cloning and you update by pulling, which means you track
`main`. so main only ever moves to a state that verifies against that key:
work happens on branches, and main moves once per release. that rule exists
because this page told you to pull.

## your workshop is yours

`~/Sandbox`, or wherever `SANDBOX_HOME` points, holds your projects, your
builds, your apps, and the record. back it up by copying the folder. this
clone is disposable; that folder never is.

when something looks wrong: `sandbox doctor`, then `sandbox drafts`. every
wall in here names its door.

## license

FSL-1.1-Apache-2.0 — free for everything except competing with the software,
and it converts to Apache 2.0 two years after each release.
