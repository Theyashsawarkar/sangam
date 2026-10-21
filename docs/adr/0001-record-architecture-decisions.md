# 1. Record architecture decisions

**Status:** Accepted  
**Date:** 2026-10-21

## Context

Decisions about how sangam is built (its dependencies, its boundaries, the trade-offs it accepts) were made in conversations and commit messages, where nobody finds them later. A contributor asking "why does it do it this way?" deserves an answer that doesn't need the original author.

## Decision

Significant decisions are recorded as Architecture Decision Records in `docs/adr/`, numbered, in Michael Nygard's format: context, decision, consequences, and a status. A record is never rewritten to reflect a change of mind; a new record supersedes it and both stay.

## Consequences

- The project website's *Decisions* page lists every record.
- A pull request that changes one of these decisions adds a record that supersedes it.
- Small, reversible choices don't need a record: the CHANGELOG is enough.
