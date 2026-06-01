# Comprenda — Investor Cut (spoken-line overlay)

**Audience: prospective investors.** This is a **companion to `demo_script.md`, not a replacement.**
The staging is identical — same shots, same **DO / ON SCREEN / CAPTURE** steps, same pre-flight and
credit-awareness. Use `demo_script.md` to drive the app; use the **SAY** blocks below in place of the
portfolio ones where they differ. Only the *narration framing* changes.

**Why a separate cut:** employers fund the *person* ("look what I built"); investors fund the
*opportunity* (does it work, is it defensible, how big is the wallet, how capital-efficient is the
team). So the spoken lines trade the I-did-X-Y-Z engineering enumeration for moat, distribution,
margin, and land-and-expand. The product walkthrough itself (PLCS → translator → divergence → brief)
is equally compelling to both audiences and is unchanged except where noted.

**Honesty guardrails (these matter more with investors — they do diligence):**
- **Native App / Marketplace = roadmap, not shipped** (ADR-0001 + docs/10 #5–6). Always future-frame
  it ("built to ship as…", "the next milestone"). Never "today it installs from the Marketplace."
- Use only numbers in the repo docs: **under $400** total compute (README); incumbents **$800–$200K/yr**
  (docs/04); market-size figures from docs/04. Be ready to cite the source for any market stat.
- Live PLCS/divergence numbers shift between runs (temp 0.3) — verify against the screen on the day.

---

## SHOT 0 — Intro (on camera) — REPLACE the identity line

Hook is unchanged (it's a strong "why now" for investors too). Swap only the second sentence:

> "Every brand now ships global content with AI in the loop — copy gets generated faster than any
> human can check how it'll *read* in each market. Comprenda is the cultural reviewer that keeps up:
> it scores how a message lands in every market before launch, live on Snowflake."
>
> "I'm Mike — I designed and shipped the whole thing solo, live on Snowflake, for under $400 in
> compute. Let me show you what it does."

*(The "$400 solo" framing front-loads capital efficiency — an investor signal — without losing
"I built it," which is a strength for a solo technical founder.)*

## SHOT 1 — Overview — UNCHANGED
Use the portfolio SAY as-is.

## SHOT 2 — Pre-launch risk (PLCS) — UNCHANGED
Use the portfolio SAY as-is (the "not a black box / sourced, not invented" beat already lands for
investors — defensibility is a moat point). Same live-number flag applies.

## SHOT 3 — Cultural translator — UNCHANGED
Use the portfolio SAY as-is (the "most tools stop at 'this is risky' — Comprenda fixes it" beat is
already a differentiation point).

## SHOT 4 — Divergence matrix — REPLACE the opening framing

Change only the first sentence from "the part an engineer will appreciate" to a moat frame; keep the
rest of the portfolio SAY (native-language + frame-vs-sentiment + the Arabic/English example + sample
sufficiency) verbatim:

> "This is the post-launch side — and here's where the moat is, the part that's hard to copy. Two
> choices make it work. First, in Comprenda every post stays in its *native* language — analyzed
> directly, never translated to English first, which is where most tools lose the signal. Second, the
> wedge: most tools measure *sentiment* — positive or negative? — and stop there. Comprenda measures
> *how* communities frame the same event differently…" *(continue exactly as in `demo_script.md`)*

## SHOT 5 — AI brief — UNCHANGED
Use the portfolio SAY as-is (source-cited synthesis + honest confidence notes = a credible, sellable
"deliverable," which is the right note for investors).

## SHOT 6 — Close — REPLACE entirely (investor close)

> "So that's the bet: most tools tell you a market reacted badly; Comprenda tells you *why* — before
> you ship. The incumbents translate everything to English and stop at sentiment; Comprenda keeps each
> market in its own language and measures how they *frame* the event — that's the hard-to-copy part. I
> built and deployed the whole system end-to-end on Snowflake, live, for under $400 in compute. It's
> built to ship as a Snowflake Native App — installed from the Marketplace into each customer's own
> account, so their data never leaves their walls; that's both the margin story and the security story,
> and that packaging is the next milestone. It runs today on bundled demo data; the expansion is every
> global brand pointing it at their own content — a standing read on how their messaging lands across
> markets, and where the cultural framing is drifting. The buyers already pay Brandwatch or Sprinklr
> four figures a month for less. Try the live version yourself — link below."

*(Carries: moat, capital efficiency, margin + security, land-and-expand, willingness-to-pay. Every
claim is sourced from the repo docs — don't inflate beyond them. Keep the Native App as future tense.)*

---

## Optional add-in shots
Same as `demo_script.md` (Analog Retrieval = grounded-RAG credibility; Event Explorer = depth). For
investors, the **Analog Retrieval** beat reinforces "defensible / sourced," which plays well; Event
Explorer is optional.
