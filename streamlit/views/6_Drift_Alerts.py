"""Drift Alerts — subscribe entities to ongoing CDS monitoring.

Consistency pass (no artboard): subscriptions render as editorial cards with a
status pill; the add form keeps its exact logic. Query / proc calls unchanged.
"""
import streamlit as st
from snowflake.snowpark.context import get_active_session

from lib.comprenda_queries import (
    list_tracked_entities, add_tracked_entity, list_languages,
    find_matching_events,
)
from lib.comprenda_theme import inject_css
from lib.comprenda_components import page_header, section_head, pill

inject_css()
session = get_active_session()

page_header(
    "Cultural monitoring · drift alerts",
    "Know before it becomes a story.",
    "Subscribe a brand, product, or event. When divergence between any two markets "
    "spikes above your threshold, you get the signal first.",
)

# ---------------------------------------------------------------------------
# Flash messages carried across the post-subscribe rerun
# ---------------------------------------------------------------------------
for level, msg in st.session_state.pop("drift_flash", []):
    getattr(st, level)(msg)

# ---------------------------------------------------------------------------
# Existing subscriptions
# ---------------------------------------------------------------------------
section_head("Monitoring · active subscriptions", "What you're watching.")
entities = list_tracked_entities(session)
if entities.empty:
    st.markdown(
        "<div class='nu-card'><div style='font:400 15px/1.5 var(--serif); "
        "color:var(--ink-muted);'>Nothing under watch yet. Add your first "
        "subscription below — you'll be alerted when divergence between markets "
        "crosses your threshold.</div></div>", unsafe_allow_html=True)
else:
    for _, r in entities.iterrows():
        active = bool(r.get("ACTIVE", True))
        status = (pill("Active", tone="safe") if active else pill("Paused", tone="warn"))
        created = str(r.get("CREATED_AT", ""))[:10]
        st.markdown(
            "<div class='nu-card' style='display:flex; align-items:center; gap:16px; "
            "margin-bottom:8px;'>"
            "<div style='flex:1;'>"
            f"<div style='font:600 16px/1.2 var(--sans); color:var(--ink-strong);'>"
            f"{r['ENTITY_NAME']}</div>"
            f"<div style='font:400 11px/1 var(--mono); color:var(--ink-muted); "
            f"margin-top:4px;'>{r.get('OWNER_EMAIL', '')}</div>"
            "</div>"
            f"{pill(str(r.get('ENTITY_TYPE', '')).capitalize())}"
            f"<div style='font:400 11px/1.5 var(--mono); color:var(--ink-muted); "
            f"text-align:right;'>Δ {r.get('CDS_THRESHOLD_DELTA', '—')} · "
            f"abs {r.get('CDS_THRESHOLD_ABS', '—')}<br>since {created}</div>"
            f"{status}"
            "</div>", unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# Add new
# ---------------------------------------------------------------------------
section_head("Add a subscription", "Put something new under watch.")
languages = list_languages(session)

with st.form("add_entity"):
    c1, c2 = st.columns(2)
    name = c1.text_input("Entity name", placeholder="e.g. iPhone 17, Olympics 2026")
    email = c2.text_input("Owner email", value=st.session_state.get("user_email", ""))
    langs = st.multiselect(
        "Languages to monitor", options=languages,
        default=[l for l in ["en", "ja", "zh", "de", "es", "ko"] if l in languages][:4],
    )
    c3, c4 = st.columns(2)
    delta = c3.number_input("Delta threshold (24h Δ-CDS)", value=0.15,
                            min_value=0.05, max_value=0.5, step=0.05)
    abs_t = c4.number_input("Absolute CDS threshold", value=0.55,
                            min_value=0.30, max_value=0.95, step=0.05)
    if st.form_submit_button("Subscribe", type="primary"):
        if name.strip() and email.strip() and langs:
            try:
                add_tracked_entity(session, name.strip(), email.strip(), langs,
                                   float(delta), float(abs_t))
                # Immediately check whether this entity matches any existing
                # event_tags — warn the user if it matches nothing, so they
                # know to check their naming before assuming alerts will fire.
                matched = find_matching_events(session, name.strip())
                flash = [("success", f"Subscribed: {name}")]
                if matched:
                    flash.append((
                        "info",
                        f"✅ Matched {len(matched)} existing event(s): "
                        + ", ".join(f"`{e}`" for e in matched)
                        + ". Alerts will fire once CDS crosses your threshold.",
                    ))
                else:
                    flash.append((
                        "warning",
                        f"⚠️ No existing events match **{name}**. "
                        "Alerts will only fire once matching event data is loaded "
                        "into the corpus. Check that your entity name resembles "
                        "an `event_tag` in your data (e.g. spaces become underscores).",
                    ))
                # Stash messages so they survive the rerun that refreshes the
                # subscriptions table above.
                st.session_state["drift_flash"] = flash
                st.rerun()
            except Exception as exc:
                st.error(f"Failed: {exc}")
        else:
            st.error("Name, email, and at least one language required.")

st.caption(
    "💡 Alerts are dispatched hourly by `internal.drift_check_task`. "
    "Resume the task with `ALTER TASK internal.drift_check_task RESUME;` if "
    "you've left it suspended during development."
)
