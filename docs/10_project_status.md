# 10 — Project status & open items (living doc)

A running snapshot of *where things stand now* and the concrete open work. Kept here —
not in `CLAUDE.md` — so the always-loaded entry file stays lean. **This doc is expected to
drift if neglected; when it conflicts with the linked ADRs/code, trust those.** Update it
as state changes.

## Current state (2026-05-26)

- **Streamlit app:** live and working. Deployed via the CLI sequence in
  [`09_streamlit_ops_runbook.md`](09_streamlit_ops_runbook.md) — *not* the Snowsight Deploy
  button (which broke on a main-file rename). Entry file is `nuance.py`.
- **Cultural Divergence Score:** now a **multi-axis profile** — topical overlap +
  frame-divergence (JSD) + sentiment divergence — per
  [ADR-0003](decisions/0003-multi-axis-divergence-profile.md), replacing the old
  text-embedding centroid distance (which measured topic, not stance, and showed zero
  divergence). Thresholds + smoothing live in `nuance_db.internal.config`. The Divergence
  Matrix page inlines its query on purpose (SiS caches `lib/` imports — see the runbook).

## Binding open items (before the native-app / Marketplace build)

1. **Reconcile the three diverged trees** (git repo / Snowsight workspace / Streamlit object
   stage) to one source of truth —
   [ADR-0002](decisions/0002-reconcile-workspace-repo-divergence.md). Binding.
2. **Rebuild the demo corpus** — it is ~17× unevenly duplicated; verify the divergence
   signal. See [`07_audit_and_fixes.md`](07_audit_and_fixes.md) "Data-quality findings"
   (includes re-measurement queries).
3. **Re-derive divergence thresholds** from the rebuilt data and update `internal.config`.
4. **Update CDS references** in `semantic_model/nuance_semantic_model.yaml` and
   `native_app/setup_script.sql` to the multi-axis model.

## Deferred / nice-to-have

- UI/UX design-system pass (`streamlit/lib/ui.py`) before the Marketplace launch.
- Distributional sentiment divergence (vs the current scaled mean-difference).
