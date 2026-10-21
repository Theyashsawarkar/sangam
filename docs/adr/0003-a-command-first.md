# 3. A command first, a tmux popup second

**Status:** Accepted  
**Date:** 2026-10-17

## Context

It began as a tmux plugin; but reviewing PRs is useful outside tmux.

## Decision

sangam is a standalone command with an installer and `make install`; the tmux plugin is one way to open it.

## Consequences

- Runs in any terminal.
- The tmux plugin links TPM's copy onto PATH.
