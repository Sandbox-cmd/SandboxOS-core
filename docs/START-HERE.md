# start here

this is Sandbox OS — a maker's workshop that runs on your own machine.
README.md says what it is; this page is the first hour, each step one
runnable command, what you should see, and what to do when you don't.

## 1 · open the workshop

DO
```
./sandbox init
```
SEE — "opened your workshop at ~/Sandbox … ready. nobody's tool." plus a
read-back line saying the wiring took.
IF-NOT — "python3 is required": install python 3.9+. want the workshop
elsewhere? `SANDBOX_HOME=/path/you/choose ./sandbox init`. re-running init
is always safe: it creates what is absent and touches nothing that lives.

## 2 · the health check

DO
```
sandbox doctor
```
SEE — a short table, every line `ok`.
IF-NOT — each failing line names its fix in the same breath.

## 3 · your first project

DO
```
sandbox project new hello "see how this feels"
sandbox project on hello
sandbox status
```
SEE — the project listed, active, with a `*` for on. bare verbs now land
on it.

## 4 · put something on the record

DO
```
sandbox note "the first thing worth remembering"
sandbox drafts
sandbox approve
```
SEE — the note stages first ("waiting for your approval"), then lands with
your key. that split is the whole design: anything durable waits for you.

## 5 · look at your workshop

DO
```
sandbox page
```
SEE — a path to page.html; open it in a browser. it renders your local
state and asks the network for nothing.

## 6 · when something is worth keeping

DO
```
sandbox save PATH --note "why it matters"
sandbox builds
```
SEE — the build on your shelf with a checksum. `sandbox use NAME` copies
it onto a project later; a payload that drifted from its card refuses to
spread.

## 7 · ship something real

give your project checks — open its PROJECT.md and add one command per
line under `## checks` — then:

DO
```
sandbox ship hello
```
SEE — the first ship asks your `k` on those exact checks; after that, a
green re-ship needs no ceremony and says `triggered: session` on the
record.

from here: `docs/MANUAL.md` for every verb · `sandbox recall QUERY` any
time you wonder whether you already decided something.
