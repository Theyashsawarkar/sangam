# 4. Vim keys with Space as the leader, emulated in fzf

**Status:** Accepted  
**Date:** 2026-11-08

## Context

Every Vayu tool is moving to the same keys: Normal and Insert modes, `Space` as the leader, and the same groups after it in every tool (`p` the object, `g` go to, `f` filter, `t` tabs, `y` copy, `o` open, `,` settings, `r` refresh, `?` keys, `q` quit). sangam had one letter per action, several of which mean something else elsewhere (`r` was request changes, `o` checkout, `d` draft, `u` account). fzf binds single keys only: it has no key sequences.

## Decision

Every key but the moving ones runs `sangam --key` through fzf's `transform`. It reads what is pending (`g`, `Space`, `Space p`...) from `$STATE/pending`, answers with fzf actions, and shows the keys that can follow in fzf's footer (which-key). While a key is pending, the moving keys are unbound, so only `Esc` or a valid next key goes on. `Space Space` opens a palette of the leader actions; the pick is replayed through the same code. The old single-letter actions moved under `Space p`, `Space g` and `Space f`; for one release they show where they went.

## Consequences

- One code path for keys, testable without fzf or tmux (`tests/keys.sh`).
- Each non-moving key starts a short-lived `sangam` (about 25 ms); `j`/`k` stay instant.
- The groups match the other Vayu tools, so a key learnt in one works in the next.
