# `design/` — Comprenda redesign artifacts

This folder holds the **redesign reference material**, not live application code.
The running design system is implemented in `streamlit/lib/`
(`comprenda_theme.py` → `inject_css()`, `comprenda_components.py`, `ui.py`).

## Canonical — keep current; the build tracks these
- **`Claude-Code-Handoff.md`** — the redesign spec. CLAUDE.md points new
  contributors here.
- **`IMPLEMENTATION_NOTES.md`** — living build log: deviations from the spec,
  gotchas, and step status.

## Reference artboards — frozen mockups, NOT a live source of truth
These were the local critique/debugging canvas used while building the redesign.
The app is Streamlit (no React), so the `.jsx`/`.html` files don't run in
production; they're the visual reference the Streamlit pages were built to match.

- **`tokens.css`** — the original mockup design-token sheet. **The live tokens are
  in `streamlit/lib/comprenda_theme.py`; editing `tokens.css` does NOT change the
  app.** Kept as the design reference. If a token changes, change it in
  `streamlit/lib/` and (optionally) mirror it here so this stays a faithful snapshot.
- **`screens.jsx`**, **`design-canvas.jsx`**, **`index.html`** — the React/HTML
  preview canvas of the artboards.

> **Distinct from `streamlit/_harness/`** — that is the live local *mock-data*
> preview of the actual Streamlit-in-Snowflake app, and it stays in active use.
> The artboards here are static design references; the `_harness/` runs the real app.

## Local-only (gitignored)
- `.design-canvas.state.json` — the preview canvas tool's view-state (titles/labels).
  Not a deliverable; ignored in `.gitignore`.
