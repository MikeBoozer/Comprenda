# ADR-0003: Replace single text-embedding CDS with a multi-axis cultural divergence profile

- **Status:** Accepted
- **Date:** 2026-05-26
- **Deciders:** Mike (operator)

## Context

Diagnosis on the live data (2026-05-26; full numbers in
[`docs/07_audit_and_fixes.md`](../07_audit_and_fixes.md) → "Data-quality findings")
showed the headline **Cultural Divergence Score is structurally blind to the divergence
the product exists to detect.**

CDS (`snowflake/07_cds_computation.sql`) is the cosine **distance** between per-`(event,
language)` **text-embedding centroids**. Findings:

- **All 528 language pairs score < 0.20; zero reach the product's own 0.35 "meaningful"
  threshold.** The Divergence Matrix shows essentially nothing.
- This is **not** a washed-out-embedding or averaging artifact: **cross-event**
  same-language centroid distances span **0.28–0.52**, so the embedding space has real
  dynamic range. The embeddings encode **topic**, not cultural **stance**.
- The divergence *is* strongly present in the enriched data — just in other dimensions:
  - **Framing:** every event has **4–5 distinct dominant frames** across its languages
    (e.g. iPhone_17_launch: en=individualist, de=pragmatic, ru=historical_grievance,
    zh=opportunity_framing).
  - **Sentiment:** per-event spread across languages is **0.41–0.91** (on −1…1).
- A **frame-distribution Jensen-Shannon prototype** produced **521/528 pairs ≥ 0.35** —
  the inverse of the flat text-CDS — confirming the signal is recoverable from data we
  already have, with **no corpus regeneration required for the metric itself**.

In short: text-embedding CDS measures *"are they discussing the same thing?"* (always yes,
same event) instead of *"do they see it differently?"* (yes — in frames and sentiment).

(The ~17× uneven duplication found alongside this is a *secondary*, mild issue; CDS is
robust to it. It is tracked separately and folded into the ADR-0002 data-bundling work.)

## Decision

**1. Replace the single text-embedding CDS with a multi-axis "divergence profile" of 2–3
orthogonal axes:**

- **Topical overlap** — the *existing* text-embedding distance, **relabeled**. It confirms
  "these markets are discussing the same event," which is genuinely useful context (it
  turns the flat-CDS finding from a bug into a feature).
- **Frame divergence (Jensen-Shannon)** — the **primary headline signal**: how differently
  cultures *frame* the same event.
- **Sentiment divergence** — how differently they *feel* about it.

**2. Compute it correctly:**

- On **deduplicated** data (one row per distinct `post_text` per event/language).
- With **smoothing** (Laplace/Dirichlet) on the frame distributions and a **sample-size
  confidence guard**, because per-`(event, language)` distinct-post counts are small
  (~10–20 over 12 frames) and raw JSD over-fires on sparse histograms.
- With **recalibrated thresholds** for each axis (the legacy 0.35/0.55 were tuned for
  cosine distance; raw JSD discriminates better than its square-root). Thresholds and
  smoothing parameters live in `internal.config`, **not** hardcoded.

**3. Present it per the UX principle (folded into this ADR so it isn't regressed):**

- **One headline number to scan** (frame-based) everywhere glanceability matters
  (heatmap, KPIs). The axes are the **explanation / drill-down**, not three co-equal gauges
  the user must combine.
- Collapse common axis combinations into a few **named situations** — e.g. *Aligned*,
  *Divergent*, *Shared lens / split mood*, *Same verdict / different reasons*.
- The **AI Brief** narrates the profile in prose ("same conversation, framed oppositely,
  felt oppositely").
- Show the axes **separately; never blend them into one weighted score** (a blended score
  reintroduces weight-tuning drift and is less interpretable).
- **Validate** the result against the demo script / ICP (a marketer must "get it" at a
  glance), not just internal review.

## Alternatives considered

- **Keep text-embedding CDS.** Rejected — it measures topic, not stance; it is the cause of
  the flat matrix.
- **Lower the 0.35/0.55 thresholds so the existing matrix lights up.** Rejected — this
  *fakes* the core metric instead of measuring divergence; it would mislead buyers and is
  exactly the kind of drift this ADR guards against.
- **Sentiment divergence alone.** Rejected as the headline — one-dimensional; loses the
  *framing* story that is the product's actual differentiator. Kept as a secondary axis.
- **Single weighted blend of frame + sentiment.** Rejected — arbitrary weights are a
  drift hazard and the blended scalar is uninterpretable. Axes are shown separately instead.
- **A re-embedded "stance signature" vector.** Reasonable, but redundant once frame and
  sentiment are surfaced directly, and more of a black box. Held as a fallback if a single
  "centroid distance" narrative is later wanted for marketing.

## Consequences

**Positive**
- The headline metric finally reflects the value proposition; the demo can *show* divergence.
- Multi-axis profile gives **triangulated confidence** and richer, more actionable insight
  (framing → repositioning; sentiment → retone) than a single scalar.
- Reuses existing enriched data — **no corpus regeneration needed for the metric**.
- The previously "broken" topical-overlap signal becomes a useful "same-conversation" axis.

**Negative / follow-up (binding)**
- Requires reworking `snowflake/07_cds_computation.sql` (or a new computation), a schema
  change to store multiple axes + the named-situation classification, threshold/smoothing
  config rows, and UI changes across the Divergence Matrix, AI Brief, and KPIs.
- Threshold recalibration is **empirical** — must be derived from the data, then sanity-
  checked, before the demo is considered trustworthy.
- Must be computed on deduplicated data, coupling lightly to the ADR-0002 data work.
- The CDS definitions in `snowflake/07_cds_computation.sql` (header) and
  `docs/06_architecture.md` must be updated when this is implemented; this ADR supersedes
  the single-metric definition.

## Notes

Evidence and re-measurement queries are in `docs/07_audit_and_fixes.md`. Implementation
will be designed in a dedicated planning pass before any code changes.
