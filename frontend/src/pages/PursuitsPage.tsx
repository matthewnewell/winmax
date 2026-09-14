import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useCreatePursuit, usePursuits, useProjects } from '../api/hooks'
import { GATE_LABEL, PURSUIT_STATUS_LABEL } from '../api/types'
import type { PursuitStatus } from '../api/types'
import { BidBadge, ScoreBadge, ScoreBadgeEmpty } from '../components/ScoreBadge'
import './PursuitsPage.css'

export default function PursuitsPage() {
  const navigate = useNavigate()
  const [project, setProject] = useState('')
  const [status, setStatus] = useState('')
  const { data: projects } = useProjects()
  const { data: pursuits, isLoading } = usePursuits({ project: project || undefined, status: status || undefined })
  const createPursuit = useCreatePursuit()
  const [composing, setComposing] = useState(false)
  const [name, setName] = useState('')

  const [searchParams, setSearchParams] = useSearchParams()
  useEffect(() => {
    if (searchParams.get('new')) {
      setComposing(true)
      setSearchParams((prev) => { const next = new URLSearchParams(prev); next.delete('new'); return next }, { replace: true })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams])

  const sorted = useMemo(() => {
    if (!pursuits) return []
    // Active pursuits first (needs a look), decided ones last; newest first within each.
    return [...pursuits].sort((a, b) => {
      const aOpen = a.status === 'active', bOpen = b.status === 'active'
      if (aOpen !== bOpen) return aOpen ? -1 : 1
      return b.created_at.localeCompare(a.created_at)
    })
  }, [pursuits])

  function handleCreate() {
    if (!name.trim()) return
    createPursuit.mutate(
      { name: name.trim() },
      { onSuccess: (p) => navigate(`/pursuits/${p.id}`) },
    )
  }

  return (
    <div className="pursuits-page">
      <div className="pursuits-page__inner">
        <header className="pursuits-page__header">
          <div>
            <h1 className="pursuits-page__title">Pursuits</h1>
            <p className="pursuits-page__hint">P(Win), P(Go), and the bid/no-bid call — three separate judgment calls, tracked at every gate.</p>
          </div>
          {!composing ? (
            <button className="wm-btn wm-btn--primary" onClick={() => setComposing(true)}>+ New pursuit</button>
          ) : (
            <div className="new-pursuit-form">
              <input
                autoFocus
                placeholder="Opportunity name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
              />
              <button className="wm-btn wm-btn--primary" onClick={handleCreate} disabled={!name.trim() || createPursuit.isPending}>
                {createPursuit.isPending ? 'Creating…' : 'Create'}
              </button>
              <button className="wm-btn wm-btn--ghost" onClick={() => { setComposing(false); setName('') }}>Cancel</button>
            </div>
          )}
        </header>

        <div className="pursuits-page__filters">
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All statuses</option>
            {(Object.keys(PURSUIT_STATUS_LABEL) as PursuitStatus[]).map((s) => (
              <option key={s} value={s}>{PURSUIT_STATUS_LABEL[s]}</option>
            ))}
          </select>
          <select value={project} onChange={(e) => setProject(e.target.value)}>
            <option value="">All projects</option>
            {(projects ?? []).map((p) => <option key={p} value={p}>{p}</option>)}
          </select>
        </div>

        {isLoading && <p className="pursuits-page__empty">Loading…</p>}
        {!isLoading && sorted.length === 0 && <p className="pursuits-page__empty">No pursuits yet.</p>}

        <div className="pursuit-cards">
          {sorted.map((p) => (
            <button key={p.id} className="pursuit-card" onClick={() => navigate(`/pursuits/${p.id}`)}>
              <div className="pursuit-card__top">
                <span className={`status-pill status-pill--${p.status}`}>{PURSUIT_STATUS_LABEL[p.status]}</span>
                <span className="pursuit-card__gate">{GATE_LABEL[p.current_gate]}</span>
              </div>
              <div className="pursuit-card__name">{p.name}</div>
              {p.customer && <div className="pursuit-card__customer">{p.customer}</div>}
              <div className="pursuit-card__badges">
                {p.p_win ? <ScoreBadge metric="p_win" score={p.p_win.score} band={p.p_win.band} /> : <ScoreBadgeEmpty metric="p_win" />}
                {p.p_go ? <ScoreBadge metric="p_go" score={p.p_go.score} band={p.p_go.band} /> : <ScoreBadgeEmpty metric="p_go" />}
                {p.bid_decision && <BidBadge decision={p.bid_decision.decision} />}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
