# LinkedIn — portfolio / "what I built" post

Builder-narrative angle for your network and prospective employers (distinct from
`linkedin_launch_post.md`, which is the product-launch announcement). Fill the
‹bracketed› links before posting. Two lengths below — pick one.

---

## Option A — short (the scroll-stopper)

AI is now drafting global marketing copy. Almost nobody checks whether it lands in
*non-English* markets before it ships — and the tools that exist translate to
English first, which destroys the cultural signal.

So I built **Comprenda**: it scores content in its *native* language space and
shows you, per market, *how differently* each community frames the same launch —
before you publish.

Under the hood it's Snowflake-native end to end: multilingual embeddings + a
cultural-frame taxonomy + a multi-axis divergence score (framing, sentiment,
topical), with the LLM work running on Snowflake Cortex and the whole thing
designed to ship as a Snowflake Native App.

▶️ Play with it (no login): https://comprenda.streamlit.app
🎬 5-min walkthrough: https://youtu.be/15cbl7WS9cQ
🛠️ Code + architecture docs: https://github.com/MikeBoozer/Comprenda

#AI #DataEngineering #Snowflake #Marketing #LLM

---

## Option B — longer (the depth version)

**The problem I kept seeing in 2026:** AI agents draft global marketing content in
seconds, but teams have no purpose-built way to QA whether it'll land in non-English
markets. Every social-listening tool translates to English first and runs
English-trained sentiment — which is exactly where the cultural signal dies.

**What I built — Comprenda:** a cultural-intelligence app that keeps content in its
native language space and surfaces, per market, *how differently* communities frame
the same event. It gives a **Pre-Launch Cultural Risk Score** before you publish,
and a divergence matrix + AI brief for post-launch monitoring.

**A few decisions I'm proud of:**
- **Native-language embeddings**, not translate-then-score — the whole premise.
- A **multi-axis divergence score** (frame divergence + sentiment + topical overlap),
  because a single "sentiment" number hides the real signal: two markets can feel the
  same way about an event for opposite reasons.
- **Snowflake-native** end to end — Cortex for the embeddings/classification/LLM work,
  Cortex Search for retrieval, Streamlit-in-Snowflake for the UI, and designed for the
  Native App Framework so it can run inside the customer's own account.
- Honest metrics: when a "confidence" number was really just a sample-size proxy,
  I relabeled it as *sample sufficiency* rather than overclaim — and scoped a
  statistically rigorous replacement as a follow-up.

▶️ Interactive demo (no login, runs on sample data): https://comprenda.streamlit.app
🎬 5-min walkthrough of the live Cortex-powered version: https://youtu.be/15cbl7WS9cQ
🛠️ Repo (architecture docs + ADRs + the build log): https://github.com/MikeBoozer/Comprenda

Happy to talk through the build — the product decisions, the tradeoffs, and what I'd
do differently at scale.

#AI #LLM #Snowflake #DataEngineering #MarketingTech #ProductDevelopment

---

### Media to attach
LinkedIn doesn't render markdown images — you attach media in the composer. Use the
four portfolio stills from `go_to_market/demo_script.md` (saved in `docs/img/`), in
this order:

1. **`02_plcs_risk_score.png`** — the clearest single-frame "what does it do"; lead
   with this still if you're not leading with the video.
2. `03_divergence_matrix.png` — the "there's real method here" frame.
3. `04_ai_brief.png` — the synthesis frame.
4. `01_overview.png` — context / the corpus at a glance.

Best layout: the **video** (or a short GIF) as the first media tile, then the
four stills as a carousel in the order above.

### Posting tips
- Lead with the **demo GIF or the video** as the media attachment — motion stops the scroll.
- Put the demo link in the **first comment** too (LinkedIn slightly favors posts that keep links out of the body; test both).
- Tag the stack (Snowflake) and, if you're job-hunting, add a soft "open to roles in ‹X›" line at the end.
