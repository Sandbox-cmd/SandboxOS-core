# Sandbox OS

a maker's operating system for your own machine. you don't chat with it —
you build on it, and it keeps an honest record of what you built while your
hands stay busy.

what that means in practice:

- **projects** — one directory per thing you're making, each with a goal,
  its checks, and its own local git history.
- **the record** — an append-only history that fills as a side effect of
  working. nothing durable lands without your keystroke; the machine
  drafts, you approve.
- **builds and apps** — save reusable pieces on your shelf, share them as
  files with checksums, install add-ons that declare exactly what they
  place and remove exactly that.
- **updates that respect you** — the system updates from its repo; your
  workshop, your projects, and anything you edited are never overwritten.
  files you changed are skipped and named, never clobbered.
- **local first** — plain text on your own disk, no server, no account, no
  telemetry, no network in any default path. the one optional bill is a
  Claude subscription, for the AI-assisted building.

## get it running

you need a terminal, macOS or Linux, and python 3.9+. nothing else.

```
git clone https://github.com/Sandbox-cmd/SandboxOS-core
cd SandboxOS-core
./sandbox init      # opens your workshop at ~/Sandbox (SANDBOX_HOME moves it)
./sandbox doctor    # the health check names anything missing
```

then your first project:

```
sandbox project new hello "try this thing out"
sandbox status
```

`docs/START-HERE.md` walks the first hour step by step. `docs/MANUAL.md`
has every command.

## check this copy yourself

```
python3 -m unittest discover -s engine/tests -t .   # the whole suite, stdlib only
./sandbox verify                                    # sha256 against the manifest
```

`verify` proves the copy changed, not who changed it. releases are signed —
turn on strict verification (signature, not just hashes) with the release
public key:

```
export SANDBOX_MINISIGN_PUBKEY=RWSSaKTVM7ywEE8f/jL16NcRhOFR1sAtIOd2hAD/ziMRscYAlaGxw+9j
./sandbox verify
```

the same key is printed in every release's notes; if this file and the
release notes ever disagree, trust neither and ask.

## license

FSL-1.1-Apache-2.0 — free for everything except competing with the
software, and it converts to Apache 2.0 two years after each release.
