# voice_fixtures — the lint, made to fail on purpose

a lint nobody can make fail proves nothing. one pair per check: the
`*.fail.*` file must fail that check and the `*.pass.*` file must pass it.
`test_voice.TestFixtures` runs every pair on every run.

check A skips this whole directory by name — the fixtures wear the words
they test, and that is the one directory-level exemption in the walk.

`flat/` is the pair no machine can judge: a `.fail.md` there passes every
regex above and still reads like a manual. its check is the owner's eye,
named in `test_flat_fixtures_pass_every_regex`, which asserts exactly that
the machine sees nothing wrong.
