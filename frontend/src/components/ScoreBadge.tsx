import type { Band, BidDecisionValue, Metric } from '../api/types'
import { METRIC_LABEL } from '../api/types'
import './ScoreBadge.css'

// Which of the four visual tones a band maps to — same red/amber/accent/green vocabulary as
// the rest of this ecosystem's status pills, applied to metrics.md's own four-band scale for
// both P(Win) and P(Go) (the band *keys* differ per metric, but there are always exactly four,
// worst to best).
const BAND_TONE: Record<Band['key'], 'critical' | 'wait' | 'accent' | 'success'> = {
  no_bid: 'critical', high_risk: 'critical',
  caution: 'wait', careful: 'wait',
  competitive: 'accent', reasonable: 'accent',
  strong: 'success', high_confidence: 'success',
}

export function ScoreBadge({ metric, score, band }: { metric: Metric; score: number; band: Band }) {
  return (
    <span className={`score-badge score-badge--${BAND_TONE[band.key]}`} title={band.guidance}>
      <span className="score-badge__metric">{METRIC_LABEL[metric]}</span>
      <span className="score-badge__score">{score}%</span>
    </span>
  )
}

export function ScoreBadgeEmpty({ metric }: { metric: Metric }) {
  return (
    <span className="score-badge score-badge--empty">
      <span className="score-badge__metric">{METRIC_LABEL[metric]}</span>
      <span className="score-badge__score">—</span>
    </span>
  )
}

export function BidBadge({ decision }: { decision: BidDecisionValue }) {
  return (
    <span className={`score-badge ${decision === 'go' ? 'score-badge--success' : 'score-badge--critical'}`}>
      <span className="score-badge__metric">Bid</span>
      <span className="score-badge__score">{decision === 'go' ? 'Go' : 'No-Go'}</span>
    </span>
  )
}
