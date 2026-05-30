// Comprenda redesign — screen components rendered into DCArtboards.
// All screens share AppChrome (top bar + left nav) and the design tokens
// defined in the <style> block in index.html.

const { useState, useMemo } = React;

// ---------------------------------------------------------------------------
// Shared chrome
// ---------------------------------------------------------------------------

const NAV_ITEMS = [
  { key: 'home',       label: 'Overview',           glyph: '◉' },
  { key: 'plcs',       label: 'Pre-launch risk',    glyph: '◐' },
  { key: 'translator', label: 'Cultural translator',glyph: '⇄' },
  { key: 'event',      label: 'Event explorer',     glyph: '◇' },
  { key: 'matrix',     label: 'Divergence matrix',  glyph: '▦' },
  { key: 'frames',     label: 'Frame distribution', glyph: '▥' },
  { key: 'drift',      label: 'Drift alerts',       glyph: '◔' },
  { key: 'analog',     label: 'Analog retrieval',   glyph: '◊' },
  { key: 'brief',      label: 'AI brief',           glyph: '▤' },
  { key: 'search',     label: 'Narrative search',   glyph: '∃' },
];

function Omnibox({ expanded, query, answer }) {
  if (expanded) {
    return (
      <div className="nu-omni nu-omni--expanded">
        <div className="nu-omni-input-row">
          <span className="nu-omni-icon">∃</span>
          <span className="nu-omni-query">{query}</span>
          <span className="nu-omni-hint">esc to close</span>
        </div>
        {answer && (
          <div className="nu-omni-answer">
            <div className="nu-omni-answer-text">{answer.text}</div>
            {answer.sources && (
              <div className="nu-omni-answer-sources">
                {answer.sources.map((s, i) => (
                  <span key={i} className="nu-omni-source">{s}</span>
                ))}
              </div>
            )}
            {answer.sql && (
              <details className="nu-omni-sql-wrap">
                <summary className="nu-omni-sql-toggle">View generated SQL</summary>
                <pre className="nu-omni-sql">{answer.sql}</pre>
              </details>
            )}
          </div>
        )}
      </div>
    );
  }
  return (
    <div className="nu-omni">
      <span className="nu-omni-placeholder">Ask anything about the corpus…</span>
      <span className="nu-omni-kbd">/</span>
      <span className="nu-omni-kbd">⌘K</span>
    </div>
  );
}

function AppChrome({ active, children, breadcrumb, omniExpanded, omniQuery, omniAnswer }) {
  return (
    <div className="nu-app">
      <div className="nu-shell">
        {/* Left nav */}
        <aside className="nu-nav">
          <div className="nu-brand">
            <div className="nu-wordmark">Comprenda</div>
            <div className="nu-tagline">Don't translate. Understand.</div>
          </div>
          <div className="nu-nav-section">
            <div className="nu-nav-kicker">Workbench</div>
            {NAV_ITEMS.slice(0,4).map(n => (
              <NavItem key={n.key} item={n} active={active===n.key} />
            ))}
          </div>
          <div className="nu-nav-section">
            <div className="nu-nav-kicker">Analysis</div>
            {NAV_ITEMS.slice(4,8).map(n => (
              <NavItem key={n.key} item={n} active={active===n.key} />
            ))}
          </div>
          <div className="nu-nav-section">
            <div className="nu-nav-kicker">Synthesis</div>
            {NAV_ITEMS.slice(8).map(n => (
              <NavItem key={n.key} item={n} active={active===n.key} />
            ))}
          </div>
          <div className="nu-nav-footer">
            <div className="nu-nav-footer-row">
              <span className="nu-dot nu-dot--safe" />
              <span>Corpus · 24h fresh</span>
            </div>
            <div className="nu-nav-footer-row nu-muted">
              v2.4 · claude-4-sonnet
            </div>
          </div>
        </aside>

        {/* Main */}
        <main className="nu-main">
          <div className="nu-topbar">
            {breadcrumb && <div className="nu-crumb">{breadcrumb}</div>}
            <Omnibox expanded={omniExpanded} query={omniQuery} answer={omniAnswer} />
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}

function AboutThisRun({ items, defaultOpen = false }) {
  return (
    <details className="nu-about" open={defaultOpen ? true : undefined}>
      <summary className="nu-about-summary">
        <span className="nu-about-kicker">About this run</span>
        <span className="nu-about-hint">{items.length} fields · click to expand</span>
      </summary>
      <div className="nu-about-grid">
        {items.map(([label, value], i) => (
          <div className="nu-about-row" key={i}>
            <span className="nu-about-label">{label}</span>
            <span className="nu-about-value">{value}</span>
          </div>
        ))}
      </div>
    </details>
  );
}

function NavItem({ item, active }) {
  return (
    <a className={'nu-nav-item' + (active ? ' is-active' : '')}>
      <span className="nu-nav-glyph">{item.glyph}</span>
      <span className="nu-nav-label">{item.label}</span>
    </a>
  );
}

// ---------------------------------------------------------------------------
// Reusable primitives
// ---------------------------------------------------------------------------

function Kicker({ children }) { return <div className="nu-kicker">{children}</div>; }
function Rule({ inset })       { return <hr className={'nu-rule' + (inset ? ' nu-rule--inset' : '')} />; }

function Metric({ label, value, delta, trend, kind }) {
  return (
    <div className="nu-metric">
      <div className="nu-metric-label">{label}</div>
      <div className="nu-metric-value">{value}</div>
      {delta && (
        <div className={'nu-metric-delta nu-metric-delta--' + (kind || 'neutral')}>
          <span>{trend === 'up' ? '▲' : trend === 'down' ? '▼' : '·'}</span>
          {delta}
        </div>
      )}
    </div>
  );
}

function RiskBadge({ score, size = 'md' }) {
  const band =
    score < 35 ? 'safe' :
    score < 55 ? 'caution' :
    score < 75 ? 'warn' : 'risk';
  const label =
    band === 'safe' ? 'Low' :
    band === 'caution' ? 'Moderate' :
    band === 'warn' ? 'Elevated' : 'High';
  return (
    <span className={`nu-badge nu-badge--${band} nu-badge--${size}`}>
      <span className="nu-badge-dot" />
      {label}
    </span>
  );
}

function Pill({ children, tone='neutral' }) {
  return <span className={`nu-pill nu-pill--${tone}`}>{children}</span>;
}

// ---------------------------------------------------------------------------
// SCREEN 1 — Overview / Home dashboard
// ---------------------------------------------------------------------------

function ScreenOverview() {
  return (
    <AppChrome active="home" breadcrumb="Overview · acme.global-marketing">
      <section className="nu-hero">
        <Kicker>Tuesday · 27 May 2026 · 09:14 PT</Kicker>
        <h1 className="nu-h1">Three signals worth your morning.</h1>
        <p className="nu-lede">
          Two new drift events, one elevated pre-launch score from
          overnight. Nothing in the corpus today contradicts the brand
          narrative — but Japan and Korea continue to drift apart on
          electrification messaging. The full read is below.
        </p>
      </section>

      <Rule />

      <section className="nu-strip">
        <Metric label="Events tracked"      value="142"     delta="+6 wk" trend="up"   kind="neutral" />
        <Metric label="Languages analyzed"  value="38"      delta="stable" kind="neutral" />
        <Metric label="Posts in corpus"     value="2.4M"    delta="+118k wk" trend="up" kind="neutral" />
        <Metric label="Drift events · 24h"  value="2"       delta="from 0" trend="up" kind="warn" />
        <Metric label="Pre-launch risk · 24h" value="7"   delta="1 ≥60"  kind="warn" />
        <Metric label="Briefs generated · 7d" value="14"    delta="+3"     trend="up" kind="neutral" />
      </section>

      <Rule />

      <div className="nu-twocol">
        <section>
          <div className="nu-section-head">
            <Kicker>Drift alerts · 24h</Kicker>
            <h2 className="nu-h2">Where communities are pulling apart.</h2>
            <p className="nu-dek">
              Sorted by Δ-CDS. <em>Lens-split</em> means same words,
              different frame; <em>mood-split</em> means same frame, opposite feeling.
            </p>
          </div>

          <ul className="nu-feed">
            <li className="nu-feed-row">
              <div className="nu-feed-head">
                <div>
                  <span className="nu-feed-entity">iPhone 17 launch</span>
                  <span className="nu-feed-pair">ja ⇄ ko</span>
                </div>
                <div className="nu-feed-delta nu-feed-delta--risk">
                  <span className="nu-mono">0.41 → 0.62</span>
                  <span className="nu-feed-trend">Δ +0.21</span>
                </div>
              </div>
              <div className="nu-feed-body">
                Korean coverage reframed the device as a <Pill tone="risk">Status loss</Pill> story
                after the price hike; Japanese discourse stayed on
                <Pill>Craft</Pill> and <Pill>Reliability</Pill>. Lens-split.
              </div>
              <div className="nu-feed-foot">
                <span className="nu-mono nu-muted">detected · 03:42 PT</span>
                <a className="nu-link">Open event →</a>
              </div>
            </li>

            <li className="nu-feed-row">
              <div className="nu-feed-head">
                <div>
                  <span className="nu-feed-entity">Olympics 2026 · opening</span>
                  <span className="nu-feed-pair">en ⇄ zh</span>
                </div>
                <div className="nu-feed-delta nu-feed-delta--warn">
                  <span className="nu-mono">0.33 → 0.49</span>
                  <span className="nu-feed-trend">Δ +0.16</span>
                </div>
              </div>
              <div className="nu-feed-body">
                English-language posts shifted to a <Pill tone="warn">Geopolitical</Pill>
                frame; Chinese-language posts held on
                <Pill>National pride</Pill>. Mood-split.
              </div>
              <div className="nu-feed-foot">
                <span className="nu-mono nu-muted">detected · 06:11 PT</span>
                <a className="nu-link">Open event →</a>
              </div>
            </li>

            <li className="nu-feed-row nu-feed-row--quiet">
              <div className="nu-feed-head">
                <div>
                  <span className="nu-feed-entity">EV tax credit · policy</span>
                  <span className="nu-feed-pair">de ⇄ fr</span>
                </div>
                <div className="nu-feed-delta">
                  <span className="nu-mono">0.18 → 0.19</span>
                  <span className="nu-feed-trend">Δ +0.01</span>
                </div>
              </div>
              <div className="nu-feed-body nu-muted">
                Held within tolerance.
              </div>
            </li>
          </ul>
        </section>

        <section>
          <div className="nu-section-head">
            <Kicker>Pre-launch scores · 24h</Kicker>
            <h2 className="nu-h2">What's at the door.</h2>
            <p className="nu-dek">
              Seven drafts scored overnight. One elevated; one to watch.
            </p>
          </div>

          <ul className="nu-feed">
            <PLCSRow draft="Live Free, Drive Fast — the electric sports car that puts you first."
                     market="ja" score={74} who="m.chen@acme.com" when="04:18 PT" />
            <PLCSRow draft="More than a phone. A vow."
                     market="zh" score={58} who="a.kapoor@acme.com" when="06:02 PT" />
            <PLCSRow draft="Reimagined for the way Europe drives."
                     market="de" score={31} who="t.weber@acme.com" when="07:45 PT" />
            <PLCSRow draft="A quieter kind of power."
                     market="ko" score={22} who="m.chen@acme.com" when="08:30 PT" tail />
          </ul>
        </section>
      </div>

      <Rule />

      <section className="nu-onward">
        <Kicker>What's next</Kicker>
        <div className="nu-onward-grid">
          <a className="nu-onward-card">
            <div className="nu-onward-num">01</div>
            <div className="nu-onward-title">Generate this morning's brief</div>
            <div className="nu-onward-body">
              Two-page synthesis across the iPhone 17 launch in English, Japanese, Korean, German, and Chinese markets.
              ~40 seconds. Source-cited.
            </div>
            <div className="nu-onward-cta">Generate →</div>
          </a>
          <a className="nu-onward-card">
            <div className="nu-onward-num">02</div>
            <div className="nu-onward-title">Translate the elevated draft</div>
            <div className="nu-onward-body">
              The 74-score Japanese line. Cultural Translator can
              produce three frame-preserving variants.
            </div>
            <div className="nu-onward-cta">Open translator →</div>
          </a>
          <a className="nu-onward-card">
            <div className="nu-onward-num">03</div>
            <div className="nu-onward-title">Subscribe a new entity</div>
            <div className="nu-onward-body">
              Add a brand, product, or campaign to ongoing drift
              monitoring. Email + Slack alerts.
            </div>
            <div className="nu-onward-cta">Add subscription →</div>
          </a>
        </div>
      </section>
    </AppChrome>
  );
}

function PLCSRow({ draft, market, score, who, when, tail }) {
  return (
    <li className={'nu-feed-row' + (tail ? ' nu-feed-row--quiet' : '')}>
      <div className="nu-feed-head">
        <div>
          <span className="nu-feed-entity">"{draft}"</span>
        </div>
        <div className="nu-plcs-score">
          <span className="nu-mono">{score}</span>
          <RiskBadge score={score} size="sm" />
        </div>
      </div>
      <div className="nu-feed-foot">
        <span className="nu-mono nu-muted">{market} · by {who} · {when}</span>
        <a className="nu-link">Open result →</a>
      </div>
    </li>
  );
}

// ---------------------------------------------------------------------------
// SCREEN 2 — Pre-Launch Risk (signature)
// ---------------------------------------------------------------------------

const PLCS_MARKETS = [
  { code: 'ja', name: 'Japan',  score: 74, conf: 0.86, band: 'risk',
    frames: ['Status quo', 'Collectivist', 'Craft reverence'],
    one: 'Reads as American individualism in a market that codes self-promotion as low-status.',
    contributors: [
      { axis: 'frame', weight: 0.42, note: 'Live Free / Drive Fast register as individualist boast' },
      { axis: 'lexicon', weight: 0.28, note: '"puts you first" — direct-comparison phrasing' },
      { axis: 'analogs', weight: 0.20, note: '3 historical near-miss launches in the Japanese corpus' },
      { axis: 'sentiment', weight: 0.10, note: 'EV discourse currently neutral in Japan' },
    ],
  },
  { code: 'ko', name: 'Korea',  score: 61, conf: 0.79, band: 'warn',
    frames: ['Status quo', 'Collectivist', 'Reform seeking'],
    one: 'Status-loss framing risk after recent price-hike discourse; "puts you first" reads as insensitive.',
    contributors: [
      { axis: 'frame', weight: 0.35, note: 'Individualist register, current status-loss discourse' },
      { axis: 'analogs', weight: 0.30, note: 'iPhone 17 Japan–Korea drift event flagged 6 hrs ago' },
      { axis: 'lexicon', weight: 0.20, note: '"first" — comparison register' },
      { axis: 'sentiment', weight: 0.15, note: 'EV neutral-to-cautious' },
    ],
  },
  { code: 'de', name: 'Germany',score: 38, conf: 0.82, band: 'caution',
    frames: ['Pragmatic', 'Reform seeking'],
    one: 'Mostly aligned; "fast" reads as performance, not recklessness, but verify Autobahn context.',
    contributors: [],
  },
  { code: 'fr', name: 'France', score: 29, conf: 0.74, band: 'safe',
    frames: ['Individualist', 'Reform seeking'],
    one: 'Frame-compatible. "Live free" maps cleanly to French liberté discourse.',
    contributors: [],
  },
];

function ScreenPLCS() {
  return (
    <AppChrome active="plcs" breadcrumb="Workbench / Pre-launch risk">
      <section className="nu-hero">
        <Kicker>Pre-launch cultural risk</Kicker>
        <h1 className="nu-h1">Will this travel?</h1>
        <p className="nu-lede">
          Score a draft tagline, headline, or campaign line for cultural
          risk in any market in your corpus. The score is grounded in
          historical content — analogs are nameable.
        </p>
      </section>

      <Rule />

      <div className="nu-plcs-input">
        <div className="nu-plcs-input-l">
          <label className="nu-label">Draft</label>
          <div className="nu-field nu-field--draft">
            <div className="nu-draft-text">
              Live Free, Drive Fast — the new electric sports car that puts you first.
            </div>
            <div className="nu-draft-meta">
              <span className="nu-mono nu-muted">12 words · en · source: Acme · campaign-2026Q3 · v3</span>
              <span className="nu-mono nu-muted">⌘↩ to score</span>
            </div>
          </div>
        </div>
        <div className="nu-plcs-input-r">
          <label className="nu-label">Target markets</label>
          <div className="nu-chips">
            <span className="nu-chip nu-chip--on">ja Japan</span>
            <span className="nu-chip nu-chip--on">ko Korea</span>
            <span className="nu-chip nu-chip--on">de Germany</span>
            <span className="nu-chip nu-chip--on">fr France</span>
            <span className="nu-chip">+ es</span>
            <span className="nu-chip">+ zh</span>
          </div>
          <label className="nu-label nu-label--space">Source</label>
          <div className="nu-select">en · English  ▾</div>
        </div>
      </div>

      <Rule />

      {/* Headline score band */}
      <section className="nu-section-head">
        <Kicker>Result · scored against 2.4M-post corpus · 38 seconds</Kicker>
        <h2 className="nu-h2">One of four markets is unsafe to ship as drafted.</h2>
        <p className="nu-dek">
          Japan scores 74/100 with 86% confidence. The driver is frame-mismatch,
          not language; translation alone will not fix it.
        </p>
      </section>

      <div className="nu-plcs-grid">
        {PLCS_MARKETS.map(m => <PLCSCard key={m.code} m={m} />)}
      </div>

      <Rule />

      {/* Risk spectrum — signature visualization */}
      <section>
        <div className="nu-section-head">
          <Kicker>Risk spectrum · positioned against historical analogs</Kicker>
          <h2 className="nu-h2">Where this draft sits, market by market.</h2>
        </div>
        <RiskSpectrum />
      </section>

      <Rule />

      {/* Deep narrative — Japan */}
      <section className="nu-narrative">
        <div className="nu-section-head">
          <Kicker>Narrative · Japan</Kicker>
          <h2 className="nu-h2">Why it scores 74.</h2>
        </div>

        <div className="nu-narr-body">
          <p>
            The phrase <em>"puts you first"</em> reads in Japanese discourse as
            an individualist boast — a register that performs poorly across
            recent automotive launches in the corpus. Three near-miss cases
            since 2022 used analogous self-comparison phrasing and
            underperformed in social sentiment by 18–34 points.
          </p>
          <p>
            The deeper issue is frame. The draft uses an
            <Pill tone="warn">Individualist</Pill> frame against a market
            currently coded as <Pill>Status quo</Pill> and
            <Pill>Craft reverence</Pill>. Cultural drift on the iPhone 17
            launch six hours ago indicates the surrounding discourse has
            tightened on status-loss anxiety, which amplifies the mismatch.
          </p>
        </div>

        <div className="nu-narr-grid">
          <div className="nu-narr-col">
            <div className="nu-narr-kicker">Contributors to score</div>
            {PLCS_MARKETS[0].contributors.map((c, i) => (
              <div className="nu-contrib" key={i}>
                <div className="nu-contrib-l">
                  <div className="nu-contrib-axis">{c.axis}</div>
                  <div className="nu-contrib-bar">
                    <div className="nu-contrib-fill" style={{width: (c.weight * 100) + '%'}} />
                  </div>
                  <div className="nu-mono nu-contrib-w">{(c.weight * 100).toFixed(0)}%</div>
                </div>
                <div className="nu-contrib-note">{c.note}</div>
              </div>
            ))}
          </div>

          <div className="nu-narr-col">
            <div className="nu-narr-kicker">Three historical analogs</div>
            <Analog year="2024" co="Detroit Motors" case="‘You First. Always.’ · Japan launch"
                    outcome="Pulled within 11 days · −22pt sentiment" gap="0.08" />
            <Analog year="2022" co="Westbrook EV" case="‘The road belongs to you.’ · Japan launch"
                    outcome="Recovered after copy revision · −18pt initial" gap="0.11" />
            <Analog year="2021" co="HRZN Auto" case="‘Drive your way.’ · Japan launch"
                    outcome="Underperformed segment · −34pt sentiment" gap="0.13" />
          </div>
        </div>
      </section>

      <Rule />

      <section className="nu-cta-band">
        <div>
          <Kicker>Recommended next move</Kicker>
          <h2 className="nu-h2 nu-cta-h">Adapt for Japan and Korea before ship.</h2>
          <p className="nu-dek">
            Cultural Translator can produce three frame-preserving variants
            — collectivist, craft-reverence, and pragmatic — each with a
            rationale and an updated risk score.
          </p>
        </div>
        <div className="nu-cta-actions">
          <button className="nu-btn nu-btn--primary">Open Translator with this draft →</button>
          <button className="nu-btn">Export as PDF</button>
          <button className="nu-btn">Share with team</button>
        </div>
      </section>

      <AboutThisRun defaultOpen items={[
        ['Session', <span className="nu-mono">plcs_2k4f9_a3b1</span>],
        ['Run started', '27 May 2026 · 09:14:32 PT'],
        ['Duration', '38 seconds'],
        ['Requested by', 'm.chen@acme.com'],
        ['Model', <span className="nu-mono">claude-4-sonnet</span>],
        ['Prompt version', <span className="nu-mono">plcs-v2.4</span>],
        ['Corpus snapshot', '27 May 2026 · 06:00 PT'],
        ['Reproducible', 'Yes — same draft + corpus snapshot yields the same score'],
      ]} />
    </AppChrome>
  );
}

function PLCSCard({ m }) {
  return (
    <div className={`nu-plcs-card nu-plcs-card--${m.band}`}>
      <div className="nu-plcs-card-top">
        <div className="nu-plcs-card-market">
          <span className="nu-mono nu-plcs-card-code">{m.code}</span>
          <span className="nu-plcs-card-name">{m.name}</span>
        </div>
        <RiskBadge score={m.score} />
      </div>
      <div className="nu-plcs-card-score">
        <span className="nu-plcs-card-n">{m.score}</span>
        <span className="nu-plcs-card-denom">/100</span>
      </div>
      <div className="nu-plcs-card-conf">
        <div className="nu-conf-bar">
          <div className="nu-conf-fill" style={{width: (m.conf * 100) + '%'}} />
        </div>
        <span className="nu-mono">{(m.conf * 100).toFixed(0)}% conf</span>
      </div>
      <div className="nu-plcs-card-one">{m.one}</div>
      <div className="nu-plcs-card-frames">
        {m.frames.map(f => <Pill key={f}>{f}</Pill>)}
      </div>
    </div>
  );
}

function RiskSpectrum() {
  // 0 to 100 axis, draw bands, markers per market, and historical analogs as
  // ticks behind the markers.
  const markets = PLCS_MARKETS;
  const analogs = [
    { x: 68, label: 'You First. Always. · 2024' },
    { x: 71, label: 'Drive your way. · 2021' },
    { x: 66, label: 'The road belongs… · 2022' },
    { x: 41, label: 'Reimagined for the road · 2023' },
  ];
  return (
    <div className="nu-spec">
      <div className="nu-spec-axis">
        <div className="nu-spec-band nu-spec-band--safe"    style={{ left: '0%',  width: '35%' }} />
        <div className="nu-spec-band nu-spec-band--caution" style={{ left: '35%', width: '20%' }} />
        <div className="nu-spec-band nu-spec-band--warn"    style={{ left: '55%', width: '20%' }} />
        <div className="nu-spec-band nu-spec-band--risk"    style={{ left: '75%', width: '25%' }} />
        {analogs.map((a, i) => (
          <div key={i} className="nu-spec-analog" style={{ left: a.x + '%' }} title={a.label}>
            <div className="nu-spec-analog-tick" />
          </div>
        ))}
        {markets.map((m, i) => (
          <div key={m.code} className="nu-spec-marker" style={{ left: m.score + '%' }}>
            <div className="nu-spec-marker-line" />
            <div className="nu-spec-marker-pill">
              <span className="nu-mono">{m.code}</span>
              <span>{m.score}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="nu-spec-scale">
        <span>0 · safe</span>
        <span>35</span>
        <span>55</span>
        <span>75</span>
        <span>100 · do not ship</span>
      </div>
      <div className="nu-spec-legend">
        <span><span className="nu-spec-legend-tick" /> historical analog from corpus</span>
        <span className="nu-muted">Hover a tick for case</span>
      </div>
    </div>
  );
}

function Analog({ year, co, case: caseName, outcome, gap }) {
  return (
    <div className="nu-analog">
      <div className="nu-analog-l">
        <div className="nu-mono nu-analog-year">{year}</div>
        <div className="nu-mono nu-muted nu-analog-gap">gap {gap}</div>
      </div>
      <div className="nu-analog-r">
        <div className="nu-analog-co">{co}</div>
        <div className="nu-analog-case">{caseName}</div>
        <div className="nu-analog-out">{outcome}</div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// SCREEN 3 — AI Brief
// ---------------------------------------------------------------------------

function ScreenBrief() {
  return (
    <AppChrome active="brief" breadcrumb={<>Synthesis / AI brief · <span className="nu-mono">iphone17_launch</span></>}>
      <section className="nu-hero">
        <Kicker>AI cultural intelligence brief · <span className="nu-mono">iphone17_launch</span> · 27 May 2026</Kicker>
        <h1 className="nu-h1">Two prices, four stories, one launch.</h1>
        <p className="nu-lede">
          Across English, Japanese, Chinese, German, and Korean, the iPhone
          17 launch is being discussed in four mutually-exclusive frames.
          The Western and Japanese narratives are converging on
          <em> craft </em>; the Korean discourse has shifted decisively to
          <em> status-loss</em>. This brief reads the room and recommends
          where to lean in.
        </p>
        <div className="nu-brief-meta">
          <span className="nu-mono nu-muted">12,418 posts · 5 languages · 38 seconds · sources cited</span>
          <span className="nu-brief-actions">
            <button className="nu-btn nu-btn--ghost">Copy markdown</button>
            <button className="nu-btn nu-btn--ghost">Download PDF</button>
            <button className="nu-btn">Share</button>
          </span>
        </div>
      </section>

      <Rule />

      <div className="nu-brief-grid">
        <aside className="nu-brief-toc">
          <div className="nu-brief-toc-kicker">In this brief</div>
          <ol className="nu-brief-toc-list">
            <li><a>Executive summary</a></li>
            <li><a>Where the markets disagree</a></li>
            <li><a>Dominant frames per language</a></li>
            <li><a>Recommendations</a></li>
          </ol>
          <div className="nu-brief-toc-meta">
            <div><span className="nu-muted">Generated</span> 09:11 PT</div>
            <div><span className="nu-muted">Requested by</span> m.chen@acme.com</div>
            <div><span className="nu-muted">Model</span> claude-4-sonnet</div>
            <div><span className="nu-muted">Confidence</span> 0.84</div>
          </div>
        </aside>

        <article className="nu-brief-body">
          <section>
            <Kicker>§ 1 · Executive summary</Kicker>
            <h2 className="nu-h2">The launch is travelling, with one outlier.</h2>
            <p>
              Four of five language communities are converging on a
              <Pill>Craft</Pill> frame for the device itself. The price
              uplift is doing different work in each market: across
              English, German, and French markets it reads as
              <Pill>Premium affirmation</Pill>; in Japan it is being
              absorbed into <Pill>Craft reverence</Pill>; in Korea it
              has become a <Pill tone="risk">Status loss</Pill> story
              within 48 hours. Cultural divergence between the Japanese
              and Korean communities on this event is 0.62 — the
              highest pair in our 2.4M-post corpus this month.
            </p>
            <ul className="nu-brief-bullets">
              <li><strong>Lean in:</strong> the craft frame is doing free work in English, Japanese, German, and French markets — amplify, don't translate.</li>
              <li><strong>Repair:</strong> Korean messaging needs an explicit value-anchor before any new creative ships.</li>
              <li><strong>Watch:</strong> Chinese discourse is currently on national-pride; that could flip with one geopolitical news cycle.</li>
            </ul>
          </section>

          <Rule inset />

          <section>
            <Kicker>§ 2 · Where the markets disagree</Kicker>
            <h2 className="nu-h2">The fault line: Japan and Korea.</h2>
            <p>
              On every other pair, frame-divergence is within tolerance.
              The Japan–Korea pair is at 0.62 — well past the 0.34
              cultural-risk threshold. The two communities are looking
              at the same event through different lenses; this is not a
              translation problem.
            </p>
            <FauxChart />
            <p className="nu-cap">
              Fig. 1 · Frame divergence across all language pairs in the
              corpus for <span className="nu-mono">iphone17_launch</span>.
              Above 0.34 = cultural risk. Source: CULTURAL_DIVERGENCE_SCORES, 27 May 09:08 PT.
            </p>
          </section>

          <Rule inset />

          <section>
            <Kicker>§ 3 · Dominant frames</Kicker>
            <h2 className="nu-h2">What each market is actually talking about.</h2>
            <div className="nu-frames">
              <FrameRow lang="en" name="English" frames={[
                { f: 'Craft',                 share: 0.41 },
                { f: 'Premium affirmation',   share: 0.27 },
                { f: 'Price anxiety',         share: 0.12 },
                { f: 'Other',                 share: 0.20 },
              ]} />
              <FrameRow lang="ja" name="Japanese" frames={[
                { f: 'Craft reverence',       share: 0.48 },
                { f: 'Reliability',           share: 0.24 },
                { f: 'Status quo',            share: 0.15 },
                { f: 'Other',                 share: 0.13 },
              ]} />
              <FrameRow lang="ko" name="Korean" frames={[
                { f: 'Status loss',           share: 0.39, risk: true },
                { f: 'Price anxiety',         share: 0.28 },
                { f: 'Craft',                 share: 0.16 },
                { f: 'Other',                 share: 0.17 },
              ]} />
              <FrameRow lang="zh" name="Chinese" frames={[
                { f: 'National pride',        share: 0.36 },
                { f: 'Premium affirmation',   share: 0.22 },
                { f: 'Craft',                 share: 0.20 },
                { f: 'Other',                 share: 0.22 },
              ]} />
              <FrameRow lang="de" name="German" frames={[
                { f: 'Pragmatic',             share: 0.42 },
                { f: 'Craft',                 share: 0.28 },
                { f: 'Premium affirmation',   share: 0.14 },
                { f: 'Other',                 share: 0.16 },
              ]} />
            </div>
          </section>

          <Rule inset />

          <section>
            <Kicker>§ 4 · Recommendations</Kicker>
            <h2 className="nu-h2">Three moves, in priority order.</h2>
            <ol className="nu-recs">
              <li>
                <div className="nu-rec-h">
                  <span className="nu-rec-n">01</span>
                  <span className="nu-rec-title">Pull the Korean status-loss frame forward.</span>
                </div>
                <p>Lead Korean placements with an explicit value-anchor — the existing creative is being absorbed into a discourse you don't want.</p>
              </li>
              <li>
                <div className="nu-rec-h">
                  <span className="nu-rec-n">02</span>
                  <span className="nu-rec-title">Amplify craft across the four converging markets; don't dilute it.</span>
                </div>
                <p>The craft frame is doing free work — resist the temptation to translate it into something more "exciting" in any of these four markets.</p>
              </li>
              <li>
                <div className="nu-rec-h">
                  <span className="nu-rec-n">03</span>
                  <span className="nu-rec-title">Quietly hedge Chinese national-pride exposure.</span>
                </div>
                <p>Have a frame-neutral fallback creative ready; the current frame is one news cycle away from flipping.</p>
              </li>
            </ol>
          </section>

          <AboutThisRun defaultOpen items={[
            ['Session', <span className="nu-mono">brief_5f7a_c2d8</span>],
            ['Generated', '27 May 2026 · 09:11:08 PT'],
            ['Duration', '38 seconds'],
            ['Requested by', 'm.chen@acme.com'],
            ['Model', <span className="nu-mono">claude-4-sonnet</span>],
            ['Prompt version', <span className="nu-mono">brief-v1.2</span>],
            ['Corpus snapshot', '27 May 2026 · 06:00 PT'],
            ['Posts surveyed', <span className="nu-mono">12,418</span>],
            ['Confidence', <span className="nu-mono">0.84</span>],
            ['Reproducible', 'Yes — same corpus snapshot yields the same brief'],
          ]} />
        </article>
      </div>
    </AppChrome>
  );
}

function FrameRow({ lang, name, frames }) {
  return (
    <div className="nu-frame-row">
      <div className="nu-frame-lang">
        <span className="nu-mono">{lang}</span>
        <span className="nu-frame-name">{name}</span>
      </div>
      <div className="nu-frame-bar">
        {frames.map((f, i) => (
          <div key={i}
               className={'nu-frame-seg' + (f.risk ? ' nu-frame-seg--risk' : '')}
               style={{width: (f.share * 100) + '%'}}
               title={`${f.f} · ${(f.share*100).toFixed(0)}%`}>
            {f.share >= 0.18 && <span>{f.f}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}

// Fake "small multiples" / dotplot of frame-divergence per pair, used inside
// the brief — illustrative only, draws with CSS.
function FauxChart() {
  const pairs = [
    { a: 'ja', b: 'ko', v: 0.62 },
    { a: 'en', b: 'ko', v: 0.41 },
    { a: 'zh', b: 'ko', v: 0.37 },
    { a: 'en', b: 'zh', v: 0.28 },
    { a: 'de', b: 'ko', v: 0.26 },
    { a: 'fr', b: 'ja', v: 0.21 },
    { a: 'en', b: 'ja', v: 0.19 },
    { a: 'en', b: 'de', v: 0.11 },
    { a: 'en', b: 'fr', v: 0.09 },
    { a: 'de', b: 'fr', v: 0.07 },
  ];
  return (
    <div className="nu-dot">
      {pairs.map((p, i) => (
        <div key={i} className="nu-dot-row">
          <div className="nu-dot-pair">
            <span className="nu-mono">{p.a}</span>
            <span className="nu-mono nu-muted">⇄</span>
            <span className="nu-mono">{p.b}</span>
          </div>
          <div className="nu-dot-track">
            <div className="nu-dot-tick" style={{left: '34%'}} />
            <div
              className={'nu-dot-mark' + (p.v >= 0.34 ? ' nu-dot-mark--risk' : '')}
              style={{left: (p.v * 100) + '%'}}
            />
          </div>
          <div className="nu-mono nu-dot-v">{p.v.toFixed(2)}</div>
        </div>
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// SCREEN 4 — Divergence Matrix
// ---------------------------------------------------------------------------

const LANGS = ['en', 'ja', 'zh', 'ko', 'de', 'fr', 'es', 'pt'];
// Deterministic-feeling pseudo-random divergence matrix
const DIVERGENCE = (() => {
  const seed = {
    'en-ja': 0.19, 'en-zh': 0.28, 'en-ko': 0.41, 'en-de': 0.11, 'en-fr': 0.09, 'en-es': 0.13, 'en-pt': 0.15,
    'ja-zh': 0.24, 'ja-ko': 0.62, 'ja-de': 0.22, 'ja-fr': 0.21, 'ja-es': 0.24, 'ja-pt': 0.26,
    'zh-ko': 0.37, 'zh-de': 0.31, 'zh-fr': 0.30, 'zh-es': 0.28, 'zh-pt': 0.29,
    'ko-de': 0.26, 'ko-fr': 0.27, 'ko-es': 0.29, 'ko-pt': 0.31,
    'de-fr': 0.07, 'de-es': 0.12, 'de-pt': 0.14,
    'fr-es': 0.10, 'fr-pt': 0.12,
    'es-pt': 0.06,
  };
  const m = {};
  for (const a of LANGS) for (const b of LANGS) {
    if (a === b) { m[a+'-'+b] = 0; continue; }
    m[a+'-'+b] = seed[a+'-'+b] ?? seed[b+'-'+a] ?? 0.15;
  }
  return m;
})();

function divClass(v) {
  if (v === 0)        return 'nu-mat-cell--diag';
  if (v < 0.15)       return 'nu-mat-cell--v1';
  if (v < 0.25)       return 'nu-mat-cell--v2';
  if (v < 0.34)       return 'nu-mat-cell--v3';
  if (v < 0.50)       return 'nu-mat-cell--v4';
  return 'nu-mat-cell--v5';
}

function ScreenMatrix() {
  return (
    <AppChrome active="matrix" breadcrumb={<>Analysis / Divergence matrix · <span className="nu-mono">iphone17_launch</span></>}>
      <section className="nu-hero">
        <Kicker>Cultural divergence matrix · <span className="nu-mono">iphone17_launch</span></Kicker>
        <h1 className="nu-h1">Eight languages, one event, one fault line.</h1>
        <p className="nu-lede">
          How differently each language community frames the iPhone 17
          launch. Color encodes frame divergence — the lens-mismatch axis.
          Topical overlap is high across the board (everyone is talking
          about the same event); the signal lives in <em>how</em>.
        </p>
      </section>

      <Rule />

      <div className="nu-mat-controls">
        <div className="nu-mat-control">
          <label className="nu-label">Event</label>
          <div className="nu-select"><span className="nu-mono">iphone17_launch</span>  ▾</div>
        </div>
        <div className="nu-mat-control">
          <label className="nu-label">Color axis</label>
          <div className="nu-tabs">
            <span className="nu-tab nu-tab--on">Frame</span>
            <span className="nu-tab">Sentiment</span>
            <span className="nu-tab">Topical</span>
          </div>
        </div>
        <div className="nu-mat-control nu-mat-control--legend">
          <label className="nu-label">Scale</label>
          <div className="nu-mat-legend">
            <span className="nu-mat-legend-cell nu-mat-cell--v1" />
            <span className="nu-mat-legend-cell nu-mat-cell--v2" />
            <span className="nu-mat-legend-cell nu-mat-cell--v3" />
            <span className="nu-mat-legend-cell nu-mat-cell--v4" />
            <span className="nu-mat-legend-cell nu-mat-cell--v5" />
            <span className="nu-mat-legend-lo">0.00</span>
            <span className="nu-mat-legend-mid">0.34 risk →</span>
            <span className="nu-mat-legend-hi">0.65</span>
          </div>
        </div>
      </div>

      <Rule />

      <div className="nu-mat-wrap">
        <div className="nu-mat-grid">
          <div className="nu-mat-corner" />
          {LANGS.map(l => <div key={'col-'+l} className="nu-mat-collabel"><span className="nu-mono">{l}</span></div>)}
          {LANGS.map(a => (
            <React.Fragment key={'row-'+a}>
              <div className="nu-mat-rowlabel"><span className="nu-mono">{a}</span></div>
              {LANGS.map(b => {
                const v = DIVERGENCE[a+'-'+b];
                const highlight = (a === 'ja' && b === 'ko') || (a === 'ko' && b === 'ja');
                return (
                  <div key={a+'-'+b}
                       className={'nu-mat-cell ' + divClass(v) + (highlight ? ' nu-mat-cell--hot' : '')}>
                    <span className="nu-mat-val">{v === 0 ? '—' : v.toFixed(2)}</span>
                  </div>
                );
              })}
            </React.Fragment>
          ))}
        </div>

        <aside className="nu-mat-aside">
          <Kicker>Selected · ja ⇄ ko</Kicker>
          <div className="nu-mat-aside-score">0.62</div>
          <RiskBadge score={75} />

          <Rule inset />

          <div className="nu-mat-aside-row">
            <span className="nu-muted">Situation</span>
            <span>Lens-split</span>
          </div>
          <div className="nu-mat-aside-row">
            <span className="nu-muted">Frame divergence</span>
            <span className="nu-mono">0.62</span>
          </div>
          <div className="nu-mat-aside-row">
            <span className="nu-muted">Sentiment divergence</span>
            <span className="nu-mono">0.31</span>
          </div>
          <div className="nu-mat-aside-row">
            <span className="nu-muted">Topical overlap</span>
            <span className="nu-mono">0.94</span>
          </div>
          <div className="nu-mat-aside-row">
            <span className="nu-muted">Confidence</span>
            <span className="nu-mono">0.86</span>
          </div>

          <Rule inset />

          <p className="nu-mat-aside-note">
            Same event, opposing lenses. Japanese discourse is on
            <Pill>Craft reverence</Pill>; Korean has reframed the launch
            as <Pill tone="risk">Status loss</Pill>. Translation alone
            will not bridge this; the creative needs a frame.
          </p>

          <button className="nu-btn nu-btn--primary nu-mat-cta">Open in event explorer →</button>
        </aside>
      </div>

      <Rule />

      <section className="nu-mat-reading">
        <Kicker>Reading the matrix</Kicker>
        <div className="nu-mat-reading-grid">
          <div>
            <h3 className="nu-h3">Aligned</h3>
            <p>Same lens, same mood. Below 0.15. de↔fr, es↔pt.</p>
          </div>
          <div>
            <h3 className="nu-h3">Lens-split</h3>
            <p>Same words, different frame. ja↔ko on this event.</p>
          </div>
          <div>
            <h3 className="nu-h3">Mood-split</h3>
            <p>Same frame, opposite feeling. Rare. Surfaces in policy events.</p>
          </div>
          <div>
            <h3 className="nu-h3">Same verdict, different reasons</h3>
            <p>Different framing, same sentiment. Look behind the agreement.</p>
          </div>
        </div>
      </section>
    </AppChrome>
  );
}

// ---------------------------------------------------------------------------
// SCREEN 0 — Brand strip / design system
// ---------------------------------------------------------------------------

function BrandStrip() {
  return (
    <div className="nu-brand-strip">
      <div className="nu-bs-row">
        <div className="nu-bs-mark">
          <div className="nu-bs-wordmark">Comprenda</div>
          <div className="nu-bs-tag">Cultural intelligence for the AI era.</div>
        </div>

        <div className="nu-bs-block">
          <div className="nu-bs-kicker">Palette · hex</div>
          <div className="nu-swatches">
            <Swatch hex="#F5F1E8" label="paper-bg" />
            <Swatch hex="#FAF7EF" label="paper-card" />
            <Swatch hex="#ECE6D7" label="paper-deep" />
            <Swatch hex="#1C1A17" label="ink" />
            <Swatch hex="#6E665B" label="ink-muted" />
            <Swatch hex="#D8D1BE" label="rule" />
            <Swatch hex="#8B2A1F" label="risk" />
            <Swatch hex="#B5781E" label="warn" />
            <Swatch hex="#2F6B4A" label="safe" />
          </div>
          <div className="nu-bs-theme">
            <div className="nu-bs-kicker">SiS theme.toml mapping</div>
            <pre className="nu-bs-pre">{`[theme]
primaryColor          = "#8B2A1F"  # oxblood
backgroundColor       = "#F5F1E8"  # paper-bg
secondaryBackgroundColor = "#ECE6D7"  # paper-deep
textColor             = "#1C1A17"  # ink
font                  = "serif"`}</pre>
          </div>
        </div>

        <div className="nu-bs-block">
          <div className="nu-bs-kicker">Type · system stacks only (SiS-safe)</div>
          <div className="nu-bs-types">
            <div className="nu-bs-type" style={{fontFamily: 'var(--serif)', fontSize: 28, lineHeight: 1, fontStyle: 'italic'}}>
              Iowan / Palatino <span className="nu-mono nu-muted">· editorial display · h1, h2, lede, numerals</span>
            </div>
            <div className="nu-bs-type" style={{fontFamily: 'var(--serif)', fontSize: 17}}>
              Iowan / Palatino · roman <span className="nu-mono nu-muted">· narrative body, briefs</span>
            </div>
            <div className="nu-bs-type" style={{fontFamily: 'var(--sans)', fontSize: 14}}>
              System sans · -apple-system <span className="nu-mono nu-muted">· UI: labels, buttons, nav, kickers</span>
            </div>
            <div className="nu-bs-type" style={{fontFamily: 'var(--mono)', fontSize: 12}}>
              ui-monospace · SF Mono <span className="nu-muted">· tabular data, codes, timestamps</span>
            </div>
          </div>
        </div>

        <div className="nu-bs-block">
          <div className="nu-bs-kicker">Voice</div>
          <ul className="nu-bs-voice">
            <li><strong>Lede first.</strong> Open every screen with one sentence of insight, not a section title.</li>
            <li><strong>Never just a number.</strong> Every metric carries a frame: trend, peer, or analog.</li>
            <li><strong>Name the move.</strong> Every screen ends in a recommended next action.</li>
            <li><strong>Cite the corpus.</strong> Quote post counts and timestamps; show your work.</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

function Swatch({ hex, label }) {
  return (
    <div className="nu-swatch">
      <div className="nu-swatch-chip" style={{ background: hex }} />
      <div className="nu-swatch-meta">
        <div className="nu-mono">{label}</div>
        <div className="nu-mono nu-muted">{hex}</div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// NavStudy — side-by-side comparison of four sidebar treatments
// ---------------------------------------------------------------------------

const NAV_SAMPLE = [
  { label: 'Overview',           kicker: 'Workbench' },
  { label: 'Pre-launch risk',    kicker: null },
  { label: 'Cultural translator',kicker: null },
  { label: 'Event explorer',     kicker: null },
  { label: 'Divergence matrix',  kicker: 'Analysis' },
  { label: 'Frame distribution', kicker: null },
  { label: 'Drift alerts',       kicker: null },
  { label: 'Analog retrieval',   kicker: null },
  { label: 'AI brief',           kicker: 'Synthesis' },
  { label: 'Narrative search',   kicker: null },
];

const ROMAN = ['i','ii','iii','iv','v','vi','vii','viii','ix','x'];

const NAV_GLYPHS = ['◉','◐','◑','◇','▦','▥','◔','◊','▤','◯'];

// Minimal SVG icon set, hand-drawn at 16px. One per page.
const ICON = {
  overview:   <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><rect x="2" y="2" width="5" height="5"/><rect x="9" y="2" width="5" height="5"/><rect x="2" y="9" width="5" height="5"/><rect x="9" y="9" width="5" height="5"/></svg>,
  plcs:       <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M2 12 L8 4 L14 12 Z"/><circle cx="8" cy="9.5" r="1" fill="currentColor"/></svg>,
  translator: <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M2 8 H14 M2 8 L6 4 M2 8 L6 12"/><path d="M14 8 L10 4 M14 8 L10 12"/></svg>,
  event:      <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><circle cx="8" cy="8" r="6"/><circle cx="8" cy="8" r="2" fill="currentColor"/></svg>,
  matrix:     <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><rect x="2" y="2" width="12" height="12"/><path d="M6 2 V14 M10 2 V14 M2 6 H14 M2 10 H14"/></svg>,
  frames:     <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><rect x="2" y="5" width="3" height="6"/><rect x="6.5" y="3" width="3" height="10"/><rect x="11" y="7" width="3" height="4"/></svg>,
  drift:      <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><path d="M2 11 Q5 5 8 8 T14 5"/></svg>,
  analog:     <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><circle cx="5" cy="8" r="3"/><circle cx="11" cy="8" r="3"/></svg>,
  brief:      <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><rect x="3" y="2" width="10" height="12"/><path d="M5 5 H11 M5 8 H11 M5 11 H9"/></svg>,
  search:     <svg viewBox="0 0 16 16" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="1.4"><circle cx="7" cy="7" r="4"/><path d="M10 10 L14 14"/></svg>,
};
const ICON_KEYS = ['overview','plcs','translator','event','matrix','frames','drift','analog','brief','search'];

function NavVariant({ tag, title, note, variant, active = 1 }) {
  return (
    <div className="nu-nv-col">
      <div className="nu-nv-tag">{tag}</div>
      <div className="nu-nv-title">{title}</div>
      <div className="nu-nv-frame">
        <div className="nu-nv-brand">
          <div className="nu-wordmark" style={{fontSize: 28}}>Comprenda</div>
          <div className="nu-tagline">Don't translate. Understand.</div>
        </div>

        {NAV_SAMPLE.map((n, i) => {
          const isActive = i === active;
          const sectionStart = n.kicker;
          return (
            <React.Fragment key={i}>
              {sectionStart && <div className="nu-nv-kicker">{sectionStart}</div>}
              <div className={'nu-nv-item' + (isActive ? ' is-active' : '') + ' nu-nv-item--' + variant}>
                {variant === 'glyph-sans' && (
                  <span className="nu-nv-marker nu-nv-marker--glyph">{NAV_GLYPHS[i]}</span>
                )}
                {variant === 'plain-sans' && (
                  <span className="nu-nv-marker nu-nv-marker--tick">{isActive ? '·' : ''}</span>
                )}
                {variant === 'plain-serif' && (
                  <span className="nu-nv-marker nu-nv-marker--tick">{isActive ? '·' : ''}</span>
                )}
                {variant === 'numbered-serif' && (
                  <span className="nu-nv-marker nu-nv-marker--num">{ROMAN[i]}.</span>
                )}
                {variant === 'svg-serif' && (
                  <span className="nu-nv-marker nu-nv-marker--svg">{ICON[ICON_KEYS[i]]}</span>
                )}
                <span className="nu-nv-label">{n.label}</span>
              </div>
            </React.Fragment>
          );
        })}
      </div>
      <div className="nu-nv-note">{note}</div>
    </div>
  );
}

function NavStudy() {
  return (
    <div className="nu-nv">
      <div className="nu-nv-head">
        <div className="nu-bs-kicker">Sidebar treatments · five directions</div>
        <div className="nu-ws-q">
          The current direction is A — sans labels with Unicode glyph
          sigils. Below, four alternatives. The question is whether the
          nav should feel like a software product or a publication.
        </div>
      </div>

      <div className="nu-nv-row">
        <NavVariant
          tag="A · CURRENT"
          title="Sans + Unicode glyphs"
          variant="glyph-sans"
          note="The current direction. Glyphs as decorative sigils — abstract, not mnemonic. Not common practice. Risk: feels arbitrary."
        />
        <NavVariant
          tag="B"
          title="Sans, no markers"
          variant="plain-sans"
          note="Strip the glyphs. Active item gets a centered dot. Cleanest, most utilitarian. Linear, Vercel, Notion."
        />
        <NavVariant
          tag="C"
          title="Serif, no markers"
          variant="plain-serif"
          note="Switch nav labels to the same serif as the headlines. The most editorial move — reads like a journal's table of contents."
        />
        <NavVariant
          tag="D"
          title="Serif + roman numerals"
          variant="numbered-serif"
          note="A journal TOC: lowercase roman numerals prefix each item. Frames the app as chapters in a publication."
        />
        <NavVariant
          tag="E"
          title="Serif + SVG icons"
          variant="svg-serif"
          note="Hand-drawn 14px line icons. Mnemonic and functional. Most professional, most implementation work."
        />
      </div>

      <div className="nu-nv-foot">
        <div className="nu-bs-kicker">My recommendation</div>
        <p className="nu-ws-rec-prose">
          <strong>C or D.</strong> Serif labels are the strongest typographic
          choice we can make within system fonts, and dropping the glyphs is a
          gain — the abstract sigils weren't pulling their weight. Between the
          two: C if you want the absolute minimum chrome; D if you want the nav
          to actively signal "this is a publication, not a SaaS app." D pairs
          especially well with the AI Brief screen, which already uses § 1–5
          section numerals — there's a system in play.
        </p>
        <p className="nu-ws-rec-prose" style={{marginTop: 12}}>
          E is excellent and the most "professional" looking, but the
          maintenance cost is real: every new page in the app needs a
          hand-drawn icon. Worth it if the icon set is a brand asset; not
          worth it if the nav rarely changes and won't appear on marketing.
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// NavGlyphStudy — if glyphs stay, which glyphs? All three columns are serif.
// ---------------------------------------------------------------------------

const GLYPH_SETS = {
  current:  ['◉','◐','◑','◇','▦','▥','◔','◊','▤','◯'],
  hybrid:   ['◉','◐','⇄','◇','▦','▥','◔','◊','▤','∃'],
  math:     ['∑','△','⇄','◇','⊠','∥','∼','≈','§','∃'],
  editorial:['¶','†','‡','※','⊞','∥','⁓','≈','§','⁂'],
};

const GLYPH_NOTES = {
  current: [
    'filled disc', 'half disc', 'half disc', 'lozenge', 'hatched square',
    'parallel hatch', 'quarter disc', 'thin lozenge', 'horizontal hatch', 'open circle',
  ],
  hybrid: [
    'filled disc',
    'half disc',
    'bidirectional exchange · semantic swap',
    'lozenge',
    'hatched square',
    'parallel hatch',
    'quarter disc',
    'thin lozenge',
    'horizontal hatch',
    'there exists · semantic swap',
  ],
  math: [
    'sum · aggregate',
    'delta · change at risk',
    'bidirectional exchange',
    'open lozenge · facet to explore',
    'boxed cross · divergence within a matrix',
    'parallel bars · distribution',
    'tilde · wave, drift',
    'approximately equal · analog',
    'section · document',
    'there exists · search',
  ],
  editorial: [
    'pilcrow · paragraph / opening',
    'dagger · attention, footnote',
    'double dagger · intersection, transfer',
    'reference mark · "see also"',
    'boxed plus · matrix',
    'parallel bars · distribution',
    'swung dash · drift, motion',
    'approximately equal · analog',
    'section · document',
    'asterism · literary search',
  ],
};

function NavGlyphCol({ tag, title, setKey, recommended, highlight }) {
  const glyphs = GLYPH_SETS[setKey];
  const notes = GLYPH_NOTES[setKey];
  const accentStyle =
    recommended ? {color: 'var(--risk)'} :
    highlight   ? {color: 'var(--signal)'} : {};
  return (
    <div className="nu-nv-col">
      <div className="nu-nv-tag" style={accentStyle}>
        {tag}{recommended && ' · suggested'}{highlight && ' · hybrid'}
      </div>
      <div className="nu-nv-title">{title}</div>

      <div className="nu-nv-frame">
        <div className="nu-brand" style={{marginBottom: 16, padding: '0 8px 12px'}}>
          <div className="nu-wordmark" style={{fontSize: 28}}>Comprenda</div>
          <div className="nu-tagline">Don't translate. Understand.</div>
        </div>

        {NAV_SAMPLE.map((n, i) => (
          <React.Fragment key={i}>
            {n.kicker && <div className="nu-nv-kicker">{n.kicker}</div>}
            <div className={'nu-nv-item nu-nv-item--plain-serif' + (i === 1 ? ' is-active' : '')}>
              <span className="nu-nv-marker nu-nv-marker--gly-serif">{glyphs[i]}</span>
              <span className="nu-nv-label">{n.label}</span>
            </div>
          </React.Fragment>
        ))}
      </div>

      <div className="nu-nv-legend">
        <div className="nu-nv-legend-kicker">Glyph map</div>
        <div className="nu-nv-legend-grid">
          {NAV_SAMPLE.map((n, i) => (
            <div className="nu-nv-legend-row" key={i}>
              <span className="nu-nv-legend-g">{glyphs[i]}</span>
              <span className="nu-nv-legend-l">{n.label}</span>
              <span className="nu-nv-legend-n">{notes[i]}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function NavGlyphStudy() {
  return (
    <div className="nu-nv">
      <div className="nu-nv-head">
        <div className="nu-bs-kicker">Sidebar glyphs · three serif treatments</div>
        <div className="nu-ws-q">
          If glyphs stay, the question is whether each one is doing semantic
          work. All three columns below pair the labels with the serif. The
          difference is which glyph set sits next to them — and whether it
          earns its place.
        </div>
      </div>

      <div className="nu-nv-row nu-nv-row--4">
        <NavGlyphCol tag="A′"  title="Current geometric set, in serif" setKey="current" />
        <NavGlyphCol tag="A″"  title="Geometric + two semantic swaps"  setKey="hybrid"  highlight />
        <NavGlyphCol tag="F"   title="Mathematical operators"          setKey="math" />
        <NavGlyphCol tag="G"   title="Editorial / printer's marks"     setKey="editorial" recommended />
      </div>

      <div className="nu-nv-foot">
        <div className="nu-bs-kicker">Read it</div>
        <p className="nu-ws-rec-prose">
          <strong>A′</strong> is the current decoration translated to serif. The
          glyphs look more elegant but they still don't <em>mean</em> anything —
          they're shapes, not signs. Honest read: cosmetically better,
          conceptually unchanged.
        </p>
        <p className="nu-ws-rec-prose" style={{marginTop: 12}}>
          <strong>A″</strong> is A′ with two surgical swaps: <em>⇄</em> for
          Cultural Translator and <em>∃</em> for Narrative Search. The eight
          decorative shapes stay, but the two items where a math operator <em>is</em>
          a better fit get the upgrade. Pragmatic middle path. Risk: mixing
          decorative and semantic glyphs creates a subtle visual inconsistency —
          the eye notices ⇄ and ∃ work differently from the rest, even if it
          can't name why.
        </p>
        <p className="nu-ws-rec-prose" style={{marginTop: 12}}>
          <strong>F</strong> is the most legible. Every glyph is a mathematical
          operator whose conventional meaning maps to what the page does:
          <em> ∑</em> for the aggregate overview, <em>△</em> for delta-of-risk,
          <em>⇄</em> for bidirectional translation, <em>≈</em> for analog
          retrieval, <em>∃</em> for search ("there exists"). A buyer in a
          finance-adjacent enterprise will read these instantly. Risk: the
          register is technical and tilts the app toward Bloomberg/quant rather
          than editorial intelligence.
        </p>
        <p className="nu-ws-rec-prose" style={{marginTop: 12}}>
          <strong>G</strong> is the on-brand answer. Printer's marks —
          <em> ¶</em>, <em>†</em>, <em>‡</em>, <em>※</em>, <em>§</em>,
          <em> ⁂</em> — are the symbols of the editorial tradition. They feel
          drawn from the same world as the serif headlines and the
          intelligence-report aesthetic. The dagger marking "pre-launch risk" is
          the literal footnote-of-caution; the section sign on "AI brief" is
          the literal document marker.
        </p>
        <p className="nu-ws-rec-prose" style={{marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--rule)'}}>
          <strong>My pick: G.</strong> It's the only one where the glyphs do the
          same conceptual work as the typography. If the editorial frame is the
          brand, the glyphs should come from the editorial vocabulary.
        </p>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// EMPTY STATES — first-run, trial-driven conversion screens
// ---------------------------------------------------------------------------

function ScreenOverviewEmpty() {
  return (
    <AppChrome active="home" breadcrumb="Overview · trial · day 1">
      <section className="nu-hero">
        <Kicker>Welcome · trial account</Kicker>
        <h1 className="nu-h1">Three reads before lunch.</h1>
        <p className="nu-lede">
          Comprenda scores how a draft will land in markets you don't speak —
          before you ship it. The fastest path is a thirty-second test
          drive on a draft of your own. Pick a starting point below.
        </p>
      </section>

      <Rule />

      <div className="nu-empty">
        <div className="nu-empty-l">
          <div className="nu-empty-icon">C</div>
          <Kicker>How most teams start</Kicker>
          <h2 className="nu-h2">A three-step trial.</h2>
          <div className="nu-empty-steps">
            <div className="nu-empty-step">
              <div className="nu-empty-step-n">01</div>
              <div>
                <div className="nu-empty-step-h">Score one draft.</div>
                <div className="nu-empty-step-p">
                  Paste any tagline, headline, product name, or campaign
                  line into Pre-Launch Risk. Pick two or three markets.
                  You'll have a defensible read in about forty seconds.
                </div>
              </div>
            </div>
            <div className="nu-empty-step">
              <div className="nu-empty-step-n">02</div>
              <div>
                <div className="nu-empty-step-h">Generate a brief.</div>
                <div className="nu-empty-step-p">
                  Pick a recent event tag — a launch, a campaign, a news
                  moment — and ask for a two-page cultural brief. It
                  comes back source-cited and ready to forward.
                </div>
              </div>
            </div>
            <div className="nu-empty-step">
              <div className="nu-empty-step-n">03</div>
              <div>
                <div className="nu-empty-step-h">Subscribe one brand.</div>
                <div className="nu-empty-step-p">
                  Drift Alerts watches a brand or product across language
                  communities and tells you when the conversation
                  diverges. Set one up; the rest happens in the
                  background.
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="nu-empty-r">
          <div className="nu-empty-try">Try with a sample draft</div>
          <div className="nu-empty-quote">
            "Live Free, Drive Fast — the new electric sports car that puts you first."
          </div>
          <div className="nu-empty-explain">
            A real automotive launch line we've scored before. The result
            is striking — and worth seeing before you paste your own.
          </div>
          <button className="nu-btn nu-btn--primary">Score this draft →</button>
          <Rule inset />
          <Kicker>Or start clean</Kicker>
          <button className="nu-btn">Open Pre-Launch Risk</button>
          <button className="nu-btn">Open AI Brief</button>
        </div>
      </div>

      <Rule />

      <section>
        <Kicker>What you'll get</Kicker>
        <div className="nu-onward-grid">
          <div className="nu-onward-card">
            <div className="nu-onward-num">i.</div>
            <div className="nu-onward-title">A score, not a vibe.</div>
            <div className="nu-onward-body">
              Every result is a number, a band, a confidence interval,
              and three historical analogs you can name in a meeting.
            </div>
          </div>
          <div className="nu-onward-card">
            <div className="nu-onward-num">ii.</div>
            <div className="nu-onward-title">Frames, not translations.</div>
            <div className="nu-onward-body">
              The signal is <em>how</em> markets are reading the same
              event differently — not whether the words translated.
            </div>
          </div>
          <div className="nu-onward-card">
            <div className="nu-onward-num">iii.</div>
            <div className="nu-onward-title">A page you can forward.</div>
            <div className="nu-onward-body">
              Every brief is exportable, source-cited, and written like
              an intelligence report — not a dashboard screenshot.
            </div>
          </div>
        </div>
      </section>
    </AppChrome>
  );
}

function ScreenPLCSEmpty() {
  return (
    <AppChrome active="plcs" breadcrumb="Workbench / Pre-launch risk · new session">
      <section className="nu-hero">
        <Kicker>Pre-launch cultural risk</Kicker>
        <h1 className="nu-h1">Score a draft.</h1>
        <p className="nu-lede">
          One number per market, on a scale of 0–100. Each number is
          backed by a confidence interval, three historical analogs from
          your corpus, and a one-sentence read. Nothing is invented;
          everything is sourced.
        </p>
      </section>

      <Rule />

      <div className="nu-plcs-input">
        <div className="nu-plcs-input-l">
          <label className="nu-label">Draft</label>
          <div className="nu-field nu-field--draft" style={{justifyContent: 'flex-start'}}>
            <div className="nu-draft-text nu-muted" style={{fontStyle: 'italic'}}>
              Paste a tagline, headline, product name, or campaign line. Up to 2,000 characters.
            </div>
            <div className="nu-draft-meta">
              <span className="nu-mono nu-muted">0 / 2,000 · ⌘↩ to score</span>
              <span className="nu-link">Try a sample →</span>
            </div>
          </div>
        </div>
        <div className="nu-plcs-input-r">
          <label className="nu-label">Target markets</label>
          <div className="nu-chips">
            <span className="nu-chip">+ pick markets</span>
          </div>
          <div className="nu-empty-explain" style={{marginTop: 8}}>
            Two to four works best. Pick the markets you'd brief a CMO on.
          </div>
          <label className="nu-label nu-label--space">Source</label>
          <div className="nu-select">en · English  ▾</div>
        </div>
      </div>

      <Rule />

      <section className="nu-empty">
        <div className="nu-empty-l">
          <Kicker>What you'll see, in plain English</Kicker>
          <h2 className="nu-h2">A score, a band, a story, a next move.</h2>
          <div className="nu-empty-steps">
            <div className="nu-empty-step">
              <div className="nu-empty-step-n">a.</div>
              <div>
                <div className="nu-empty-step-h">A number, banded.</div>
                <div className="nu-empty-step-p">
                  0–35 ship · 35–55 watch · 55–75 adapt · 75–100 do not ship.
                  Bands derived from outcomes of 1,200+ historical launches in your corpus.
                </div>
              </div>
            </div>
            <div className="nu-empty-step">
              <div className="nu-empty-step-n">b.</div>
              <div>
                <div className="nu-empty-step-h">A confidence interval.</div>
                <div className="nu-empty-step-p">
                  How sure the model is, given the corpus density for that
                  market. Shown by default; the calculation expands on click.
                </div>
              </div>
            </div>
            <div className="nu-empty-step">
              <div className="nu-empty-step-n">c.</div>
              <div>
                <div className="nu-empty-step-h">Three nameable analogs.</div>
                <div className="nu-empty-step-p">
                  Historical lines that scored similarly, with what
                  happened next. The defensibility your stakeholders need.
                </div>
              </div>
            </div>
            <div className="nu-empty-step">
              <div className="nu-empty-step-n">d.</div>
              <div>
                <div className="nu-empty-step-h">A recommended next move.</div>
                <div className="nu-empty-step-p">
                  Ship, adapt, or do not ship. If adapt: a one-click handoff
                  to Cultural Translator with the draft and target frame
                  pre-filled.
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="nu-empty-r">
          <div className="nu-empty-try">A draft worth seeing</div>
          <div className="nu-empty-quote">
            "Live Free, Drive Fast — the new electric sports car that puts you first."
          </div>
          <div className="nu-empty-explain">
            Real automotive launch line, scored against ja, ko, de, fr.
            Spoiler: one market is a 74. Worth seeing why.
          </div>
          <button className="nu-btn nu-btn--primary">Use this sample →</button>
        </div>
      </section>
    </AppChrome>
  );
}

function ScreenMatrixEmpty() {
  return (
    <AppChrome active="matrix" breadcrumb="Analysis / Divergence matrix · pick event">
      <section className="nu-hero">
        <Kicker>Cultural divergence matrix</Kicker>
        <h1 className="nu-h1">Pick an event. Read the room.</h1>
        <p className="nu-lede">
          The matrix shows how differently each language community frames
          the same event. Color encodes frame divergence — the
          lens-mismatch axis. Pick an event tag below, or start with one
          we've prepared.
        </p>
      </section>

      <Rule />

      <div className="nu-mat-controls">
        <div className="nu-mat-control">
          <label className="nu-label">Event</label>
          <div className="nu-select">— pick an event tag —  ▾</div>
        </div>
        <div className="nu-mat-control">
          <label className="nu-label">Color axis</label>
          <div className="nu-tabs">
            <span className="nu-tab nu-tab--on">Frame</span>
            <span className="nu-tab">Sentiment</span>
            <span className="nu-tab">Topical</span>
          </div>
        </div>
      </div>

      <Rule />

      <div className="nu-empty">
        <div className="nu-empty-l">
          <Kicker>Three events worth opening first</Kicker>
          <h2 className="nu-h2">Pre-loaded into your trial corpus.</h2>
          <div className="nu-empty-steps">
            <div className="nu-empty-step">
              <div className="nu-empty-step-n">·</div>
              <div>
                <div className="nu-empty-step-h">iphone17_launch <span className="nu-mono nu-muted" style={{fontWeight:400}}>· 12.4k posts · 5 langs</span></div>
                <div className="nu-empty-step-p">The clean fault-line case. ja↔ko at 0.62; everything else is in tolerance.</div>
              </div>
            </div>
            <div className="nu-empty-step">
              <div className="nu-empty-step-n">·</div>
              <div>
                <div className="nu-empty-step-h">olympics26_opening <span className="nu-mono nu-muted" style={{fontWeight:400}}>· 38.1k posts · 8 langs</span></div>
                <div className="nu-empty-step-p">High-divergence on en↔zh; geopolitical frame vs. national-pride.</div>
              </div>
            </div>
            <div className="nu-empty-step">
              <div className="nu-empty-step-n">·</div>
              <div>
                <div className="nu-empty-step-h">ev_tax_credit_2026 <span className="nu-mono nu-muted" style={{fontWeight:400}}>· 4.2k posts · 4 langs</span></div>
                <div className="nu-empty-step-p">Pragmatic-vs-ideological framing across de, fr, en, es.</div>
              </div>
            </div>
          </div>
        </div>

        <div className="nu-empty-r">
          <div className="nu-empty-try">How to read it, in two sentences</div>
          <div className="nu-empty-quote">
            "Light cells agree. Dark red disagrees. The diagonal is always blank — a language agrees with itself."
          </div>
          <div className="nu-empty-explain">
            Above 0.34 = cultural risk. The matrix highlights any pair
            past that threshold. Selecting a cell opens the language pair
            in Event Explorer for the story behind the number.
          </div>
          <button className="nu-btn nu-btn--primary">Open <span className="nu-mono">iphone17_launch</span> →</button>
        </div>
      </div>
    </AppChrome>
  );
}

// ---------------------------------------------------------------------------
// SCREEN — Cultural Translator (filled, from PLCS handoff)
// ---------------------------------------------------------------------------

const TRANSLATOR_VARIANTS = [
  {
    n: 1,
    frame: 'Collectivist',
    text: 'Together, we go further. The electric sports car built for the roads we share.',
    rationale: 'Shifts from individual self-promotion ("puts you first") to shared journey. "We" replaces "you"; achievement is collective, not competitive — the register Japanese automotive advertising rewards.',
    risk: 28,
    conf: 0.81,
    band: 'safe',
  },
  {
    n: 2,
    frame: 'Craft reverence',
    text: 'Precision in motion. An electric sports car, made with the care it deserves.',
    rationale: 'Positions the vehicle as a crafted object worthy of respect. Removes speed and freedom framing; foregrounds the monozukuri (making-things) value set that codes as premium in Japan.',
    risk: 22,
    conf: 0.84,
    band: 'safe',
  },
  {
    n: 3,
    frame: 'Pragmatic',
    text: 'Quiet power, real range. The electric sports car that delivers where it matters.',
    rationale: 'Focuses on tangible, verifiable performance claims. Avoids identity or emotional appeals; positions the buyer as discerning rather than aspirational — a safer register in the current status-loss discourse.',
    risk: 31,
    conf: 0.78,
    band: 'safe',
  },
];

function TranslatorVariantCard({ v }) {
  return (
    <div className={`nu-tv-card nu-tv-card--${v.band}`}>
      <div className="nu-tv-card-head">
        <span className="nu-tv-card-n">Variant {v.n}</span>
        <Pill>{v.frame}</Pill>
        <div className="nu-tv-card-score">
          <span className="nu-mono">{v.risk}</span>
          <span className="nu-tv-card-denom">/100</span>
          <RiskBadge score={v.risk} size="sm" />
        </div>
      </div>
      <blockquote className="nu-tv-card-text">"{v.text}"</blockquote>
      <div className="nu-tv-card-rationale">{v.rationale}</div>
      <div className="nu-tv-card-foot">
        <span className="nu-mono nu-muted">{(v.conf * 100).toFixed(0)}% confidence on re-scored risk</span>
        <button className="nu-btn nu-btn--sm">Copy text</button>
      </div>
    </div>
  );
}

function ScreenTranslator() {
  return (
    <AppChrome active="translator" breadcrumb="Workbench / Cultural translator">
      <section className="nu-hero">
        <Kicker>Cultural translator · adapting for Japan</Kicker>
        <h1 className="nu-h1">Same intent, different frame.</h1>
        <p className="nu-lede">
          Three culturally-adapted variants of the source draft, each
          shifting the cultural frame to match Japanese discourse. Every
          variant is re-scored for risk so you can compare before shipping.
        </p>
      </section>

      <Rule />

      <div className="nu-tv-input">
        <div className="nu-tv-input-l">
          <label className="nu-label">Source draft</label>
          <div className="nu-field nu-field--draft">
            <div className="nu-draft-text">
              Live Free, Drive Fast — the new electric sports car that puts you first.
            </div>
            <div className="nu-draft-meta">
              <span className="nu-mono nu-muted">12 words · en · via pre-launch risk</span>
            </div>
          </div>
        </div>
        <div className="nu-tv-input-r">
          <label className="nu-label">Target market</label>
          <div className="nu-select">ja · Japan  ▾</div>
          <label className="nu-label nu-label--space">Source language</label>
          <div className="nu-select">en · English  ▾</div>
          <label className="nu-label nu-label--space">Frame override</label>
          <div className="nu-select">Auto-detect  ▾</div>
          <div className="nu-field-hint">Adapts to the target market's dominant frames. Override to force a specific frame.</div>
        </div>
      </div>

      <Rule />

      <section>
        <div className="nu-section-head">
          <Kicker>Result · 3 variants · re-scored against 2.4M-post corpus</Kicker>
          <h2 className="nu-h2">Three ways this could land in Japan.</h2>
          <p className="nu-dek">
            Original scored 74/100 risk. All three variants score below 35 —
            within the ship-safe band. Each takes a different cultural frame.
          </p>
        </div>

        <div className="nu-tv-grid">
          {TRANSLATOR_VARIANTS.map(v => <TranslatorVariantCard key={v.n} v={v} />)}
        </div>
      </section>

      <Rule />

      <section className="nu-tv-compare">
        <div className="nu-section-head">
          <Kicker>Risk comparison · original vs. adapted</Kicker>
          <h2 className="nu-h2">The gap the translator closed.</h2>
        </div>
        <div className="nu-tv-compare-grid">
          <div className="nu-tv-compare-card nu-tv-compare-card--original">
            <div className="nu-tv-compare-label">Original draft</div>
            <div className="nu-tv-compare-score"><span className="nu-tv-compare-n">74</span>/100</div>
            <RiskBadge score={74} />
            <div className="nu-tv-compare-text">"Live Free, Drive Fast — the new electric sports car that puts you first."</div>
          </div>
          {TRANSLATOR_VARIANTS.map(v => (
            <div key={v.n} className="nu-tv-compare-card">
              <div className="nu-tv-compare-label">Variant {v.n} · {v.frame}</div>
              <div className="nu-tv-compare-score"><span className="nu-tv-compare-n">{v.risk}</span>/100</div>
              <RiskBadge score={v.risk} />
              <div className="nu-tv-compare-text">"{v.text}"</div>
            </div>
          ))}
        </div>
      </section>

      <Rule />

      <section className="nu-cta-band">
        <div>
          <Kicker>Next</Kicker>
          <h2 className="nu-h2 nu-cta-h">Ship variant 2 — or adapt for Korea next.</h2>
          <p className="nu-dek">
            Korea scored 61 on the original draft. Open the translator
            with the same source to generate Korean-market variants.
          </p>
        </div>
        <div className="nu-cta-actions">
          <button className="nu-btn nu-btn--primary">Adapt for Korea →</button>
          <button className="nu-btn">Export all variants as PDF</button>
          <button className="nu-btn">Share with team</button>
        </div>
      </section>

      <AboutThisRun defaultOpen items={[
        ['Session', <span className="nu-mono">trans_7kq2_b4c8</span>],
        ['Source session', <span className="nu-mono">plcs_2k4f9_a3b1</span>],
        ['Run started', '27 May 2026 · 09:16:04 PT'],
        ['Duration', '12 seconds'],
        ['Requested by', 'm.chen@acme.com'],
        ['Model', <span className="nu-mono">claude-4-sonnet</span>],
        ['Prompt version', <span className="nu-mono">translator-v1</span>],
        ['Target frame', '(auto-detect dominant)'],
        ['Variants generated', '3'],
        ['Re-scored', 'Yes — each variant scored against corpus'],
      ]} />
    </AppChrome>
  );
}

// ---------------------------------------------------------------------------
// Expose for index.html
// ---------------------------------------------------------------------------
Object.assign(window, {
  BrandStrip, NavStudy, NavGlyphStudy,
  ScreenOverview, ScreenPLCS, ScreenBrief, ScreenMatrix,
  ScreenOverviewEmpty, ScreenPLCSEmpty, ScreenMatrixEmpty,
  ScreenTranslator,
});
