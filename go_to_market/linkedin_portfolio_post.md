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
12-category cultural-frame taxonomy + a multi-axis divergence score (framing,
sentiment, topical), with the LLM work running on Snowflake Cortex and the whole
thing packaged as a Snowflake Native App.

▶️ Play with it (no login): ‹demo URL›
🎬 2-min walkthrough: ‹video URL›
🛠️ Code + architecture docs: ‹repo URL›

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

**A few engineering/decisions I'm proud of:**
- **Native-language embeddings**, not translate-then-score — the whole premise.
- A **multi-axis divergence score** (frame Jensen-Shannon divergence + sentiment +
  topical overlap), because a single "sentiment" number hides the real signal: two
  markets can feel the same way about an event for opposite reasons.
- **Snowflake-native** end to end — Cortex for embeddings/classification/LLM,
  Cortex Search for retrieval, Streamlit-in-Snowflake for the UI, and the Native App
  Framework for distribution (it runs inside the customer's own account).
- Honest metrics: when a "confidence" number was really just a sample-size proxy,
  I relabeled it as *sample sufficiency* rather than overclaim — and scoped the
  statistically rigorous version (bootstrap CI on the divergence) as a follow-up.

▶️ Interactive demo (no login, runs on sample data): ‹demo URL›
🎬 2-min walkthrough of the live Cortex-powered version: ‹video URL›
🛠️ Repo (architecture docs + ADRs + the build log): ‹repo URL›

Happy to talk through any of it — the cultural-frame taxonomy, the divergence math,
or the Native App packaging.

#AI #LLM #Snowflake #DataEngineering #MarketingTech #ProductDevelopment

---

### Posting tips
- Lead with the **demo GIF or the video** as the media attachment — motion stops the scroll.
- Put the demo link in the **first comment** too (LinkedIn slightly favors posts that keep links out of the body; test both).
- Tag the stack (Snowflake) and, if you're job-hunting, add a soft "open to roles in ‹X›" line at the end.
