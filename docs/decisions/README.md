# Architecture Decision Records

This folder records significant, hard-to-reverse decisions about Project Nuance —
the *why* behind structural choices, which code and git history don't preserve.

## Conventions

- One decision per file, numbered: `NNNN-short-title.md`.
- Keep each to ~1 page: **Context, Decision, Alternatives, Consequences.**
- **Append-only.** Never rewrite a past decision. When a decision changes, add a new
  ADR and mark the old one `Status: Superseded by ADR-NNNN`. A superseded ADR is still
  a true record of what was decided, and when.
- Only for genuinely significant choices (distribution model, data architecture, major
  dependencies) — not routine ones.
- This folder is the **canonical** home for decisions. External notes (Notion, etc.)
  should link here, not restate.

## Index

- [0001](0001-native-app-distribution-with-demo-data.md) — Distribute Nuance as a
  self-contained Snowflake Native App with bundled synthetic demo data. *(Accepted)*
