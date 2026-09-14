import { Fragment, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Nav from '../components/Nav'
import './SplashPage.css'

// Matches backend/seed.py's DEMO_PURSUIT_ID — the healthy demo pursuit, and its real current
// figures (kept in sync by hand, same convention as The Fixer's splash figure hardcoding its
// demo case's actual numbers rather than inventing illustrative ones).
const DEMO_PURSUIT_ID = 'demo-avionics-idiq'

const GATES = [
  { label: 'P(Go)', value: '78%', band: 'Reasonable confidence', tone: 'accent' as const },
  { label: 'P(Win)', value: '68%', band: 'Competitive position', tone: 'accent' as const },
  { label: 'Bid / No-Bid', value: 'Go', band: 'Capture investment authorized', tone: 'success' as const },
]

const FEATURES = [
  {
    title: 'Three judgment calls, not one score',
    body: "P(Win), P(Go), and Bid/No-Bid answer different questions — can we win it, will the government follow through, should we fund the chase — and a strong one doesn't excuse a weak other. All three re-assessed at every gate, not scored once and filed.",
  },
  {
    title: 'A note, not just a number',
    body: 'Every score and every bid call carries a required note — what evidence moved it. A 75% with no rationale is exactly the kind of unsupported number this app is built to catch.',
  },
  {
    title: 'One assistant, not six',
    body: "An early sketch of this tool split the work across six specialized agent roles. WinMax starts with one assistant that can challenge a score against its own note — the same restraint this ecosystem applies everywhere else.",
  },
]

export default function SplashPage() {
  const [infoOpen, setInfoOpen] = useState(false)

  useEffect(() => {
    if (!infoOpen) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setInfoOpen(false)
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [infoOpen])

  return (
    <div className="splash-page">
      <Nav />
      <div className="splash-page__scroll">
        <div className="splash-page__content">
          <header className="splash-hero">
            <h1 className="splash-hero__title">WinMax</h1>
            <p className="splash-hero__sub">
              A gated pursuit tracker — P(Win), P(Go), and Bid/No-Bid, each its own honest number.
              <button className="splash-info-btn" onClick={() => setInfoOpen(true)} aria-label="What do P(Win), P(Go), and Bid/No-Bid mean?">?</button>
            </p>
          </header>

          <figure className="splash-figure">
            <Link className="splash-figure__link" to={`/pursuits/${DEMO_PURSUIT_ID}`}>
              <div className="splash-layout">
                {GATES.map((g, i) => (
                  <Fragment key={g.label}>
                    <div className={`splash-gate splash-gate--${g.tone}`}>
                      <div className="splash-gate__label">{g.label}</div>
                      <div className="splash-gate__value">{g.value}</div>
                      <div className="splash-gate__band">{g.band}</div>
                    </div>
                    {i < GATES.length - 1 && (
                      <div className="splash-connector">
                        <div className="splash-connector__line" />
                        <div className="splash-connector__head">▶</div>
                      </div>
                    )}
                  </Fragment>
                ))}
              </div>
            </Link>
          </figure>

          <div className="splash-grid">
            {FEATURES.map((f) => (
              <div key={f.title} className="splash-card">
                <div className="splash-card__heading">{f.title}</div>
                <p className="splash-card__body">{f.body}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {infoOpen && (
        <div className="splash-modal-backdrop" onClick={() => setInfoOpen(false)}>
          <div className="splash-modal" onClick={(e) => e.stopPropagation()}>
            <button className="splash-modal__close" onClick={() => setInfoOpen(false)} aria-label="Close">✕</button>
            <h2 className="splash-modal__title">P(Win), P(Go) &amp; Bid/No-Bid</h2>
            <p className="splash-modal__body">
              <strong>P(Go)</strong> gates first: will the government actually follow through on this procurement, independent of whether we could win it? Continuing Resolutions, unstable requirements, and quiet cancellations kill more pursuits than competition does.
            </p>
            <p className="splash-modal__body">
              <strong>P(Win)</strong> gates second: if the procurement proceeds, can we win it? Customer relationships, competitive position, price-to-win, and provable discriminators — not hope.
            </p>
            <p className="splash-modal__body">
              <strong>Bid/No-Bid</strong> gates third: even with strong P(Win) and P(Go), should the company fund the chase right now? Strategic fit, cost to pursue, and what else the same capture staff would be doing instead.
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
