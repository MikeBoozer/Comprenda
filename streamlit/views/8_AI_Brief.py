"""AI Cultural Intelligence Brief — editorial, source-cited synthesis.

GENERATE_BRIEF returns a single markdown blob + source post_ids, so the editorial
TOC / numbered sections are derived from the markdown. Two real figures
(frame distribution, pairwise divergence) are drawn from existing query helpers
to realize the §6.4 inline-figure intent with corpus data, not mock values.

Redesign blueprint: Claude-Code-Handoff.md §6.4. Proc signature preserved.
"""
import datetime

import streamlit as st
from snowflake.snowpark.context import get_active_session
import altair as alt
import pandas as pd

from lib.comprenda_queries import (
    list_event_tags, list_languages, call_generate_brief,
    get_frame_distribution, get_cds_matrix,
)
from lib.comprenda_theme import inject_css
from lib.comprenda_components import page_header, frame_share_bar, event_label

inject_css()

session = get_active_session()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _section_head(kicker, headline, dek=None):
    dek_html = (f"<p style='font:400 14px/1.5 var(--serif); color:var(--ink-muted);"
                f" max-width:680px; margin:6px 0 0;'>{dek}</p>" if dek else "")
    st.markdown(
        f"<div class='nu-kicker'>{kicker}</div><h2>{headline}</h2>{dek_html}",
        unsafe_allow_html=True)


def parse_brief(md):
    """Return (title, [(heading, body), ...]) from the brief markdown.

    A leading '# Title' becomes the title; '## ' headings split sections.
    """
    lines = (md or "").splitlines()
    title = None
    start = 0
    for i, ln in enumerate(lines):
        if ln.strip():
            if ln.startswith("# ") and not ln.startswith("## "):
                title = ln[2:].strip()
                start = i + 1
            break
    sections, head, body = [], None, []
    for ln in lines[start:]:
        if ln.startswith("## "):
            if head is not None or any(b.strip() for b in body):
                sections.append((head, "\n".join(body).strip()))
            head, body = ln[3:].strip(), []
        else:
            body.append(ln)
    if head is not None or any(b.strip() for b in body):
        sections.append((head, "\n".join(body).strip()))
    sections = [(h, b) for h, b in sections if h or b.strip()]
    return title, sections


def first_paragraph(body):
    for para in body.split("\n\n"):
        if para.strip():
            return " ".join(para.split())
    return ""


# ---------------------------------------------------------------------------
# Figures (real data via existing query helpers)
# ---------------------------------------------------------------------------
def render_frame_figure(event_tag, languages):
    try:
        fd = get_frame_distribution(session, event_tag)
    except Exception:
        return
    if fd is None or fd.empty:
        return
    _section_head("Figure · dominant frames", "What each market is talking about.",
                  "Frame share per language, from the corpus. Source: CULTURAL_FRAMES.")
    wanted = set(languages or [])
    for lang, grp in fd.groupby("DETECTED_LANGUAGE"):
        if wanted and lang not in wanted:
            continue
        total = float(grp["N"].sum()) or 1.0
        top = grp.sort_values("N", ascending=False).head(4)
        shares = {r.CULTURAL_FRAME: r.N / total for r in top.itertuples()}
        rest = 1.0 - sum(shares.values())
        if rest > 0.01:
            shares["other"] = rest
        frame_share_bar(lang, shares)


def render_divergence_figure(event_tag):
    try:
        cds = get_cds_matrix(session, event_tag)
    except Exception:
        return
    if cds is None or cds.empty:
        return
    cds = cds.copy()
    cds["pair"] = cds["LANGUAGE_A"] + " ⇄ " + cds["LANGUAGE_B"]
    st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
    _section_head("Figure · pairwise frame divergence", "Where the fault lines are.",
                  "Each pair's frame divergence. Past 0.34 (dashed) = cultural risk. "
                  "Source: CULTURAL_DIVERGENCE_SCORES.")
    xmax = max(0.65, float(cds["HEADLINE_SCORE"].max()))
    rule = (alt.Chart(pd.DataFrame({"x": [0.34]}))
            .mark_rule(color="#8B2A1F", strokeDash=[4, 3]).encode(x="x:Q"))
    dots = (
        alt.Chart(cds).mark_circle(size=130, opacity=0.9).encode(
            x=alt.X("HEADLINE_SCORE:Q", title="Frame divergence",
                    scale=alt.Scale(domain=[0, xmax])),
            y=alt.Y("pair:N", sort="-x", title=None,
                    axis=alt.Axis(labelFont="ui-monospace, SF Mono, Menlo",
                                  labelColor="#1C1A17", ticks=False, domain=False)),
            color=alt.condition(alt.datum.HEADLINE_SCORE >= 0.34,
                                alt.value("#8B2A1F"), alt.value("#1C1A17")),
            tooltip=[alt.Tooltip("pair:N", title="Pair"),
                     alt.Tooltip("HEADLINE_SCORE:Q", title="Frame div.", format=".2f"),
                     alt.Tooltip("SITUATION_LABEL:N", title="Situation")]))
    st.altair_chart((rule + dots).properties(height=28 * len(cds) + 40)
                    .configure_view(strokeWidth=0).configure_axis(grid=False),
                    use_container_width=True)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
events = list_event_tags(session)
if not events:
    page_header("AI cultural intelligence brief", "Read the room, on demand.",
                "A two-page cultural brief for any event in your corpus.")
    st.warning("No events found. Load demo data first (see docs/03_runbook.md).")
    st.stop()

languages = list_languages(session)


def render_inputs():
    c1, c2 = st.columns([1, 2])
    ev = c1.selectbox("Event", options=events, format_func=event_label)
    langs = c2.multiselect(
        "Target languages", options=languages,
        default=[l for l in ["en", "ja", "zh", "de", "es"] if l in languages][:5])
    gen = st.button("Generate brief", type="primary", use_container_width=True,
                    disabled=(not langs))
    return ev, langs, gen


have_result = "brief_result" in st.session_state

if have_result:
    state = st.session_state["brief_result"]
    title, sections = parse_brief(state["result"].get("brief_markdown", ""))
    if not title:
        title = f"Reading the room: {event_label(state['event'])}."
    lede = first_paragraph(sections[0][1]) if sections else ""
    _now = datetime.datetime.now()
    date = f"{_now.day} {_now:%b %Y}"
    page_header(f"AI cultural intelligence brief · {event_label(state['event'])} · {date}",
                title, lede)
    with st.expander("Generate a different brief", expanded=False):
        ev, langs, gen = render_inputs()
else:
    page_header("AI cultural intelligence brief", "Read the room, on demand.",
                "A two-page cultural brief for any event in your corpus: where the "
                "markets diverge, the dominant frames, and what to do about it. "
                "Source-cited, generated on demand.")
    ev, langs, gen = render_inputs()

if gen:
    t0 = datetime.datetime.now()
    with st.spinner("Synthesizing brief…"):
        try:
            r = call_generate_brief(
                session, ev, langs,
                requested_by=getattr(getattr(st, "user", None), "user_name", "unknown"))
            st.session_state["brief_result"] = {
                "result": r, "event": ev, "langs": langs,
                "elapsed": (datetime.datetime.now() - t0).total_seconds(),
            }
            st.rerun()
        except Exception as exc:
            st.error(f"Failed: {exc}")


# ===========================================================================
# POPULATED BRIEF
# ===========================================================================
def render_brief(state):
    r = state["result"]
    md = r.get("brief_markdown", "")
    _title, sections = parse_brief(md)
    n_sources = len(r.get("source_post_ids", []) or [])
    n_langs = len(r.get("target_languages", []) or state["langs"])

    # Meta row + actions
    meta_l, meta_r = st.columns([2, 1])
    meta_l.markdown(
        f"<div style='font-family:var(--mono); font-size:12px; color:var(--ink-muted);"
        f" letter-spacing:0.04em;'>{n_sources} SOURCES CITED · {n_langs} LANGUAGES · "
        f"{state['elapsed']:.0f}s · {r.get('model', '—')}</div>",
        unsafe_allow_html=True)
    meta_r.download_button("Download Markdown", data=(md or "").encode("utf-8"),
                           file_name=f"comprenda_brief_{state['event']}.md",
                           mime="text/markdown", use_container_width=True)
    st.divider()

    # TOC (best-effort sticky) + article
    toc_col, art_col = st.columns([1, 3], gap="large")
    with toc_col:
        toc = "".join(
            f"<li style='margin:4px 0;'>§ {i} · {h or 'Section'}</li>"
            for i, (h, _b) in enumerate(sections, 1))
        st.markdown(
            "<div style='position:sticky; top:16px;'>"
            "<div class='nu-kicker'>In this brief</div>"
            f"<ol style='list-style:none; padding:0; margin:8px 0 0; "
            f"font:400 13px/1.5 var(--sans); color:var(--ink-muted);'>{toc}</ol></div>",
            unsafe_allow_html=True)
    with art_col:
        for i, (head, body) in enumerate(sections, 1):
            st.markdown(f"<div class='nu-kicker'>§ {i}</div><h2>{head or ''}</h2>",
                        unsafe_allow_html=True)
            if body:
                st.markdown(body)
            if i < len(sections):
                st.divider()

        st.divider()
        render_frame_figure(state["event"], state["langs"])
        render_divergence_figure(state["event"])

        with st.expander("Sources cited (post_ids)", expanded=False):
            st.json(r.get("source_post_ids", []))
        with st.expander("Show raw markdown", expanded=False):
            st.code(md, language="markdown")


def render_panel():
    st.divider()
    _section_head("What's in a brief",
                  "Six sections, written like an intelligence report.")
    cols = st.columns(3, gap="medium")
    items = [
        ("Executive summary", "The verdict in three sentences: what's travelling, what isn't, what to watch."),
        ("Where the markets disagree", "The fault lines, ranked — which language pairs diverge, and on which axis."),
        ("Dominant frames", "What each market is actually talking about, frame by frame."),
        ("Risk flags", "The specific phrasings or frames that will misfire, and where."),
        ("Recommendations", "Concrete moves in priority order — lean in, repair, hedge."),
        ("Sources cited", "Representative post_ids; the brief shows its work."),
    ]
    for i, (h, p) in enumerate(items):
        with cols[i % 3]:
            st.markdown(f"""
              <div class='nu-card' style='min-height:130px; margin-bottom:16px;'>
                <div style='font:600 15px/1.3 var(--sans); color:var(--ink-strong);'>{h}</div>
                <div style='font:400 13px/1.5 var(--sans); color:var(--ink-muted);
                            margin-top:6px;'>{p}</div>
              </div>
            """, unsafe_allow_html=True)


if have_result:
    render_brief(st.session_state["brief_result"])
else:
    render_panel()
