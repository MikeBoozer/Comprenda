# Comprenda UI Redesign — Claude Code Handoff Spec

> A single paste-ready document for Claude Code to implement the Comprenda
> redesign into Streamlit-in-Snowflake. Includes design tokens, theme
> mapping, per-component specs, microcopy library, CSS-injection
> strategy, the master implementation prompt, and the critique→improve
> loop pattern for iteration.
>
> **The companion HTML file `index.html`** contains the live mockups
> referenced throughout (Brand strip, Pre-Launch Risk populated/empty,
> Home populated/empty, AI Brief, Divergence Matrix populated/empty).
> Open it alongside this doc.

---

## 0 · Reading order

1. **§1 Design intent** — what we're trying to feel like, and why.
2. **§2 Tokens** — paste the hex values, type scale, spacing scale.
3. **§3 SiS theme.toml** — the file that goes in `.streamlit/config.toml`.
4. **§4 CSS injection** — the single `inject_css()` helper to call once per page.
5. **§5 Component specs** — how each piece looks and is built in Streamlit.
6. **§6 Per-screen blueprints** — what changes on each redesigned page.
7. **§7 Microcopy library** — exact strings for headlines, empty states, CTAs.
8. **§8 Master prompt for Claude Code** — paste this verbatim.
9. **§9 Critique→improve loop** — the iteration pattern, with role prompts.

---

## 1 · Design intent

**Aesthetic**: editorial intelligence-report. Serif headlines. Generous
whitespace. A single oxblood signal color that means "risk." Numbers
set in tabular monospace and treated like type, not chart labels.
Every screen leads with a one-sentence verdict (the "lede") and ends
with a recommended next move (the "onward"). Nothing decorative;
nothing is allowed on screen that isn't earning its place.

**Buyer**: CMO / Brand VP. Low patience for tables. Wants the
defensibility (analogs, confidence, sources cited) available, but
hidden behind progressive disclosure until asked for.

**Tone of voice**:
- Lede first. Open every screen with one declarative sentence.
- Never just a number. Every metric carries a frame: trend, band, or analog.
- Name the move. Every screen ends in a recommended next action.
- Cite the corpus. Quote post counts and timestamps; show your work.

---

## 2 · Tokens

### 2.1 Color (hex)

| Token            | Hex       | Use                                              |
|------------------|-----------|--------------------------------------------------|
| `paper-bg`       | `#F5F1E8` | Page background                                  |
| `paper-card`     | `#FAF7EF` | Card / panel surface                             |
| `paper-deep`     | `#ECE6D7` | Inset, nav active, button hover                  |
| `paper-deeper`   | `#E2DAC5` | Diagonal cell / table stripe                     |
| `ink`            | `#1C1A17` | Body text                                        |
| `ink-strong`     | `#0E0D0B` | Headings, primary button bg, max contrast        |
| `ink-muted`      | `#6E665B` | Captions, kickers, secondary metadata            |
| `ink-faint`      | `#9C9586` | Tertiary metadata, disabled                      |
| `rule`           | `#D8D1BE` | Thin dividers                                    |
| `rule-strong`    | `#C3B99F` | Input borders, button borders                    |
| `risk`           | `#8B2A1F` | Risk signal (oxblood) — used SPARINGLY           |
| `risk-bg`        | `#F2DDD8` | Risk pill / badge background                     |
| `warn`           | `#B5781E` | Elevated band                                    |
| `warn-bg`        | `#F5E6CD` | Warn pill / badge background                     |
| `safe`           | `#2F6B4A` | Safe band (forest green)                         |
| `safe-bg`        | `#DCE9DF` | Safe pill / badge background                     |
| `signal`         | `#1F4E79` | Reserved editorial blue — currently unused       |

**Rule of color economy**: any single screen uses at most two of
`risk`, `warn`, `safe`, `signal`. The default page is monochrome
paper-on-ink; color enters only to mark a verdict.

**Risk bands** (used everywhere a score appears):
- `0 – 35`  → safe  ("Ship")
- `35 – 55` → caution ("Watch") — band color is `ink-muted`, not warn
- `55 – 75` → warn ("Adapt")
- `75 – 100` → risk ("Do not ship")

### 2.2 Type

System font stacks only. SiS sandbox can't reliably load web fonts.

```css
--serif: "Iowan Old Style", "Palatino Linotype", Palatino, "URW Palladio L",
         "Book Antiqua", Georgia, serif;
--sans:  -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui,
         "Helvetica Neue", Helvetica, Arial, sans-serif;
--mono:  ui-monospace, "SF Mono", "Cascadia Code", "Roboto Mono", Menlo,
         Consolas, monospace;
```

**Wordmark**: the literal string `Comprenda` set in `--serif`, **roman** (not italic), 700 weight, 32px in the nav, 72px on brand strip. Letter-spacing `-0.01em`. Never as an image.

**Type scale** (px / line-height / weight / family):

| Token      | Spec                         | Use                            |
|------------|------------------------------|--------------------------------|
| `display`  | 44 / 1.05 / 400 / serif      | Page hero `<h1>`               |
| `h1`       | 32 / 1.1  / 400 / serif      | Section-opening headlines      |
| `h2`       | 22 / 1.25 / 400 / serif      | Sub-section heads              |
| `h3`       | 16 / 1.3  / 600 / sans       | UI section labels              |
| `body`     | 15 / 1.55 / 400 / sans       | Default UI                     |
| `lede`     | 17 / 1.55 / 400 / serif      | The hero subhead               |
| `narrative`| 16 / 1.6  / 400 / serif      | Long-form prose                |
| `small`    | 13 / 1.45 / 400 / sans       | Metadata, footnotes            |
| `kicker`   | 11 / 1    / 600 / sans uppercase, 0.12em tracking | Eyebrows |
| `mono`     | 12 / 1.4  / 400 / mono       | Data, codes, timestamps        |

`font-variant-numeric: tabular-nums` on anything that renders a
number. Every score on screen.

### 2.3 Spacing

A small fixed scale, used everywhere. Streamlit's `gap=` accepts these.

| Token | px  | Use                                  |
|-------|-----|--------------------------------------|
| `s-1` | 4   | Hairline gap                         |
| `s-2` | 8   | Tight inline gap                     |
| `s-3` | 12  | Default field padding                |
| `s-4` | 16  | Card inset                           |
| `s-5` | 20  | Between cards / list items           |
| `s-6` | 28  | Section break                        |
| `s-7` | 40  | Major section break                  |
| `s-8` | 56  | Hero margin                          |
| `s-9` | 80  | Page bottom padding                  |

### 2.4 Radii, borders, shadows

- **Radius**: `2px` everywhere. Sharp, editorial. No rounded cards.
- **Borders**: `1px solid var(--rule)` on cards. `1px solid var(--rule-strong)` on inputs/buttons. Risk-banded cards get a `3px solid var(--risk|warn|safe|ink-muted)` top border.
- **Shadows**: none. Editorial flatness; depth via rule + spacing.

---

## 3 · SiS `theme.toml`

Put this in `.streamlit/config.toml` in the Streamlit-in-Snowflake project.

```toml
[theme]
primaryColor             = "#8B2A1F"   # risk / oxblood — st.button primary, focus
backgroundColor          = "#F5F1E8"   # paper-bg
secondaryBackgroundColor = "#ECE6D7"   # paper-deep (sidebar, inset)
textColor                = "#1C1A17"   # ink
font                     = "serif"     # body falls back to system serif stack
```

`primaryColor` doubles as the focus-ring and selected-tab color across
Streamlit widgets. Use sparingly elsewhere so the focus state stays
salient.

---

## 4 · CSS injection — one helper, one call per page

Build a `lib/comprenda_theme.py` module with a single `inject_css()`
function. Call it as the first Streamlit operation on every page,
right after `set_page_config`.

**Why one big string, injected once**: avoids the multi-`st.markdown`
flicker, keeps CSS in one place, easy to version.

**Anti-pattern to avoid**: do NOT target Streamlit's emotion-cache
classes (`.st-emotion-cache-1xy23z` etc.) — they rotate on every
version upgrade. Target stable `[data-testid]` attributes, semantic
elements (`h1`, `h2`, `.stMetric`), or wrap our own content in
`st.markdown(unsafe_allow_html=True)` with `nu-`prefixed classes.

```python
# lib/comprenda_theme.py
import streamlit as st

# Pulled from the design tokens in §2. Single source of truth.
_TOKENS = """
:root {
  --paper-bg:#F5F1E8; --paper-card:#FAF7EF; --paper-deep:#ECE6D7;
  --paper-deeper:#E2DAC5;
  --ink:#1C1A17; --ink-strong:#0E0D0B; --ink-muted:#6E665B; --ink-faint:#9C9586;
  --rule:#D8D1BE; --rule-strong:#C3B99F;
  --risk:#8B2A1F; --risk-bg:#F2DDD8;
  --warn:#B5781E; --warn-bg:#F5E6CD;
  --safe:#2F6B4A; --safe-bg:#DCE9DF;
  --serif:"Iowan Old Style","Palatino Linotype",Palatino,"URW Palladio L","Book Antiqua",Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,"Helvetica Neue",Helvetica,Arial,sans-serif;
  --mono:ui-monospace,"SF Mono","Cascadia Code","Roboto Mono",Menlo,Consolas,monospace;
}
"""

# Stable Streamlit selectors — testids, semantic tags. NO emotion-cache hashes.
_BASE = """
html, body, .stApp { background: var(--paper-bg); color: var(--ink); }
.stApp { font-family: var(--sans); }

/* Editorial type for headings — Streamlit renders st.title -> h1, etc. */
h1, h2, h3, h4 { font-family: var(--serif); color: var(--ink-strong); letter-spacing:-0.01em; font-weight: 400; }
h1 { font-size: 44px; line-height: 1.05; }
h2 { font-size: 22px; line-height: 1.25; }
h3 { font-size: 16px; line-height: 1.3; font-family: var(--sans); font-weight: 600; }

/* st.caption — used as kicker */
[data-testid="stCaptionContainer"] {
  font-family: var(--sans); font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.12em; color: var(--ink-muted);
}

/* st.metric — neutralize the default emoji-y look */
[data-testid="stMetric"] { background: transparent; padding: 0; }
[data-testid="stMetricLabel"] {
  font-family: var(--sans); font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.12em; color: var(--ink-muted);
}
[data-testid="stMetricValue"] {
  font-family: var(--serif); font-size: 32px; line-height: 1; color: var(--ink-strong);
  font-variant-numeric: tabular-nums;
}
[data-testid="stMetricDelta"] { font-family: var(--mono); font-size: 11px; }

/* Buttons */
.stButton > button {
  font-family: var(--sans); font-size: 13px; font-weight: 500;
  border-radius: 2px; border: 1px solid var(--rule-strong);
  background: var(--paper-card); color: var(--ink); letter-spacing: 0.01em;
  padding: 10px 14px;
}
.stButton > button:hover { background: var(--paper-deep); border-color: var(--ink-muted); }
.stButton > button[kind="primary"] {
  background: var(--ink-strong); color: var(--paper-bg); border-color: var(--ink-strong);
}
.stButton > button[kind="primary"]:hover { background: var(--risk); border-color: var(--risk); }

/* Inputs */
[data-baseweb="input"], [data-baseweb="select"] > div, .stTextArea textarea {
  border-radius: 2px !important; border-color: var(--rule-strong) !important;
  background: var(--paper-card) !important; font-family: var(--sans) !important;
}

/* Dividers */
[data-testid="stDivider"] hr { border-top: 1px solid var(--rule); }

/* Dataframe — strip the rounded chrome, set serif numerals */
[data-testid="stDataFrame"] { border: 1px solid var(--rule); border-radius: 2px; }

/* Sidebar */
[data-testid="stSidebar"] { background: var(--paper-card); border-right: 1px solid var(--rule); }
"""

# Custom component classes — used by st.markdown(unsafe_allow_html=True).
_COMPONENTS = """
.nu-kicker { font: 600 11px/1 var(--sans); text-transform: uppercase;
             letter-spacing: 0.14em; color: var(--ink-muted); }
.nu-lede   { font: 400 17px/1.55 var(--serif); color: var(--ink); max-width: 720px; }

.nu-card   { background: var(--paper-card); border: 1px solid var(--rule);
             padding: 20px; border-radius: 2px; }

.nu-pill   { display:inline-block; padding:2px 7px; font:500 11px/1.4 var(--mono);
             background: var(--paper-deep); color: var(--ink-muted);
             border:1px solid var(--rule); border-radius:2px; margin: 0 2px; }
.nu-pill--risk { background: var(--risk-bg); color: var(--risk); border-color: var(--risk); }
.nu-pill--warn { background: var(--warn-bg); color: var(--warn); border-color: var(--warn); }
.nu-pill--safe { background: var(--safe-bg); color: var(--safe); border-color: var(--safe); }

.nu-badge { display:inline-flex; gap:5px; align-items:center;
            padding:3px 8px; font:500 11px/1.4 var(--sans);
            border:1px solid var(--rule); border-radius:2px;
            letter-spacing: 0.04em; text-transform: uppercase; }
.nu-badge--safe { background: var(--safe-bg); color: var(--safe); border-color: var(--safe); }
.nu-badge--caution { background: var(--paper-deep); color: var(--ink); border-color: var(--rule-strong); }
.nu-badge--warn { background: var(--warn-bg); color: var(--warn); border-color: var(--warn); }
.nu-badge--risk { background: var(--risk-bg); color: var(--risk); border-color: var(--risk); }

/* The PLCS hero — the signature visualization. Pure CSS, no JS. */
.nu-score { display: flex; flex-direction: column; gap: 8px; }
.nu-score-n { font: 400 96px/0.95 var(--serif); color: var(--ink-strong);
              font-variant-numeric: tabular-nums; }
.nu-score-n--risk { color: var(--risk); }
.nu-score-n--warn { color: var(--warn); }
.nu-score-n--safe { color: var(--safe); }
.nu-score-denom { font: 400 22px/1 var(--serif); color: var(--ink-faint); }

.nu-band { position: relative; height: 72px; border: 1px solid var(--rule);
           background: linear-gradient(to right,
             var(--safe-bg)    0%,  var(--safe-bg)    35%,
             var(--paper-deep) 35%, var(--paper-deep) 55%,
             var(--warn-bg)    55%, var(--warn-bg)    75%,
             var(--risk-bg)    75%, var(--risk-bg)    100%); }
.nu-band-marker { position:absolute; top:0; bottom:0; width:2px;
                  background: var(--ink-strong); transform: translateX(-50%); }
.nu-band-marker-pill { position:absolute; top:-24px; left:50%; transform:translateX(-50%);
                       background: var(--ink-strong); color: var(--paper-bg);
                       padding: 3px 8px; font: 600 11px/1 var(--sans);
                       border-radius: 2px; white-space: nowrap; }
.nu-band-analog { position: absolute; top: 50%; transform: translate(-50%,-50%);
                  width: 1px; height: 56px; background: var(--ink-muted); opacity: 0.55; }

/* Confidence bar */
.nu-conf-bar { height: 3px; background: var(--paper-deep); position: relative; }
.nu-conf-fill { position: absolute; inset: 0 auto 0 0; background: var(--ink-strong); }

/* Recommendation band — the dark CTA strip at the bottom of every result */
.nu-cta-band { background: var(--ink-strong); color: var(--paper-bg);
               padding: 28px 40px; display: grid;
               grid-template-columns: 2fr 1fr; gap: 28px; align-items: center;
               border-radius: 2px; }
.nu-cta-band h2 { color: var(--paper-bg); font-family: var(--serif);
                  font-size: 22px; margin: 4px 0 0; }
.nu-cta-band .nu-kicker { color: rgba(245,241,232,0.55); }
.nu-cta-band p { color: rgba(245,241,232,0.75); margin: 8px 0 0;
                 font-family: var(--sans); font-size: 14px; line-height: 1.5; }
"""

def inject_css():
    """Call once per page, right after st.set_page_config()."""
    st.markdown(f"<style>{_TOKENS}{_BASE}{_COMPONENTS}</style>",
                unsafe_allow_html=True)
```

---

## 5 · Component specs

Each component below is one of:
- **Native** — built from Streamlit primitives styled by `_BASE`.
- **Custom** — built from `st.markdown(unsafe_allow_html=True)` using the `nu-*` classes in `_COMPONENTS`.
- **Altair** — Altair chart styled to match.

### 5.1 Page header (Native)

```python
st.caption(f"{section.upper()} · {context}")    # kicker
st.title(headline)                               # h1, serif
st.markdown(f"<p class='nu-lede'>{lede}</p>",
            unsafe_allow_html=True)              # lede
st.divider()
```

Every page opens with this pattern. The kicker, headline, and lede are
the contract: by the time the user has read these three lines, they
should know what the screen is for.

### 5.2 KPI strip (Native, with CSS-tuned `st.metric`)

```python
cols = st.columns(6, gap="medium")
cols[0].metric("Events tracked", "142", "+6 wk")
cols[1].metric("Languages",      "38",  "stable")
# ...
```

`st.metric` is restyled by `_BASE` — label becomes a kicker, value
becomes serif tabular-nums, delta becomes mono. Use `delta_color="off"`
when the delta is informational only (so it doesn't tint green/red).

### 5.3 PLCS per-market card (Custom)

```python
def plcs_card(market_code, market_name, score, conf, one_liner, frames):
    band = ("risk" if score >= 75 else "warn" if score >= 55
            else "caution" if score >= 35 else "safe")
    label = {"safe":"Low","caution":"Moderate","warn":"Elevated","risk":"High"}[band]
    frames_html = "".join(f"<span class='nu-pill'>{f}</span>" for f in frames)
    st.markdown(f"""
      <div class='nu-card' style='border-top: 3px solid var(--{band});
                                  min-height: 280px; display:flex;
                                  flex-direction:column; gap:12px;'>
        <div style='display:flex; justify-content:space-between;'>
          <div>
            <div class='nu-kicker'>{market_code}</div>
            <div style='font:600 16px/1.2 var(--sans);
                        color:var(--ink-strong);'>{market_name}</div>
          </div>
          <span class='nu-badge nu-badge--{band}'>{label}</span>
        </div>
        <div style='display:flex; align-items:baseline; gap:4px;'>
          <span class='nu-score-n nu-score-n--{band}'
                style='font-size:64px;'>{score}</span>
          <span class='nu-score-denom'>/100</span>
        </div>
        <div style='display:flex; align-items:center; gap:8px;'>
          <div class='nu-conf-bar' style='flex:1;'>
            <div class='nu-conf-fill' style='width:{conf*100:.0f}%;'></div>
          </div>
          <span style='font:var(--mono); font-size:11px; color:var(--ink-muted);'>
            {conf*100:.0f}% conf
          </span>
        </div>
        <div style='font:400 13px/1.5 var(--serif); color:var(--ink);'>
          {one_liner}
        </div>
        <div style='margin-top:auto; display:flex; flex-wrap:wrap; gap:3px;'>
          {frames_html}
        </div>
      </div>
    """, unsafe_allow_html=True)
```

Render four cards in a `st.columns(4)` row.

### 5.4 Risk band (the signature viz) — Custom

```python
def risk_band(markers, analogs=()):
    """
    markers: list of (label, score, band) — drawn on top.
    analogs: list of (label, score) — drawn as light ticks behind.
    """
    analog_html = "".join(
      f"<div class='nu-band-analog' style='left:{s}%;' title='{lbl}'></div>"
      for lbl, s in analogs)
    marker_html = "".join(
      f"<div class='nu-band-marker' style='left:{s}%;'>"
      f"<div class='nu-band-marker-pill'>{lbl} · {s}</div></div>"
      for lbl, s, _band in markers)
    st.markdown(f"""
      <div class='nu-band'>{analog_html}{marker_html}</div>
      <div style='display:flex; justify-content:space-between;
                  margin-top:8px; font:500 11px/1 var(--mono);
                  color:var(--ink-muted);'>
        <span>0 · safe</span><span>35</span><span>55</span>
        <span>75</span><span>100 · do not ship</span>
      </div>
    """, unsafe_allow_html=True)
```

This is the screenshot people will paste into Slack. Make sure the
markers don't overlap — if two scores are within 4 points, nudge them.

### 5.5 Analog list item (Custom)

```python
def analog(year, company, case_name, outcome, gap):
    st.markdown(f"""
      <div style='display:flex; gap:16px; padding:12px 0;
                  border-bottom:1px solid var(--rule);'>
        <div style='min-width:76px;'>
          <div style='font:600 13px/1.2 var(--sans);'>{year}</div>
          <div style='font:400 10px/1.2 var(--mono);
                      color:var(--ink-muted);'>gap {gap}</div>
        </div>
        <div>
          <div style='font:600 13px/1.2 var(--sans);
                      color:var(--ink-strong);'>{company}</div>
          <div style='font:italic 400 13px/1.3 var(--serif);'>{case_name}</div>
          <div style='font:400 12px/1.4 var(--sans);
                      color:var(--ink-muted);'>{outcome}</div>
        </div>
      </div>
    """, unsafe_allow_html=True)
```

### 5.6 Recommendation band (Custom)

```python
def rec_band(kicker, headline, body, primary_label, primary_action,
             secondary=()):
    st.markdown(f"""
      <div class='nu-cta-band'>
        <div>
          <div class='nu-kicker'>{kicker}</div>
          <h2>{headline}</h2>
          <p>{body}</p>
        </div>
        <div></div>
      </div>
    """, unsafe_allow_html=True)
    # Buttons sit outside the band so they remain native (clickable).
    cols = st.columns([1, 1, 1])
    if cols[0].button(primary_label, type="primary",
                      use_container_width=True):
        primary_action()
    for i, (lbl, fn) in enumerate(secondary, start=1):
        if cols[i].button(lbl, use_container_width=True):
            fn()
```

### 5.7 Divergence heatmap — **Altair**

Frame-divergence color uses an interpolated scale, not the default
`reds`. Use the same band thresholds as PLCS so the visual language is
consistent across screens.

```python
import altair as alt

def divergence_heatmap(df):
    # df columns: language_a, language_b, headline_score, situation_label,
    # frame_divergence, sentiment_divergence, topical_overlap
    return (
        alt.Chart(df)
        .mark_rect(stroke="#F5F1E8", strokeWidth=2)
        .encode(
            x=alt.X("language_b:N", title=None,
                    axis=alt.Axis(orient="top", labelAngle=0,
                                  labelFontWeight="bold",
                                  labelFont="ui-monospace, SF Mono, Menlo",
                                  labelFontSize=12,
                                  labelColor="#1C1A17", ticks=False, domain=False)),
            y=alt.Y("language_a:N", title=None,
                    axis=alt.Axis(labelFontWeight="bold",
                                  labelFont="ui-monospace, SF Mono, Menlo",
                                  labelFontSize=12,
                                  labelColor="#1C1A17", ticks=False, domain=False)),
            color=alt.Color(
                "headline_score:Q",
                scale=alt.Scale(
                    domain=[0, 0.15, 0.25, 0.34, 0.50, 0.65],
                    range=["#ECE6D7", "#E9E6D7", "#E5D0B6",
                           "#D9A887", "#BF6C4B", "#8B2A1F"],
                ),
                legend=alt.Legend(title="Frame divergence",
                                  titleFontSize=11, labelFontSize=11),
            ),
            tooltip=[
                alt.Tooltip("language_a:N", title="A"),
                alt.Tooltip("language_b:N", title="B"),
                alt.Tooltip("situation_label:N", title="Situation"),
                alt.Tooltip("headline_score:Q", title="Frame div.", format=".2f"),
                alt.Tooltip("sentiment_divergence:Q", title="Sentiment div.", format=".2f"),
                alt.Tooltip("topical_overlap:Q", title="Topical overlap", format=".2f"),
            ],
        )
        .properties(height=520)
        .configure_view(strokeWidth=0)
        .configure_axis(grid=False)
    )
```

### 5.8 Frame-share bar (the brief's per-language frame chart) — Custom

A horizontal bar made of segments. Same structure as the PLCS chip
row, with width set by share. The "risk" segment (the frame your
content is being absorbed into) gets the oxblood treatment.

### 5.9 Confidence & sources — progressive disclosure

Use `st.expander` styled with `_BASE`. Default the PLCS narrative
expander to open only when `score >= 60`; default Sources Cited to
closed. The trust signal needs to be present, not in the user's face.

```python
with st.expander("Sources cited", expanded=False):
    st.markdown("""…""")
with st.expander("Confidence calculation", expanded=False):
    st.markdown("""…""")
```

---

## 6 · Per-screen blueprints

For each page, the structure is **kicker → h1 → lede → divider → body → divider → recommendation band**.

### 6.1 `comprenda_app.py` — Home / Overview

**Today (populated):**
1. Kicker: `TUESDAY · 27 MAY · 09:14 PT`
2. H1: a one-sentence "three signals" lede that names the count of
   things worth attention. *(See microcopy §7.1.)*
3. Lede paragraph: which two drift events and one elevated PLCS score
   from overnight; one-sentence pre-summary.
4. KPI strip: 6 metrics in `st.columns(6)`.
5. Two-column feeds: Drift alerts (left), PLCS scores (right). Each
   feed-item is a custom card with entity / pair / delta / one-liner /
   timestamp / next-action link.
6. Onward grid: 3 cards — generate-this-morning's-brief, translate the
   elevated draft, subscribe a new entity.

**First-run / empty:**
1. Welcome kicker + H1: "Three reads before lunch."
2. Lede: explain what Comprenda does in 1 sentence, name the trial path.
3. Two-column layout: left = three-step "how teams start" with
   icon-letter `N`; right = a sample draft (the "Live Free, Drive Fast"
   tagline) with a one-click "Score this draft" button.
4. "What you'll get" 3-card grid (a score not a vibe; frames not
   translations; a page you can forward).

### 6.2 `pages/1_Pre_Launch_Risk.py` — Pre-Launch Risk

**Populated:**
1. Header (kicker / h1 / lede).
2. Input zone in `st.columns([2, 1])`: draft on the left, target
   markets + source on the right. Markets render as chips, not a
   multiselect, when possible (custom HTML); fall back to `st.multiselect`.
3. Run button (primary, full-width).
4. Results header — `kicker + h2 + dek`: "One of four markets is unsafe."
5. Four-column PLCS cards (§5.3).
6. **Signature viz**: the risk band (§5.4) with one marker per market and
   the three nearest historical analogs as ticks behind.
7. Narrative section for the highest-risk market — two-column: left =
   contributor bars (frame / lexicon / analogs / sentiment); right =
   three analogs.
8. Progressive disclosure: `st.expander("Sources cited")` and
   `st.expander("Confidence calculation")`.
9. Recommendation band — handoff to Cultural Translator with the
   high-risk markets pre-selected.

**Empty / first-run:**
1. Header.
2. Input zone with greyed-out placeholder text and a single chip:
   `+ pick markets`. Input meta shows `0 / 2,000 · ⌘↩ to score · Try a sample →`.
3. "What you'll see" panel in `st.columns([3, 2])`: left = a labeled
   four-part breakdown (number banded, confidence, three analogs,
   recommended next move); right = a sample-draft card with one-click
   "Use this sample" button.

### 6.3 `pages/4_Divergence_Matrix.py` — Divergence Matrix

**Populated:**
1. Header.
2. Controls row: event selector + axis tabs (Frame / Sentiment /
   Topical) + a horizontal color-scale legend.
3. Two-column: left = the heatmap (Altair, §5.7) sized at ~640px wide;
   right = a 260px aside card with the currently-selected pair's
   numbers (frame div, sentiment div, topical overlap, confidence) and
   a "Open in event explorer" CTA. Selection state is a `st.session_state`
   key; clicking a cell rerenders the aside.
4. "Reading the matrix" four-column legend grid below — aligned,
   lens-split, mood-split, same-verdict-different-reasons.

**Empty / first-run:**
1. Header with "Pick an event. Read the room." H1.
2. Controls row with `— pick an event tag —` placeholder.
3. Two-column: left = "Three events worth opening first" — three
   pre-loaded event tags with one-sentence descriptions and post counts;
   right = "How to read it, in two sentences" panel with a sample CTA.

### 6.4 `pages/8_AI_Brief.py` — AI Brief

**Populated:**
1. Header (full version): kicker shows event + date, h1 is the brief's
   actual title (one declarative sentence), lede is 2-3 sentences of
   the executive summary. Meta row below: post count, language count,
   generation time, plus three action buttons (copy markdown / download
   PDF / share).
2. Two-column body: 220px sticky TOC on the left, 760px article column
   on the right.
3. Sections numbered `§ 1` through `§ 5` with serif numerals. Each
   section opens with its own kicker + h2 + first paragraph.
4. Inline figures: frame distribution bars (§5.8), dot-chart for
   pairwise frame divergence (custom).
5. Recommendations as numbered list with italic serif "01 / 02 / 03"
   prefixes.

This screen has no "empty state" — the brief generation is the empty
state. Pre-generation, the page is just the input selector + a
descriptive panel about what the brief contains.

---

## 7 · Microcopy library

Drop these in as default strings; the implementer can wire them to
real values. Tone: declarative, CMO-first, never apologetic, never
celebratory.

### 7.1 Home

| Slot                | String |
|---------------------|--------|
| Kicker (populated)  | `{DAY} · {DATE} · {TIME} {TZ}` |
| H1 (populated)      | `Three signals worth your morning.` (or `Two signals…` / `One signal…` etc.) |
| Lede (populated)    | `{N} new drift events, {M} elevated pre-launch score{s} from overnight. {one-sentence "biggest story"}. The full read is below.` |
| H1 (no signals)     | `Quiet morning.` |
| Lede (no signals)   | `No drift events past tolerance, no elevated pre-launch scores in the last 24 hours. The corpus is tracking {N} entities; the next scheduled drift check is at {TIME}.` |
| H1 (empty / day 1)  | `Three reads before lunch.` |
| Lede (empty)        | `Comprenda scores how a draft will land in markets you don't speak — before you ship it. The fastest path is a thirty-second test drive on a draft of your own. Pick a starting point below.` |
| Onward 1 title      | `Generate this morning's brief` |
| Onward 2 title      | `Translate the elevated draft` |
| Onward 3 title      | `Subscribe a new entity` |

### 7.2 Pre-Launch Risk

| Slot                | String |
|---------------------|--------|
| Kicker              | `PRE-LAUNCH CULTURAL RISK · PLCS` |
| H1 (empty)          | `Score a draft.` |
| H1 (high-risk)      | `One of {N} markets is unsafe to ship as drafted.` |
| H1 (all clear)      | `Cleared. No market scored above 35.` |
| H1 (mixed)          | `Mostly fine. {market} is the one to watch.` |
| Lede (empty)        | `One number per market, on a scale of 0–100. Each number is backed by a confidence interval, three historical analogs from your corpus, and a one-sentence read. Nothing is invented; everything is sourced.` |
| Result kicker       | `RESULT · SCORED AGAINST {N}-POST CORPUS · {SECONDS}s` |
| Per-card one-liners | One sentence each, written by the model. *No exclamation marks.* |
| CTA band kicker     | `RECOMMENDED NEXT MOVE` |
| CTA band H2         | `Adapt for {markets} before ship.` |
| CTA band primary    | `Open Translator with this draft →` |
| CTA band sec.       | `Export as PDF` · `Share with team` |
| Sample draft (empty)| `"Live Free, Drive Fast — the new electric sports car that puts you first."` |
| Sample-draft note   | `A real automotive launch line we've scored before. The result is striking — and worth seeing before you paste your own.` |

### 7.3 Divergence Matrix

| Slot                | String |
|---------------------|--------|
| Kicker              | `CULTURAL DIVERGENCE MATRIX · {EVENT_TAG}` |
| H1 (populated)      | `{N} languages, one event, {M} fault line{s}.` |
| Lede                | `How differently each language community frames the {event}. Color encodes frame divergence — the lens-mismatch axis. Topical overlap is high across the board (everyone is talking about the same event); the signal lives in *how*.` |
| H1 (empty)          | `Pick an event. Read the room.` |
| Reading 1           | `**Aligned.** Same lens, same mood. Below 0.15.` |
| Reading 2           | `**Lens-split.** Same words, different frame.` |
| Reading 3           | `**Mood-split.** Same frame, opposite feeling. Rare.` |
| Reading 4           | `**Same verdict, different reasons.** Look behind the agreement.` |

### 7.4 AI Brief

| Slot                | String |
|---------------------|--------|
| Kicker              | `AI CULTURAL INTELLIGENCE BRIEF · {EVENT_TAG} · {DATE}` |
| H1                  | Model-generated; coach with: *one declarative sentence, no colon, no question mark, ≤ 9 words.* |
| Lede                | Model-generated; coach with: *first sentence is the verdict; second sentence is the qualifier; third sentence is the watch-out.* |
| Section heads       | `EXECUTIVE SUMMARY` · `WHERE THE MARKETS DISAGREE` · `DOMINANT FRAMES` · `RISK FLAGS` · `RECOMMENDATIONS` · `SOURCES CITED` |
| Generated meta      | `{N} POSTS · {M} LANGUAGES · {S}s · SOURCES CITED` |

### 7.5 Universal empty-state primary CTAs

Never `Get started`. Never `Try it now`.

| When                                | Use |
|-------------------------------------|-----|
| Trial first visit                   | `Score the sample draft →` |
| No data in corpus yet               | `Load the demo corpus →` |
| No subscriptions yet                | `Subscribe your first brand →` |
| No briefs generated yet             | `Generate a brief for {recent_event} →` |

### 7.6 Frame labels (display vs. storage)

The corpus stores frames as snake_case identifiers (`status_quo`, `craft_reverence`, `reform_seeking`, `status_loss`, `premium_affirmation`, etc.). **Never render the raw token in UI** — it reads as a database leak. Always transform for display.

| Raw token            | Display                |
|----------------------|------------------------|
| `status_quo`         | `Status quo`           |
| `craft_reverence`    | `Craft reverence`      |
| `status_loss`        | `Status loss`          |
| `premium_affirmation`| `Premium affirmation`  |
| `national_pride`     | `National pride`       |
| `price_anxiety`      | `Price anxiety`        |
| `craft`              | `Craft`                |
| `individualist`      | `Individualist`        |
| `other`              | `Other`                |

**Rule**: take the snake_case token, replace underscores with spaces, capitalize only the first letter. Build one helper, use everywhere:

```python
def frame_label(token: str) -> str:
    return token.replace("_", " ").replace("-", " ").capitalize()
```

Set frame labels in pills (`var(--mono)` font) for that "data token but readable" feel. In running narrative prose, drop the pill chrome and just use the words — `the draft uses an individualist frame against a market currently coded as status quo and craft reverence`.

---

## 8 · Master prompt for Claude Code

Paste this into Claude Code at the root of your Streamlit repo. The
companion files Claude Code will need: `Claude-Code-Handoff.md` (this
file), `index.html` (the mockups), and `tokens.css` and `screens.jsx`
for reference.

````markdown
You are implementing a UI/UX redesign of the Comprenda Streamlit-in-Snowflake app.

# Reference materials (read in this order)
1. `Claude-Code-Handoff.md` — full design spec, tokens, microcopy, theme.toml.
2. `index.html` — live mockups for every screen. Open in a browser to see the target.
3. `tokens.css` — the design tokens, ported verbatim.
4. `streamlit/` — the current implementation.

# Hard constraints (DO NOT VIOLATE)
- Streamlit-in-Snowflake only. NO external pip packages beyond what's in `environment.yml`. NO streamlit-extras, NO custom JS components.
- CSS via `st.markdown(unsafe_allow_html=True)` ONLY. NEVER target `.st-emotion-cache-*` classes — only stable `[data-testid="..."]` attributes, semantic HTML elements, or your own `nu-*` classes.
- Charts via Altair only. NO Plotly, NO D3, NO Vega-Lite-via-JSON.
- System font stacks only. NO Google Fonts, NO @font-face. The wordmark is the literal string "Comprenda" set in `var(--serif)` italic.
- Wide layout, desktop only. Don't add mobile breakpoints.
- Preserve all existing query logic in `lib/comprenda_queries.py`. Do not change any SQL.
- Preserve all stored-procedure call signatures.

# Order of operations (do these one at a time, commit between each)
0. **File renames** — the existing Streamlit codebase uses `nuance_*` names. Rename so the product name is reflected end-to-end:
     - `nuance_app.py` → `comprenda_app.py` (Streamlit entry point)
     - `lib/nuance_queries.py` → `lib/comprenda_queries.py`
     - Update every import accordingly. **Do not touch the SQL or query logic inside these files.**
     - **Leave the `nu-*` CSS class prefix as-is** — it's internal-only and renaming it touches every component. Internal artifact, not a product name leak.
1. Create `lib/comprenda_theme.py` with the `inject_css()` helper from §4. Copy the token + base + components CSS verbatim from `Claude-Code-Handoff.md`.
2. Create `.streamlit/config.toml` with the `[theme]` block from §3.
3. Build per-component helpers in `lib/comprenda_components.py`:
     - `page_header(kicker, headline, lede)`
     - `kpi(label, value, delta=None, kind="neutral")`
     - `plcs_card(market_code, market_name, score, conf, one_liner, frames)`
     - `risk_band(markers, analogs=())`
     - `analog(year, company, case_name, outcome, gap)`
     - `rec_band(kicker, headline, body, primary_label, primary_action, secondary=())`
     - `frame_share_bar(language, share_dict)`
     - `pill(text, tone="neutral")` and `badge(score)`
   Each takes the data it needs and emits one `st.markdown(unsafe_allow_html=True)` call OR a chain of native Streamlit primitives — see §5 for the exact HTML.
4. Refactor `comprenda_app.py` (the home page) to match §6.1. Add the empty-state branch when KPIs are all zero.
5. Refactor `pages/1_Pre_Launch_Risk.py` to match §6.2. Add the empty-state branch when `draft` is empty.
6. Refactor `pages/4_Divergence_Matrix.py` to match §6.3. Replace the existing Altair chart with the §5.7 version. Add the empty-state branch.
7. Refactor `pages/8_AI_Brief.py` to match §6.4.
8. Leave the other five pages structurally alone, but add three lines at the top of each: `from lib.comprenda_theme import inject_css; inject_css()`, and wrap their headers in `page_header()` from `lib/comprenda_components.py`. That gets the visual refresh on every page without a deep rework.

# What "done" looks like for each page
- The page header is `page_header(kicker, headline, lede)` — never raw `st.title`.
- Every result section ends in a `rec_band(...)` with a recommended next move OR is wrapped in an empty-state branch.
- Every score on screen uses tabular-nums and is paired with its band.
- Confidence and sources are in `st.expander`s, default-collapsed unless the score warrants attention.
- Microcopy matches §7 (replace placeholders with real values).
- The screen looks like the corresponding artboard in `index.html`. If it doesn't, fix the screen, not the artboard.

# How to verify
After each page:
1. Run the app locally (or in a Snowflake dev account).
2. Take a screenshot.
3. Open the corresponding artboard in `index.html` side-by-side.
4. Run the critique loop in `Claude-Code-Handoff.md` §9. Apply the critique. Iterate until pass.

# What you may NOT do
- Add a "Comprenda" logo image. Use the typographic wordmark only.
- Add emoji to UI labels (the kicker glyphs in the mockup nav are part of the design; everywhere else, no emoji).
- Add peer / industry benchmark widgets. We have no benchmark data.
- Add streamlit-extras, streamlit-shadcn-ui, or any other styling lib.
- Reorder navigation pages. Their existing order is the trial-onboarding order.
- Change the page filenames; Streamlit's auto-router depends on them.

Begin with step 1. After each step, summarize what changed in one paragraph and wait for "go" before continuing.
````

---

## 9 · Critique → improve loop

A two-role pattern. Run as separate Claude Code conversations, or in
the same one with explicit role flips.

### 9.1 The implementer prompt

> You are the implementer. Your job is to apply the redesign as
> specified in `Claude-Code-Handoff.md`. After each page, output:
> (a) the diff you applied, (b) a screenshot of the result.
> Then wait for the critique.

### 9.2 The critic prompt

Paste this into a new Claude Code conversation. Feed it the screenshot
+ the corresponding artboard from `index.html`.

> You are a senior product designer reviewing an implementation of the
> Comprenda redesign. You are paid to find what's wrong, not what's right.
> The reference is `Claude-Code-Handoff.md` plus the corresponding
> artboard in `index.html`.
>
> Score the implementation against these eight criteria. Each is /10.
>
> 1. **Hierarchy** — does the lede land within 2 seconds? Does the eye
>    move kicker → headline → lede → numbers → next-move? Or is
>    everything fighting for attention?
> 2. **Number weight** — are scores in serif tabular-nums, sized like
>    type, NOT like chart labels? Does every number have a band, an
>    interval, or an analog adjacent to it?
> 3. **Color economy** — is risk-color used ≤ 3 times on screen? Is
>    safe-color used at all? Color must be a verdict, never decoration.
> 4. **Empty-state quality** — is there a sample, a CTA, and a
>    one-paragraph explainer? No "no data yet" pity-text.
> 5. **CMO-first copy** — every headline a declarative sentence?
>    Lede contains the verdict? Onward names a concrete next move?
> 6. **Implementation hygiene** — any `.st-emotion-cache-*` selectors?
>    Any web fonts? Any non-Altair charts? Any pip packages outside
>    `environment.yml`? Each is a fail.
> 7. **Editorial restraint** — any emoji? Any rounded corners > 2px?
>    Any shadow other than `none`? Any color outside the §2 palette?
> 8. **The signature viz** — does the PLCS risk band look like the
>    artboard? Are markers spaced legibly? Are historical analogs as
>    ticks behind?
>
> For each criterion: score, one sentence of evidence, one sentence of
> fix. Total /80. Below 64 means another pass.

### 9.3 The loop

```
implementer commits → critic scores
  → critic writes ONE issue list ordered by impact
  → implementer fixes top 3 issues, commits
  → critic re-scores
  → stop when total ≥ 72 or three iterations, whichever first.
```

Three iterations is the realistic ceiling. After that, you should
review by hand — the model starts polishing in circles past iteration
three. Don't let it.

### 9.4 What "self-iterating" can realistically do for a Streamlit app

Honest answer: about 80% of the way. The critic-loop catches missing
empty states, wrong color usage, oversized headings, missing CTAs,
emoji that snuck in, the wrong band colors. It will not catch:

- Whether the data on screen is actually what a real PLCS run returns
  (the model fakes plausible values).
- Whether the Snowflake permissions allow the SQL to run.
- Whether the auto-dispatched drift task actually fires.
- Whether `inject_css()` breaks under a future Streamlit version (it
  won't if you stick to `[data-testid]` selectors — but no model can
  verify a future version).

For the last 20%, plan one human review pass on a real Snowflake
deployment before declaring it done.

---

## 10 · The round-trip workflow (Design ⇄ Code)

This handoff isn't a single hand-off. Most projects do one or two
round-trips between the design environment that produced this doc and
your Claude Code implementation. Knowing when to round-trip vs. fix
in place is the difference between three iterations and twelve.

### 10.1 Decide here vs. decide in Code

| Type of decision | Decide in design env | Decide in Claude Code |
|---|---|---|
| Aesthetic (type, color, layout, hierarchy) | ✅ | ❌ |
| What's on each screen / information architecture | ✅ | ❌ |
| Signature viz visual design | ✅ | ❌ |
| Microcopy and tone | ✅ | partial |
| Empty-state structure | ✅ | ❌ |
| Real `SCORE_CONTENT` / `GENERATE_BRIEF` JSON not fitting the layout | ❌ | ✅ then back |
| Altair chart fidelity to the mock | partial | ✅ |
| CSS that leaks under real Streamlit | ❌ | ✅ |
| Snowsight chrome conflicts | ❌ | ✅ |
| Permissions / SQL / deployment | ❌ | ✅ |

**Rule**: design decisions go in this doc + `index.html` artboards.
Implementation discoveries that *invalidate a design assumption* come
back here to update the design — then re-feed Code with the revised
spec.

### 10.2 The round-trip

```
Design env (here)
  ├─ Iterate aesthetic, structure, microcopy
  └─ Export: this doc + index.html + tokens.css
        ↓
Claude Code (your repo)
  ├─ implementer ⇄ critic loop (§9), 2–3 iterations
  └─ If a real-data shape, an Altair limitation, or a SiS-CSS
     issue invalidates a design assumption:
        ↓
Back to Design env
  ├─ Update artboard + spec accordingly
  └─ Re-export v2
        ↓
Back to Claude Code, fresh implementer ⇄ critic loop on v2
```

Most projects round-trip **once**, sometimes twice. Past that, the
design isn't converging — stop and decide with a human in the room.

### 10.3 What the critic loop will NOT catch

Worth restating from §9.4 and expanding:

- Whether the data on screen reflects what your stored procs really
  return (the model invents plausible values).
- Whether Snowflake permissions allow the SQL to run for the trial
  user role.
- Whether the SiS sandbox actually loads the system serif (e.g.
  Windows-only Snowflake VDIs may fall back further than expected —
  watch for Georgia rendering).
- Whether the auto-dispatched drift task actually fires on schedule.
- Whether `inject_css()` survives a future Streamlit version (it will
  if you stick to `[data-testid]` selectors — but the critic can only
  check the version in front of it).

For each of these, plan a **manual review pass** on a real Snowflake
deployment before declaring done.

### 10.4 Practical iteration cadence

A realistic project rhythm:

| Day | Action | Where |
|---|---|---|
| 1 | First design pass; settle aesthetic, IA, microcopy | Design env |
| 1 | First Code pass: theme + components + 2 screens | Claude Code |
| 2 | Critic loop on those 2 screens, 2 iterations | Claude Code |
| 2 | Human review screenshots side-by-side with artboards | You |
| 3 | Fix design assumptions surfaced by real data | Design env |
| 3 | Second Code pass: remaining screens | Claude Code |
| 4 | Critic loop on remaining screens | Claude Code |
| 4 | Deploy to a Snowflake dev account; manual QA | You |
| 5 | Bug-fix + polish pass | Claude Code |

Total: about a week of elapsed time, of which maybe 6–8 hours is
yours.

### 10.5 Automating the loop further

The critique loop in §9 is *semi-automated* — you carry screenshots
between two conversations. Two ways to push toward fully unattended:

1. **In one Claude Code session, with role flips.** Tell Code: "After
   each implementation step, switch role to critic, score against the
   rubric, write a fix list, switch back to implementer, apply, repeat
   until score ≥ 72 or three iterations." This is the cheapest
   upgrade. It works because the rubric is concrete.
2. **A shell script that orchestrates both prompts** + uses Claude
   Code's headless mode + saves screenshots between steps. More
   reliable, more effort. Reasonable if you're going to do this for
   ten projects, overkill for one.

The ceiling is the same either way: the loop polishes 80% of the
deviation from the artboards. The last 20% needs human judgment,
either at the end of each loop or via the round-trip back to the
design env.

---

## 11 · One-shot install / setup

```text
# Files to create (in order)
.streamlit/config.toml            ← §3
lib/comprenda_theme.py               ← §4
lib/comprenda_components.py          ← §5 helpers

# Files to refactor (in order)
comprenda_app.py                     ← §6.1
pages/1_Pre_Launch_Risk.py        ← §6.2
pages/4_Divergence_Matrix.py      ← §6.3
pages/8_AI_Brief.py               ← §6.4
# Other pages: minimal — inject_css() + page_header() only.
```

---

*End of handoff. Reference `index.html` alongside for the pixels.*
