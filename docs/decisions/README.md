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
- [0002](0002-reconcile-workspace-repo-divergence.md) — The deployed app (Snowsight
  workspace) and the git repo have diverged; ship current fixes into the workspace now,
  reconcile to a single source of truth during native-app packaging. *(Accepted)*
- [0003](0003-multi-axis-divergence-profile.md) — Replace the single text-embedding CDS
  (which measures topic, not stance, and shows zero divergence) with a multi-axis profile —
  topical overlap + frame divergence (JSD) + sentiment — with a one-headline-number UX.
  *(Accepted)*
