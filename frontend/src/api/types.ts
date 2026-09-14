export const GATES = ['qualification', 'capture_plan', 'pre_proposal', 'rfp_release', 'final_proposal_review'] as const
export type Gate = (typeof GATES)[number]
export const GATE_LABEL: Record<Gate, string> = {
  qualification: 'Qualification',
  capture_plan: 'Capture Plan',
  pre_proposal: 'Pre-Proposal',
  rfp_release: 'RFP Release',
  final_proposal_review: 'Final Proposal Review',
}

export type PursuitStatus = 'active' | 'no_bid' | 'lost' | 'won'
export const PURSUIT_STATUS_LABEL: Record<PursuitStatus, string> = {
  active: 'Active', no_bid: 'No-Bid', lost: 'Lost', won: 'Won',
}

export type Metric = 'p_win' | 'p_go'
export const METRIC_LABEL: Record<Metric, string> = { p_win: 'P(Win)', p_go: 'P(Go)' }

export type BandKey = 'no_bid' | 'caution' | 'competitive' | 'strong' | 'high_risk' | 'careful' | 'reasonable' | 'high_confidence'

export interface Band {
  key: BandKey
  label: string
  guidance: string
}

/** One P(Win) or P(Go) assessment — always carries the note that justifies it. `band` is
 * computed server-side from the thresholds in backend/bands.py (metrics.md's own numbers),
 * not stored, so a later threshold change re-bands history automatically. */
export interface ScoreEntry {
  id: string
  pursuit_id: string
  metric: Metric
  score: number
  band: Band
  gate: Gate
  note: string
  author: string | null
  created_at: string
}

export type BidDecisionValue = 'go' | 'no_go'

export interface BidDecision {
  id: string
  pursuit_id: string
  decision: BidDecisionValue
  gate: Gate
  note: string
  author: string | null
  created_at: string
}

export interface Pursuit {
  id: string
  name: string
  customer: string | null
  project: string | null
  portfolio: string | null
  description: string | null
  current_gate: Gate
  status: PursuitStatus
  created_by: string | null
  created_at: string
  p_win: ScoreEntry | null
  p_go: ScoreEntry | null
  bid_decision: BidDecision | null
  score_history?: ScoreEntry[]
  bid_history?: BidDecision[]
}

export type EventKind = 'note' | 'change'

export interface PursuitEvent {
  id: string
  pursuit_id: string
  created_at: string
  author: string | null
  kind: EventKind
  field: string | null
  old_value: string | null
  new_value: string | null
  note: string | null
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
}

export interface ChatResponse {
  reply: string
  error?: string
}
