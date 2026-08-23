---
description: open a build session on an intent, plan it, and come back with a diff
argument-hint: "what you are about to build"
allowed-tools: Bash(sandbox make:*), Bash(git diff:*), Bash(git status:*)
---

open the pass first, plan before you build, and hand the close back.

1. run `sandbox make --open "$ARGUMENTS"` and read what it prints — it names
   the project it opened on and snapshots the tree it will diff against.
2. enter plan mode, and stay there until the plan holds. when this host offers
   a worktree, take one: the work stays isolated until the pass closes.
3. build the plan.
4. show `git diff --stat` where the work lives, so the change is a computed
   number rather than your summary of it.
5. print this line for the owner to run at their terminal, with the project
   name and an honest summary filled in, and stop:

       sandbox make --close NAME --summary "what changed, in your words"

the close takes no key. it stages your summary, and what lands it is the
owner's own `sandbox approve`. this command leaves the verb to them either
way: what you do here is show the work, and their hand puts it on the
record.
