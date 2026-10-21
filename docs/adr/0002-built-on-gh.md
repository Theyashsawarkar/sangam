# 2. Build on the GitHub CLI, fzf and tmux

**Status:** Accepted  
**Date:** 2026-10-15

## Context

Reviewing PRs means authentication, many API calls and a fast interface. Writing an API client and a TUI framework would dwarf the tool.

## Decision

sangam is a bash program on top of `gh` (sign-in and API), fzf (the interface) and tmux (popups and panes).

## Consequences

- No token or config needed: it uses your `gh` sign-in.
- Those three tools are required.
