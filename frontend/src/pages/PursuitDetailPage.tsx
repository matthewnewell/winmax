import { useState } from 'react'
import { useParams } from 'react-router-dom'
import { useAddBidDecision, useAddScore, useHealth, usePursuit, useUpdatePursuit } from '../api/hooks'
import { GATES, GATE_LABEL, PURSUIT_STATUS_LABEL } from '../api/types'
import type { Gate, Metric, PursuitStatus } from '../api/types'
import Nav from '../components/Nav'
import { BidBadge, ScoreBadge, ScoreBadgeEmpty } from '../components/ScoreBadge'
import Journal from '../components/Journal'
import ChatPanel from '../components/ChatPanel'
import { getAuthor, relativeTime } from '../lib/journal'
import './PursuitDetailPage.css'

const P_WIN_FACTORS = [
  'Customer relationship strength', 'Competitive position', 'Solution fit',
  'Past performance alignment', 'Price-to-win gap', 'Incumbent advantage',
  'Teaming posture', 'Black hat assessment', 'Discriminators',
]
const P_GO_FACTORS = [
  'Budget appropriation status', 'Requirement stability', 'Program office track record',
  'Congressional/administration priority', 'Urgency of need', 'Acquisition strategy lock',
  'Incumbent protest exposure', 'Market research signals',
]
const BID_FACTORS = [
  'Strategic fit', 'Cost to pursue', 'Expected value vs. pursuit cost', 'Resource availability',
  'Capacity impact', 'Pipeline opportunity cost', 'Margin expectations', 'Risk profile', 'Teaming dependencies',
]

export default function PursuitDetailPage() {
  const { pursuitId } = useParams<{ pursuitId: string }>()
  const { data: p, isLoading } = usePursuit(pursuitId)
  const { data: health } = useHealth()
  const updatePursuit = useUpdatePursuit(pursuitId ?? '')
  const [chatOpen, setChatOpen] = useState(false)
  const [editing, setEditing] = useState(false)
  const [factorsFor, setFactorsFor] = useState<'p_win' | 'p_go' | 'bid' | null>(null)

  if (isLoading || !p) return <div className="pursuit-detail__loading">Loading…</div>

  return (
    <div className="pursuit-layout">
      <Nav />
      <div className="pursuit-layout__row">
        <div className="pursuit-detail">
          <div className="pursuit-detail__inner">
            <header className="pursuit-detail__header">
              {p.portfolio && <span className="pursuit-detail__badge">{p.portfolio}</span>}
              <div className="pursuit-detail__title-row">
                <div className="pursuit-detail__title-block">
                  <h1 className="pursuit-detail__title">{p.name}</h1>
                  {p.customer && <div className="pursuit-detail__customer">{p.customer}</div>}
                </div>
                <div className="pursuit-detail__title-actions">
                  <select
                    value={p.current_gate}
                    onChange={(e) => updatePursuit.mutate({ current_gate: e.target.value as Gate, author: getAuthor() })}
                  >
                    {GATES.map((g) => <option key={g} value={g}>{GATE_LABEL[g]}</option>)}
                  </select>
                  <select
                    className={`status-select status-select--${p.status}`}
                    value={p.status}
                    onChange={(e) => updatePursuit.mutate({ status: e.target.value as PursuitStatus, author: getAuthor() })}
                  >
                    {(Object.keys(PURSUIT_STATUS_LABEL) as PursuitStatus[]).map((s) => (
                      <option key={s} value={s}>{PURSUIT_STATUS_LABEL[s]}</option>
                    ))}
                  </select>
                  <button className="wm-btn wm-btn--ghost" onClick={() => setEditing((v) => !v)}>
                    {editing ? 'Done editing' : '✎ Edit'}
                  </button>
                </div>
              </div>
              {editing ? (
                <PursuitEditForm pursuitId={p.id} name={p.name} customer={p.customer} description={p.description} onDone={() => setEditing(false)} />
              ) : (
                p.description && <p className="pursuit-detail__desc">{p.description}</p>
              )}
            </header>

            <section className="pursuit-detail__section">
              <div className="assessment-grid">
                <ScoreColumn pursuitId={p.id} metric="p_win" current={p.p_win} history={p.score_history} gate={p.current_gate}
                  factors={P_WIN_FACTORS} showFactors={factorsFor === 'p_win'} onToggleFactors={() => setFactorsFor(factorsFor === 'p_win' ? null : 'p_win')} />
                <ScoreColumn pursuitId={p.id} metric="p_go" current={p.p_go} history={p.score_history} gate={p.current_gate}
                  factors={P_GO_FACTORS} showFactors={factorsFor === 'p_go'} onToggleFactors={() => setFactorsFor(factorsFor === 'p_go' ? null : 'p_go')} />
                <BidColumn pursuitId={p.id} current={p.bid_decision} history={p.bid_history} gate={p.current_gate}
                  factors={BID_FACTORS} showFactors={factorsFor === 'bid'} onToggleFactors={() => setFactorsFor(factorsFor === 'bid' ? null : 'bid')} />
              </div>
              <p className="pursuit-detail__gating-note">
                P(Go) gates first — if the government won't follow through, nothing else matters. P(Win) gates second. Bid/No-Bid gates third: walk away even from a probable win if the economics don't work.
              </p>
            </section>

            <section className="pursuit-detail__section" aria-label="Journal">
              <h2 className="pursuit-detail__section-title">Journal</h2>
              <Journal pursuitId={p.id} />
            </section>
          </div>
        </div>

        {chatOpen ? (
          <ChatPanel pursuitId={p.id} aiConfigured={health?.ai_configured ?? false} onCollapse={() => setChatOpen(false)} />
        ) : (
          <button className="pursuit-layout__chat-tab" onClick={() => setChatOpen(true)} title="Open chat">✨ Chat</button>
        )}
      </div>
    </div>
  )
}

function ScoreColumn({
  pursuitId, metric, current, history, gate, factors, showFactors, onToggleFactors,
}: {
  pursuitId: string
  metric: Metric
  current: import('../api/types').ScoreEntry | null
  history?: import('../api/types').ScoreEntry[]
  gate: Gate
  factors: string[]
  showFactors: boolean
  onToggleFactors: () => void
}) {
  const addScore = useAddScore(pursuitId)
  const [adding, setAdding] = useState(false)
  const [score, setScore] = useState('50')
  const [note, setNote] = useState('')
  const entries = (history ?? []).filter((e) => e.metric === metric)

  function submit() {
    const n = parseInt(score, 10)
    if (!(n >= 0 && n <= 100) || !note.trim()) return
    addScore.mutate(
      { metric, score: n, gate, note: note.trim(), author: getAuthor() },
      { onSuccess: () => { setAdding(false); setNote('') } },
    )
  }

  return (
    <div className="assessment-col">
      <div className="assessment-col__head">
        {current ? <ScoreBadge metric={metric} score={current.score} band={current.band} /> : <ScoreBadgeEmpty metric={metric} />}
        <button className="assessment-col__factors-btn" onClick={onToggleFactors} title="What to weigh">?</button>
      </div>
      {current && <p className="assessment-col__guidance">{current.band.guidance}</p>}

      {showFactors && (
        <ul className="assessment-col__factor-list">
          {factors.map((f) => <li key={f}>{f}</li>)}
        </ul>
      )}

      {entries.length > 0 && (
        <ul className="assessment-col__history">
          {entries.slice().reverse().map((e) => (
            <li key={e.id}>
              <div className="assessment-col__history-top">
                <span className="assessment-col__history-score">{e.score}%</span>
                <span className="assessment-col__history-gate">{GATE_LABEL[e.gate]}</span>
                <span className="assessment-col__history-time">{relativeTime(e.created_at)}</span>
              </div>
              <p className="assessment-col__history-note">{e.note}</p>
            </li>
          ))}
        </ul>
      )}

      {adding ? (
        <div className="assessment-add">
          <input type="number" min="0" max="100" value={score} onChange={(e) => setScore(e.target.value)} />
          <textarea
            rows={2}
            placeholder="What evidence supports this score?"
            value={note}
            onChange={(e) => setNote(e.target.value)}
          />
          <div className="assessment-add__actions">
            <button className="wm-btn wm-btn--primary" onClick={submit} disabled={!note.trim() || addScore.isPending}>
              {addScore.isPending ? 'Saving…' : 'Save'}
            </button>
            <button className="wm-btn wm-btn--ghost" onClick={() => setAdding(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <button className="wm-btn wm-btn--ghost assessment-col__add" onClick={() => setAdding(true)}>+ New assessment</button>
      )}
    </div>
  )
}

function BidColumn({
  pursuitId, current, history, gate, factors, showFactors, onToggleFactors,
}: {
  pursuitId: string
  current: import('../api/types').BidDecision | null
  history?: import('../api/types').BidDecision[]
  gate: Gate
  factors: string[]
  showFactors: boolean
  onToggleFactors: () => void
}) {
  const addBid = useAddBidDecision(pursuitId)
  const [adding, setAdding] = useState(false)
  const [decision, setDecision] = useState<'go' | 'no_go'>('go')
  const [note, setNote] = useState('')

  function submit() {
    if (!note.trim()) return
    addBid.mutate(
      { decision, gate, note: note.trim(), author: getAuthor() },
      { onSuccess: () => { setAdding(false); setNote('') } },
    )
  }

  return (
    <div className="assessment-col">
      <div className="assessment-col__head">
        {current ? <BidBadge decision={current.decision} /> : <span className="score-badge score-badge--empty"><span className="score-badge__metric">Bid</span><span className="score-badge__score">—</span></span>}
        <button className="assessment-col__factors-btn" onClick={onToggleFactors} title="What to weigh">?</button>
      </div>

      {showFactors && (
        <ul className="assessment-col__factor-list">
          {factors.map((f) => <li key={f}>{f}</li>)}
        </ul>
      )}

      {(history ?? []).length > 0 && (
        <ul className="assessment-col__history">
          {(history ?? []).slice().reverse().map((b) => (
            <li key={b.id}>
              <div className="assessment-col__history-top">
                <span className={`assessment-col__history-score${b.decision === 'no_go' ? ' assessment-col__history-score--no' : ''}`}>
                  {b.decision === 'go' ? 'Go' : 'No-Go'}
                </span>
                <span className="assessment-col__history-gate">{GATE_LABEL[b.gate]}</span>
                <span className="assessment-col__history-time">{relativeTime(b.created_at)}</span>
              </div>
              <p className="assessment-col__history-note">{b.note}</p>
            </li>
          ))}
        </ul>
      )}

      {adding ? (
        <div className="assessment-add">
          <select value={decision} onChange={(e) => setDecision(e.target.value as 'go' | 'no_go')}>
            <option value="go">Go</option>
            <option value="no_go">No-Go</option>
          </select>
          <textarea rows={2} placeholder="Rationale" value={note} onChange={(e) => setNote(e.target.value)} />
          <div className="assessment-add__actions">
            <button className="wm-btn wm-btn--primary" onClick={submit} disabled={!note.trim() || addBid.isPending}>
              {addBid.isPending ? 'Saving…' : 'Save'}
            </button>
            <button className="wm-btn wm-btn--ghost" onClick={() => setAdding(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <button className="wm-btn wm-btn--ghost assessment-col__add" onClick={() => setAdding(true)}>+ New call</button>
      )}
    </div>
  )
}

function PursuitEditForm({
  pursuitId, name, customer, description, onDone,
}: {
  pursuitId: string
  name: string
  customer: string | null
  description: string | null
  onDone: () => void
}) {
  const updatePursuit = useUpdatePursuit(pursuitId)
  const [form, setForm] = useState({ name, customer: customer ?? '', description: description ?? '', note: '' })

  function submit() {
    if (!form.name.trim()) return
    updatePursuit.mutate(
      {
        name: form.name.trim(),
        customer: form.customer.trim() || undefined,
        description: form.description.trim() || undefined,
        author: getAuthor(),
        journal_note: form.note.trim() || undefined,
      },
      { onSuccess: onDone },
    )
  }

  return (
    <div className="pursuit-edit-form">
      <label>
        Name
        <input value={form.name} onChange={(e) => setForm((f) => ({ ...f, name: e.target.value }))} />
      </label>
      <label>
        Customer
        <input value={form.customer} onChange={(e) => setForm((f) => ({ ...f, customer: e.target.value }))} />
      </label>
      <label>
        Description
        <textarea rows={2} value={form.description} onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))} />
      </label>
      <label>
        Journal note <span className="pursuit-edit-form__optional">(optional)</span>
        <input placeholder="Why this change?" value={form.note} onChange={(e) => setForm((f) => ({ ...f, note: e.target.value }))} />
      </label>
      <div className="pursuit-edit-form__actions">
        <button className="wm-btn wm-btn--primary" onClick={submit} disabled={!form.name.trim() || updatePursuit.isPending}>
          {updatePursuit.isPending ? 'Saving…' : 'Save'}
        </button>
        <button className="wm-btn wm-btn--ghost" onClick={onDone}>Cancel</button>
      </div>
    </div>
  )
}
