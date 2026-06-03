"""Interaction smoke test — drives the hero flows and asserts REAL outputs render."""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STREAMLIT = HERE.parent
for p in (str(STREAMLIT), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ["COMPRENDA_DEMO"] = "1"

import fixtures
import snowflake.snowpark.context as _ctx
_ctx.get_active_session = lambda: fixtures.FakeSession()
sys.modules["lib.comprenda_queries"] = fixtures.build_query_module()

from streamlit.testing.v1 import AppTest  # noqa: E402

fails = []


def check(name, cond, detail=""):
    print(f"{'ok   ' if cond else 'FAIL '} {name}" + (f"  ({detail})" if detail else ""))
    if not cond:
        fails.append(name)


def ss(at, key, default=None):
    try:
        return at.session_state[key]
    except (KeyError, AttributeError):
        return default


def view(rel):
    return AppTest.from_file(str(STREAMLIT / "views" / rel), default_timeout=60)


# --- PLCS: score the Tesla draft across default markets (en, ja, fr, hi) -------
at = view("1_Pre_Launch_Risk.py").run()
at.text_area(key="plcs_draft").set_value("Own the future... individual freedom.").run()
# click the primary "Score cultural risk" button
[b for b in at.button if "Score cultural risk" in b.label][0].click().run()
res = ss(at, "plcs_results", {}).get("results", {})
check("PLCS no exception", not at.exception, str(list(at.exception)))
check("PLCS scored 4 markets", len(res) == 4, f"markets={list(res)}")
check("PLCS en is safe (25)", res.get("en", {}).get("plcs_score") == 25)
check("PLCS hi elevated (72)", res.get("hi", {}).get("plcs_score") == 72)
check("PLCS narrative is real", "cultural risk" in (res.get("hi", {}).get("risk_narrative", "")).lower())

# --- Divergence Matrix: switch events -> event-aware inline CDS path -----------
at = view("4_Divergence_Matrix.py").run()
at.selectbox(key="matrix_event").set_value("iPhone_17_launch").run()
title_iphone = at.title[0].value if at.title else ""
check("Matrix iPhone no exception", not at.exception, str(list(at.exception)))
check("Matrix iPhone populated", "fault" in title_iphone.lower() or "language" in title_iphone.lower(), title_iphone)
at.selectbox(key="matrix_event").set_value("K-pop_global_tour").run()
title_kpop = at.title[0].value if at.title else ""
check("Matrix switches per event", title_kpop and title_kpop != title_iphone, f"{title_iphone!r} -> {title_kpop!r}")

# --- AI Brief: generate for Tesla --------------------------------------------
at = view("8_AI_Brief.py").run()
at.selectbox[0].set_value("Tesla_robotaxi_debut").run()
[b for b in at.button if "Generate brief" in b.label][0].click().run()
br = ss(at, "brief_result", {})
md = br.get("result", {}).get("brief_markdown", "")
check("Brief no exception", not at.exception, str(list(at.exception)))
check("Brief markdown is real", len(md) > 1000 and "#" in md, f"len={len(md)}")
check("Brief event is Tesla", br.get("event") == "Tesla_robotaxi_debut")

# --- Translator: generate variants -------------------------------------------
at = view("2_Cultural_Translator.py").run()
at.text_area(key="translator_source").set_value("Own the future. Pure individual freedom.").run()
[b for b in at.button if "Generate adapted variants" in b.label][0].click().run()
tr = ss(at, "translator_results", {}).get("result", {})
check("Translator no exception", not at.exception, str(list(at.exception)))
check("Translator 3 variants", len(tr.get("variants", [])) == 3, f"n={len(tr.get('variants', []))}")

# --- Analog Retrieval: find analogs ------------------------------------------
at = view("7_Analog_Retrieval.py").run()
at.text_area(key="analog_query").set_value("individualist campaign in a collectivist market").run()
[b for b in at.button if b.label == "Find analogs"][0].click().run()
ar = ss(at, "analog_results", {}).get("r", {})
names = [a.get("case_name") for a in ar.get("analogs", [])]
check("Analog no exception", not at.exception, str(list(at.exception)))
check("Analog returns Levi's", any("Levi" in (n or "") for n in names), str(names))

# --- Narrative Search: query -------------------------------------------------
at = view("9_Narrative_Search.py").run()
at.text_input(key="nsearch_q").set_value("robotaxi").run()
[b for b in at.button if b.label == "Search"][0].click().run()
ns = ss(at, "nsearch_results", {}).get("df")
check("Narrative no exception", not at.exception, str(list(at.exception)))
check("Narrative returns rows", ns is not None and len(ns) > 0, f"rows={0 if ns is None else len(ns)}")

# --- Overview feed variety (recommendation #1) -------------------------------
feed = fixtures.plcs_scores_df(10)
n_drafts = feed["DRAFT_PREVIEW"].nunique() if not feed.empty else 0
check("Overview feed shows varied drafts", n_drafts > 1, f"distinct drafts={n_drafts}")

print("\n" + ("PASS" if not fails else "FAILURES: " + ", ".join(fails)))
sys.exit(1 if fails else 0)
