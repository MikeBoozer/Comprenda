# Comprenda — Demo / Portfolio Walkthrough (shot-list)

**Audience: prospective employers** (not buyers). Foreground *what you built and the
engineering behind it* — Snowflake-native, Cortex inference, a multi-axis divergence
metric, RAG-grounded analogs, an honest confidence label, a custom editorial design
system deployed live as a Streamlit-in-Snowflake app. Keep a thread of product sense, but
the subtext is "I designed, built, and shipped this end-to-end."

**Target length: ~4–4.5 min** (trim to ~3 with the `CUT-FOR-3` beats removed). One take, Loom,
casual-but-confident. This is a **shot-list**: each shot = what to *do*, what to *say*, and
what the screen *should* show. Verified values are stated; everything else is a `[read live]`
slot — **read the number off the screen, don't memorize it**, so nothing you say contradicts
what's rendered.

**Format:** a ~15-second **on-camera intro** (SHOT 0), then the screen tour as **clean
voice-over — no webcam picture-in-picture** (the editorial UI is a deliverable; keep it
unobstructed), and an **optional on-camera outro** (SHOT 6). Audio quality matters more than
the camera — use a decent mic, and look at the lens during the on-camera beats.

---

## Pre-flight (do this BEFORE you hit record)

- [ ] **Warm + verify the app first** — run the unfinished half of
      `docs/12_post_rebuild_render_checklist.md` (§4 AI Brief, §5 Frame Distribution, §6
      PLCS / Translator / Analogs). It de-risks the take: better to find a traceback now
      than mid-recording. The "Fast 2-minute pass" at the bottom of docs/12 + one
      click-through of PLCS / Translator / AI Brief is enough.
- [ ] App open in Snowsight → **Projects → Streamlit → Comprenda**. If it was open during
      the last rebuild, **⋮ → Rerun** so you're not on a stale session.
- [ ] Editorial theme loads; grouped sidebar **Workbench / Analysis / Synthesis** with glyphs;
      **no red traceback / `ModuleNotFoundError`**.
- [ ] Browser at 100% zoom, sidebar expanded, a clean window (no bookmarks bar clutter).
- [ ] **Credit awareness:** PLCS scoring, Translator re-score, and Brief generation each spend
      Cortex credits, and the SPCS container burns credits while idle. Don't leave it sitting
      between takes. The two big spends (PLCS live score, Brief) persist in session once run —
      if credits are tight, generate them once during the warm-up and let them **re-render**
      on the recording instead of re-clicking. The one spend worth showing *live* is the PLCS
      score (the spinner-to-result moment is the money shot).
- [ ] No hard numbers memorized. The only values you may state from memory are the verified
      ones below; everything market-specific is read off the screen.

### Verified on-screen values (from the 2026-05-30 rebuild — safe to state)
- Overview KPIs: **Events 8 · Languages 12 · Posts 1,440**
- Divergence matrix top fault lines: frame divergence **~0.40–0.48**
- "Sample sufficiency" spans **0.40 / 0.60 / 0.80** by sample size (it is *not* called
  "confidence" anymore — it's an honest sample-size label)
- PLCS sample line (already in the app behind **Try a sample →**):
  *"Live Free, Drive Fast — the new electric sports car that puts you first."*
- PLCS default markets: **ja · ko · de · fr** (already selected — no clicking needed)

---

## SHOT 0 — Intro · on camera · 0:00–0:15

**Format:** full-screen talking head, looking at the lens. The hook stays the literal first
words — identity rides in *after* it, so the opening keeps its punch.

**SAY (hook first, identity second):**
> "Every brand now ships global content with AI in the loop — copy gets generated faster than
> any human can check how it'll *read* in each market. Comprenda is the cultural reviewer that
> keeps up: it scores how a message lands in every market before launch, live on Snowflake."
>
> "I'm Mike — I built it end-to-end, on live Cortex AI against a real multilingual corpus.
> Let me show you."

**Then cut to the screen.** Don't re-deliver the hook once you're on the app.

---

## SHOT 1 — Overview · screen · 0:15–0:35

**Page:** Workbench → **Overview** (the default landing page).

**SAY (orient + bridge — not the hook again):**
> "Here's the app, running over that corpus — eight events, twelve languages, about 1,440
> posts. I'll start where a marketing team would: with a draft they're about to ship."

**ON SCREEN / EXPECTED:** editorial sidebar (Workbench / Analysis / Synthesis); KPI row reads
**Events 8 · Languages 12 · Posts 1,440**.

**CAPTURE:** still of the Overview landing (clean editorial UI + KPI row).

---

## SHOT 2 — Pre-launch risk (PLCS) · 0:35–1:45 · *the signature feature*

**Page:** Workbench → **Pre-launch risk**.

**DO:**
1. Click **Try a sample →** (prefills the automotive line — no typing on camera).
2. Leave target markets at the defaults **ja · ko · de · fr**.
3. Click **Score cultural risk**.

**SAY (while it scores — the live moment):**
> "I paste a draft tagline and pick four markets. Comprenda scores cultural risk 0–100 per
> market — live inference on Snowflake's Cortex AI, a few seconds each."

**SAY (when results land — verify the numbers against the screen before you commit them):**
> "Here's the verdict: three of four markets are unsafe to ship as drafted. The highest-risk
> market for this tagline is Japan, scoring 75/100. And this is the part I care about — it's
> not a black box. It gives the narrative for *why*, and three real historical analogs
> retrieved from the corpus — for example, in 1990 Mercedes-Benz's poorly chosen brand name
> 'Bēnsǐ' translated as 'rush to die,' which delayed their launch into the Chinese market — so
> the score is defensible, not invented. Nothing here is hallucinated; everything's sourced.
> The *gap* measures semantic closeness to that historical case — lower means a closer match."

**SAY (point at the band + handoff):**
> "The risk spectrum positions every market on one scale, and it recommends a next move —
> 'adapt before ship,' with a one-click handoff to the translator."

**ON SCREEN / EXPECTED:** per-market PLCS cards with scores + confidence; a "Narrative" block
for the worst market; **three analog cards** (proper pills, not one letter per pill); the
0–100 risk spectrum; a "Recommended next move" band with **Open Translator with this draft →**.

**CAPTURE:** still of the scored cards + risk spectrum (this is your hero screenshot /
thumbnail).

> **Live-number flag:** the script states example values ("three of four," "Japan 75/100") for a
> smooth read, but these come from live Cortex inference (temp 0.3) and **can shift between runs**.
> On recording day, glance at the screen and adjust the spoken numbers if they differ — never let
> the narration contradict the render. Same applies to the analog shown: name whichever one is
> actually on screen.

> **CUT-FOR-3:** keep this shot in full; it's the centerpiece.

---

## SHOT 3 — Cultural translator · 1:45–2:35 · *the workflow payoff*

**Page:** click **Open Translator with this draft →** from the PLCS recommendation band
(shows the product is a connected workflow, and the draft + flagged markets carry over).

**DO:**
1. Confirm the source draft carried over; target market is pre-filled to a flagged market.
2. Click **Generate adapted variants**.

**SAY:**
> "Most tools stop at 'this is risky.' Comprenda fixes it. It generates variants in the
> target market's *language*, each shifting the cultural frame deliberately — for example, here
> is a variant expressed through the competitive-threat frame — with a one-sentence rationale
> for each so a marketer can defend the choice. And you can re-score any variant back through
> the same risk model to prove the risk score actually dropped — I gated that behind a button so
> it only spends compute when you ask."

**ON SCREEN / EXPECTED:** three variant cards, each with a frame-shift pill, target-language
text, and a rationale; a "Re-score … for risk →" button below.

**CAPTURE:** still of the three variant cards.

> **CUT-FOR-3:** skip the actual **Re-score** click (it spends credits and adds ~20s); just
> *say* it exists and move on.

---

## SHOT 4 — Divergence matrix · 2:35–3:20 · *the analytical depth*

**Page:** Analysis → **Divergence matrix**.

**DO:**
1. Pick the event **iPhone 17 launch**.
2. In the aside's **Selected pair** dropdown, pick a dark / high-divergence pair.

**SAY:**
> "This is the post-launch side, and the part an engineer will appreciate. Two choices make it
> work. First, in Comprenda every post stays in its *native* language — analyzed directly,
> never translated to English first, which is where most tools lose the signal. Second, the
> wedge: most tools measure *sentiment* — was the reaction positive or negative? — and stop
> there. Comprenda measures *how* communities frame the same event differently, with a
> Jensen-Shannon divergence over their cultural-frame distributions, on a three-axis profile:
> frame, sentiment, and topical overlap. Same sentiment, completely different reasoning — and
> that's the part you can act on. For example, the Arabic- and English-speaking markets — which
> we can see have similar sentiment and are talking about similar topics around the iPhone 17
> launch — are experiencing and reacting to the event through very *different* cultural frames.
> And the sample sufficiency tells you how much data backs each pair: languages with less
> representation in the corpus, like Hindi or Italian, score lower, so you know which numbers to
> lean on and which are still provisional."

**ON SCREEN / EXPECTED:** full 12×12 heatmap (oxblood ramp); aside reads out the selected pair
with **Frame divergence / Sentiment divergence / Topical overlap / Sample sufficiency** and a
situation label (Lens-split / Mood-split / Aligned). Top pairs **~0.40–0.48**, *not* a flat
value; sample sufficiency varies **0.4 / 0.6 / 0.8**.

**CAPTURE:** still of the heatmap + aside.

> **Not spoken — interview talking point** (if asked "what would you improve?"): sample
> sufficiency is a transparent sample-size proxy. The rigorous next step (docs/10 #4b) is a
> Dirichlet-posterior credible interval on the per-pair JSD, plus a permutation test surfaced
> as an "above chance" flag — coherent with the smoothing already in the pipeline, compute-only.

---

## SHOT 5 — AI brief · 3:20–4:00 · *the synthesis*

**Page:** Synthesis → **AI brief**.

**DO:**
1. Event **iPhone 17 launch**; languages **en · ja · zh · de** (defaults are fine).
2. Click **Generate brief** (or let the pre-warmed brief re-render if conserving credits).

**SAY:**
> "Finally, when a CMO asks 'what's happening across our markets,' it synthesizes a
> source-cited brief — executive summary, where the markets disagree, dominant frames,
> recommendations — with the post IDs it drew from, plus two real figures generated from the
> corpus, not mock data. And the confidence notes are honest: it actually flags the thin
> languages — Hindi-involved pairs show limited data support, a sample sufficiency of 0.4.
> It tells you what it *doesn't* know."

**ON SCREEN / EXPECTED:** brief renders as TOC + article sections; meta row reads
"`[N]` SOURCES CITED · `[N]` LANGUAGES · `[N]`s · `[model]`"; two figures (frame-share bars +
pairwise frame-divergence dot plot with a dashed 0.34 line); a **Download Markdown** button.
Confidence notes name thin languages — **not** "1.0 across all pairs."

**CAPTURE:** still of the brief header + first section + the figures.

> **CUT-FOR-3:** show the brief rendered from the warm-up generation instead of generating
> live, and read just the summary + confidence note.

---

## SHOT 6 — Close · screen or on camera · 4:00–4:25

**Page:** back to **Overview** (or stay on the brief). **Delivery (optional):** for a bookend,
cut back to the full-screen talking head for the last two sentences — a natural place to add a
soft "I'm open to [roles] in [X]" if you're job-hunting. Voice-over over the screen is fine
too; the on-camera outro is a nice-to-have, not required.

**SAY (employer-facing close + trajectory):**
> "So that's the idea: most tools tell you a market reacted badly; Comprenda tells you *why*,
> before you ship. End-to-end, I designed the divergence metric, wrote the Snowpark UDFs and
> Cortex stored procedures, built the ten-page Streamlit-in-Snowflake app and its design
> system, and deployed it live. It's built to ship as a Snowflake Native App — installed from
> the Marketplace into each customer's own account, so their data never leaves their walls;
> that packaging is the next milestone. It runs today on bundled demo data; the expansion is
> every global brand pointing it at their own content — a live read on how their messaging
> lands across markets, and where the cultural framing is drifting. There's also a
> Snowflake-free version of the exact same app you can click through yourself — link's in the
> description. Thanks for watching."

> **Accuracy flag (read before recording):** the Native App / Marketplace install is **roadmap,
> not shipped** — per ADR-0001 + docs/10 #5–6 the app currently runs as a single
> Streamlit-in-Snowflake instance in the dev account; the Native App folder is a skeleton. The
> wording above is deliberately future-framed ("built to ship as… / next milestone"). Do **not**
> say "today it installs from the Marketplace" — that's the one claim that fails diligence.

**ON SCREEN / EXPECTED:** the editorial UI; clean exit.

---

## Optional add-in shots

Two extra beats you can splice into the main arc for more depth or a technical flex. **Both are
optional and both are `CUT-FOR-3`.** Adding both pushes the runtime to ~5.5 min (fine, but at the
upper edge for an employer video) — if you add only one, pick by audience: Analog retrieval is the
engineering / RAG flex; Event explorer is analytical depth that reinforces "not a black box."

### Optional A — Analog retrieval beat · splice after SHOT 2 (PLCS) · ~20s

**Why here:** the analogs just appeared *inside* the risk score; this shows the retrieval engine
behind them, directly. **Cost:** a small Cortex spend (query embedding + vector search).

**Page:** Analysis → **Analog retrieval**.

**DO:**
1. Click **Try an example →** (prefills the automotive-in-Japan query — continuous with the PLCS sample).
2. Leave target market **(any)** and count at **5**; click **Find analogs**.

**SAY:**
> "Those analogs in the risk score aren't decorative — they come from a retrieval engine I can
> show directly. I describe a situation, and it pulls the closest historical precedents from a
> curated case library by semantic similarity — company, year, what went wrong, the failure
> frames, each with its distance score. It's RAG over real marketing-failure cases — the same
> engine that pulled the three analogs behind the Pre-Launch score, so nothing it cites is invented."

**ON SCREEN / EXPECTED:** analog cards — *company · year*, italic case name, description, an
**Outcome** callout, **Failure frames** + **Affected markets** pills (proper pills, not
per-character), and a "gap `0.xxx`" distance per card.

**CAPTURE:** optional — an analog card close-up reads well as a "RAG / grounded" still.

### Optional B — Event explorer · splice after SHOT 4 (Divergence matrix) · ~25s

**Why here:** SHOT 4's aside has an **Open in event explorer →** button — a natural handoff, and
this is the per-market read *behind* the pairwise divergence. **Cost:** free — a pure SQL
aggregation, no Cortex.

**Page:** click **Open in event explorer →** from the matrix aside (or Analysis → **Event
explorer**), same event (**iPhone 17 launch**).

**SAY:**
> "The matrix tells you which pairs diverge; this is the read behind it. For one event, every
> market's actual mood and dominant frame, side by side — so 'English and Japanese diverge'
> becomes 'English framed it as opportunity, Japanese as status-quo, and here's the sentiment
> gap.' It's the decomposition that makes the divergence number trustworthy — a real per-market
> read under it, not a black-box score."

**ON SCREEN / EXPECTED:** KPI strip (**Markets · Posts · Avg sentiment · Sentiment spread**); a
sentiment-by-market bar chart on a −1…+1 scale; a **dominant-frame-by-market** list (language →
frame pill → post count).

**CAPTURE:** optional — the sentiment bars + dominant-frame list make a clean "per-market read" still.

---

## Post-recording

- Trim only the silent head/tail. Don't cut content.
- Add captions (Loom auto-generates) — **review the spoken numbers** against the screen.
- Title: **"Comprenda — score how your tagline reads in four markets, live on Snowflake Cortex"**
- Description: one line on the stack (Snowflake · Cortex · Streamlit-in-Snowflake · Snowpark)
  + the public-demo link + the repo link.

## Portfolio stills to grab (for README / LinkedIn placeholders)
1. Overview landing (editorial UI + KPI row) — the "what is this" shot.
2. PLCS scored cards + risk spectrum — the hero / thumbnail.
3. Divergence matrix heatmap + aside — the "there's real method here" shot.
4. AI brief (header + a figure) — the "it synthesizes and cites" shot.

> These four map directly onto the empty image slots in `README.md` ("See it run") and
> `go_to_market/linkedin_portfolio_post.md`. Drop them in after capture.
