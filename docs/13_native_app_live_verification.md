# 13 — Native App live verification (captured 2026-06-03)

**Why this doc exists.** The Snowflake free trial that hosts the live Comprenda
deployment is expected to expire on/around 2026-06-03. The live Streamlit-in-Snowflake
app already has durable evidence (4 stills + a 5-min walkthrough video + a LinkedIn post),
but those were all captured *before* the Snowflake **Native App** was built and verified.
The native app — the Marketplace-distribution form of the product — had **zero captured
evidence** and cannot be demonstrated on a real account again once the trial dies (it would
have to be rebuilt from scratch on a fresh account). This file captures the irreplaceable
proof: that `COMPRENDA_APP` installed, provisioned, and ran all four hero Cortex features
end-to-end on a real Snowflake account.

All outputs below are **verbatim from the live account** (`snow sql`), not reconstructed.

## Provenance

| Field | Value |
|---|---|
| Account | `REB37163` (org locator `BKGUVJA-ASB96470`) |
| Region | `AWS_US_WEST_2` |
| Snowflake version | `10.19.101` |
| Captured at | `2026-06-03 04:17 -0700` |
| Captured by | `MIKEBOOZER` / role `ACCOUNTADMIN` |

## 1. Application package + installed application exist

`SHOW APPLICATION PACKAGES` / `SHOW APPLICATIONS`:

| Object | Name | Detail |
|---|---|---|
| Application package | `COMPRENDA_PKG` | `distribution = INTERNAL`, `type = NATIVE`, created 2026-06-02 |
| Installed application | `COMPRENDA_APP` | from package `COMPRENDA_PKG`, `label = "Comprenda v1.0"`, `patch 3`, `upgrade_state = COMPLETE` |

This is a genuine Snowflake Native App install (`type = NATIVE`), not a plain database —
the same artifact that would be published to Marketplace.

## 2. Provisioning succeeded — compute objects materialized

`provision_app()` built these (the parts a setup script can't, because it runs without a
warehouse):

**Two Cortex Search services — both `ACTIVE` / `ACTIVE`:**

| Service | Search column | Source rows | Embedding model | Refresh |
|---|---|---|---|---|
| `COMPRENDA_APP.APP_DATA.COMPRENDA_POST_SEARCH` | `POST_TEXT` | 1,440 | `snowflake-arctic-embed-m-v1.5` (auto-embedded) | INCREMENTAL, lag 1h |
| `COMPRENDA_APP.APP_DATA.COMPRENDA_ANALOG_SEARCH` | `DESCRIPTION` | 39 | `snowflake-arctic-embed-m-v1.5` (auto-embedded) | INCREMENTAL, lag 1d |

**Streamlit object:** `COMPRENDA_APP.APP_INSTANCE.COMPRENDA_APP` (`url_id 7w4vv7pxat2xkrp45erm`,
owner role type `APPLICATION`).

**App-created warehouse:** `COMPRENDA_WH` (X-Small, auto-suspend 60s, owned by the
`APPLICATION`) — the warehouse the search services refresh on.

## 3. Bundled demo corpus materialized into the app's own tables

`SELECT COUNT(*)` over `COMPRENDA_APP.APP_DATA.*` (readable because `app_admin` application
role is granted to `ACCOUNTADMIN`):

| Table | Rows |
|---|---|
| `social_posts` | 1,440 |
| `cultural_frames` | 1,440 |
| `cultural_divergence_scores` | 528 |
| `analog_corpus` | 39 |

The corpus spans **8 events × 12 languages** (180 posts/event):
`iPhone_17_launch`, `Tesla_robotaxi_debut`, `Olympics_2026_opening`, `World_Cup_2026_final`,
`K-pop_global_tour`, `BrandX_rebrand`, `EU_AI_act_enforcement`, `Climate_Summit_2026`.

**Top divergence pairs (real `frame_divergence`, the JSD headline metric):**

| Event | Pair | Frame div | Sent div | Topical overlap | Situation |
|---|---|---|---|---|---|
| Tesla_robotaxi_debut | en–hi | 0.483 | 0.116 | 0.856 | Same verdict, different reasons |
| iPhone_17_launch | ar–en | 0.457 | 0.017 | 0.912 | Same verdict, different reasons |
| iPhone_17_launch | en–fr | 0.448 | 0.120 | 0.941 | Same verdict, different reasons |
| K-pop_global_tour | en–fr | 0.445 | 0.113 | 0.848 | Same verdict, different reasons |
| Olympics_2026_opening | en–fr | 0.444 | 0.117 | 0.924 | Same verdict, different reasons |
| Tesla_robotaxi_debut | en–fr | 0.439 | 0.139 | 0.925 | Divergent |

## 4. All four hero Cortex procedures ran live

Each call below was executed against the installed app via
`CALL COMPRENDA_APP.APP_INSTANCE.<proc>(...)`. Outputs are verbatim.

### 4a. `score_content` — Pre-Launch Cultural Risk Score (PLCS)

**Input:** an individualist, "freedom"-framed Western draft aimed at the Hindi market
(`source = en`, `target = hi`):

> "Own the future. The all-new Tesla Robotaxi puts YOU in control - no driver, no limits,
> just pure individual freedom. Be the first to ride solo and leave the crowd behind."

**Result:** `plcs_score = 72`, `confidence = 0.80`, model `claude-4-sonnet`,
top frames in target market `["ambiguous","spiritual_ethical","individualist"]`,
15 nearest neighbors retrieved via `COMPRENDA_POST_SEARCH`.

> The draft presents significant cultural risk for the Hindi-speaking market due to frame
> misalignment. While the content emphasizes individualistic themes like 'pure individual
> freedom' and 'leave the crowd behind,' the historical analog data shows dominant frames
> are 'spiritual_ethical' and 'ambiguous' rather than purely individualist. Indian culture
> traditionally values collective harmony and community over extreme individualism. The
> phrase 'leave the crowd behind' could be particularly problematic as it suggests
> abandoning one's community, which conflicts with cultural values of family and social
> connection. Additionally, the aggressive tone of 'Own the future' may clash with more
> humble, spiritually-oriented communication preferences. Though only 13% of similar
> historical content showed negative sentiment, the strong individualistic messaging
> creates substantial risk of cultural disconnect in a market where collective values and
> spiritual considerations often take precedence over personal autonomy.

### 4b. `find_analogs` — historical-analog retrieval (the moat)

**Input:** `query = "Western tech brand launches an individualist, freedom-focused ad
campaign in a culturally collectivist market and triggers backlash"`, `target_market = hi`,
`k = 4`. Retrieved via `COMPRENDA_ANALOG_SEARCH` (semantic + reranker), filtered to
`affected_markets contains 'hi'` → 2 on-target hits:

| Analog | Company / Year | Frames | Why it matched |
|---|---|---|---|
| **Levi's 501 in India** | Levi's, 1995 | individualist ↔ collectivist | US individualist "rebel" messaging fell flat; collectivist market preferred family-celebration framing. Re-shot for family frame; sales recovered. |
| **McDonald's Hindu Beef Tallow Fries** | McDonald's, 2001 | spiritual_ethical | US fries cooked in beef tallow despite vegetarian claims → spiritual-ethical violation in Hindu market; $10M settlement; vegetarian-only India menu after. |

Both are precisely the failure modes the PLCS narrative flagged (individualist-frame clash;
spiritual-ethical sensitivity) — the retrieval and the risk score corroborate each other.

### 4c. `generate_brief` — AI Cultural Intelligence Brief

**Input:** `event_tag = iPhone_17_launch`, `target_languages = ['en','ar','fr','zh']`.
**Output (verbatim Markdown from `claude-4-sonnet`, prompt `ai-brief-v3`):**

```markdown
# Cultural Intelligence Brief: iPhone 17 Launch

## Executive Summary

The iPhone 17 launch reveals a consistent pattern of "same verdict, different reasons"
across most language communities, with moderate to high frame divergence (0.29-0.46)
despite strong topical overlap. English and Arabic speakers show the most positive
sentiment, while French and Chinese communities remain notably neutral, creating potential
messaging challenges for unified global campaigns.

## Key Cultural Divergences

| Language Pair | Situation | Frame Divergence | Sentiment Divergence | Interpretation |
|---------------|-----------|------------------|---------------------|----------------|
| Arabic-English | Same verdict, different reasons | 0.457 | 0.017 | Arabic frames through ambiguous/spiritual lens vs. English pragmatic/individualist approach, but similar enthusiasm |
| English-French | Same verdict, different reasons | 0.448 | 0.120 | English opportunity/pragmatic framing vs. French ambiguous/reform-seeking, with English notably more positive |
| Arabic-German | Divergent | 0.363 | 0.227 | Significant sentiment split alongside frame differences - highest sentiment divergence in dataset |
| English-Japanese | Divergent | 0.288 | 0.263 | Major sentiment disconnect despite discussing same topics - second-highest sentiment gap |
| English-Russian | Divergent | 0.321 | 0.146 | Moderate but meaningful divergence in both framing and emotional response |

## Dominant Frames by Region

- **Arabic**: Predominantly ambiguous framing (67%) with historical grievance and spiritual/ethical considerations
- **English**: Pragmatic and opportunity-focused (55%) with strong individualist perspective and some threat awareness
- **French**: Heavily ambiguous (53%) with reform-seeking and spiritual/ethical undertones
- **Chinese**: Opportunity-driven (40%) and pragmatic (25%) with notable nationalist elements (15%)

## Risk Flags

• **Arabic-German sentiment chasm**: 0.227 sentiment divergence suggests fundamentally different emotional responses that could undermine coordinated European-MENA campaigns
• **English-Japanese disconnect**: High sentiment divergence (0.263) despite cultural proximity indicates potential Asia-Pacific messaging conflicts
• **French neutrality barrier**: Consistently low sentiment (0.049) combined with reform-seeking frames suggests skepticism toward corporate messaging
• **Chinese nationalist undertones**: 15% nationalist framing could amplify during geopolitical tensions or trade disputes
• **Russian divergence pattern**: Consistent "divergent" classification with English suggests systematic messaging resistance

## Messaging Recommendations

**English**: Leverage the dominant pragmatic and opportunity frames with individualist benefits. Emphasize personal empowerment and practical advantages, as this audience shows highest receptivity (0.289 sentiment) to direct value propositions.

**Arabic**: Navigate carefully between spiritual/ethical considerations and the strong ambiguous framing. Avoid overly commercial messaging; instead emphasize community benefits and align with cultural values while acknowledging the complexity reflected in the ambiguous framing.

**French**: Address the reform-seeking mindset directly by positioning the product as progressive change rather than incremental improvement. Counter the neutral sentiment (0.049) by acknowledging skepticism and providing substantive differentiation rather than marketing hyperbole.

**Chinese**: Capitalize on the strong opportunity framing (40%) while respecting nationalist sentiments. Emphasize innovation leadership and collective progress, balancing individual benefits with broader societal advancement themes that resonate with the collectivist elements.

## Data & Sample-Size Notes

Most language pairs show adequate data backing (0.6 sample sufficiency), with Japanese-Chinese comparisons particularly well-supported (0.8). Hindi, Italian comparisons rely on lighter data volumes (0.4), making those insights more preliminary. The core target languages (English, Arabic, French, Chinese) all have sufficient data volume to support these cultural intelligence findings.
```

Note the brief correctly narrates `sample_sufficiency` (0.4 / 0.6 / 0.8) as data-volume
adequacy — **not** statistical confidence — per the honesty relabel in `docs/10` #4b.

### 4d. `translate_culture` — Cultural Translator (CJK output path)

**Input:** `source = en`, `target = ja`, frame hint auto-selected → `threat_framing`
(the dominant non-ambiguous frame for Japanese in the corpus). Source line:

> "Own the future. Pure individual freedom - the new phone thats just for you, so you can
> stand out from the crowd."

**Output — 3 Japanese variants, each shifting the frame toward the target market:**

| # | Frame shift | Variant (ja) | Rationale |
|---|---|---|---|
| 1 | obsolescence_threat | 時代に取り残されるな。完全個人仕様の新スマホで、埋もれる群衆から脱出せよ。 | Frames individual freedom as avoiding the threat of being left behind by technological progress and social conformity. |
| 2 | identity_loss_threat | みんなと同じでいいのか。あなただけの新スマホで、没個性の危険から身を守れ。 | Positions the phone as protection against the threat of losing one's unique identity in a homogeneous society. |
| 3 | competitive_survival_threat | 選ばれなければ終わり。純粋個人仕様の新スマホで、競争社会を生き抜け。 | Emphasizes the phone as essential for surviving in a competitive society where not being chosen means failure. |

The model preserved marketing intent while re-framing from Western individualism toward the
target market's dominant frame — and emitted correct multibyte Japanese end-to-end
(`PYTHONUTF8=1` required for the `snow` CLI to handle the CJK round-trip).

## What this does and doesn't cover

- **Covered (text/query evidence, irreplaceable):** the app + package install, version/patch,
  provisioning (search services, warehouse, materialized corpus), the real divergence matrix,
  and all four hero Cortex procedures returning live output. This is the proof that dies with
  the trial.
- **Not covered here (operator's part):** browser stills of the installed app's Streamlit
  rendering inside Snowsight (Data Products → Apps → Comprenda). Those are the native-app
  analog of the SiS stills already captured for the live app, and are worth grabbing in the
  same session if the trial is still up.
