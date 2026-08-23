---
description: open a build session on an intent, plan it, and come back with a diff
argument-hint: "what you are about to build"
allowed-tools: Bash(sandbox make:*), Bash(git diff:*), Bash(git status:*)
---

open the pass first. plan before you build, and hand the close back.

1. run `sandbox make --open "$ARGUMENTS"` and read what it prints. it names the
   project it opened on, and it snapshots the tree it will diff against.
2. enter plan mode, and stay there until the plan holds. when this host offers a
   worktree, take one: the work stays isolated until the pass closes.
3. build the plan.
4. show `git diff --stat` where the work lives, so the change reaches them as a
   computed number instead of your summary of it, and paste what it prints
   without trimming a line.
5. print this line for the owner to run at their own terminal, with the project
   name filled in and an honest summary in your words, then stop and wait:

       sandbox make --close NAME --summary "what changed, in your words"

the close takes no key. it stages your summary, and the only thing that lands
that summary is the owner's own `sandbox approve`, read at a real keyboard.
either way this command leaves the verb to them: you show the work, and their
hand puts it on the record.
