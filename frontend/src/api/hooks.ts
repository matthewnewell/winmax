import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { api } from './client'
import type { BidDecisionValue, ChatMessage, ChatResponse, Gate, Metric, PursuitEvent, PursuitStatus } from './types'
import type { Pursuit } from './types'

export function usePursuits(filters?: { project?: string; status?: string }) {
  const params = new URLSearchParams()
  if (filters?.project) params.set('project', filters.project)
  if (filters?.status) params.set('status', filters.status)
  const qs = params.toString()
  return useQuery({
    queryKey: ['pursuits', filters?.project ?? null, filters?.status ?? null],
    queryFn: () => api.get<Pursuit[]>(`/pursuits${qs ? `?${qs}` : ''}`),
  })
}

export function usePursuit(pursuitId: string | undefined) {
  return useQuery({
    queryKey: ['pursuits', 'detail', pursuitId],
    queryFn: () => api.get<Pursuit>(`/pursuits/${pursuitId}`),
    enabled: !!pursuitId,
  })
}

export function useProjects() {
  return useQuery({
    queryKey: ['projects'],
    queryFn: () => api.get<string[]>('/projects'),
  })
}

export function useHealth() {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => api.get<{ status: string; ai_configured: boolean }>('/health'),
  })
}

function useInvalidatePursuit(pursuitId?: string) {
  const qc = useQueryClient()
  return () => {
    qc.invalidateQueries({ queryKey: ['pursuits'] })
    if (pursuitId) {
      qc.invalidateQueries({ queryKey: ['pursuits', 'detail', pursuitId] })
      qc.invalidateQueries({ queryKey: ['pursuits', pursuitId, 'events'] })
    }
  }
}

export function useCreatePursuit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (data: { name: string; customer?: string; project?: string; portfolio?: string; description?: string; created_by?: string }) =>
      api.post<Pursuit>('/pursuits', data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['pursuits'] })
      qc.invalidateQueries({ queryKey: ['projects'] })
    },
  })
}

export function useUpdatePursuit(pursuitId: string) {
  const invalidate = useInvalidatePursuit(pursuitId)
  return useMutation({
    mutationFn: (
      data: Partial<Pick<Pursuit, 'name' | 'customer' | 'project' | 'portfolio' | 'description'>> & {
        current_gate?: Gate
        status?: PursuitStatus
        author?: string
        journal_note?: string
      },
    ) => api.put<Pursuit>(`/pursuits/${pursuitId}`, data),
    onSuccess: invalidate,
  })
}

export function useDeletePursuit() {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (pursuitId: string) => api.del(`/pursuits/${pursuitId}`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['pursuits'] }),
  })
}

// ── Scores (P(Win) / P(Go)) ─────────────────────────────────────────────────────────────────

export function useAddScore(pursuitId: string) {
  const invalidate = useInvalidatePursuit(pursuitId)
  return useMutation({
    mutationFn: (data: { metric: Metric; score: number; gate?: Gate; note: string; author?: string }) =>
      api.post<Pursuit>(`/pursuits/${pursuitId}/scores`, data),
    onSuccess: invalidate,
  })
}

// ── Bid / No-Bid ─────────────────────────────────────────────────────────────────────────────

export function useAddBidDecision(pursuitId: string) {
  const invalidate = useInvalidatePursuit(pursuitId)
  return useMutation({
    mutationFn: (data: { decision: BidDecisionValue; gate?: Gate; note: string; author?: string }) =>
      api.post<Pursuit>(`/pursuits/${pursuitId}/bid-decisions`, data),
    onSuccess: invalidate,
  })
}

// ── Journal ──────────────────────────────────────────────────────────────────────────────────

export function usePursuitEvents(pursuitId: string | undefined) {
  return useQuery({
    queryKey: ['pursuits', pursuitId, 'events'],
    queryFn: () => api.get<PursuitEvent[]>(`/pursuits/${pursuitId}/events`),
    enabled: !!pursuitId,
  })
}

export function useAddPursuitEvent(pursuitId: string) {
  const invalidate = useInvalidatePursuit(pursuitId)
  return useMutation({
    mutationFn: (data: { note: string; author?: string }) => api.post<PursuitEvent>(`/pursuits/${pursuitId}/events`, data),
    onSuccess: invalidate,
  })
}

export function useDeletePursuitEvent(pursuitId: string) {
  const invalidate = useInvalidatePursuit(pursuitId)
  return useMutation({
    mutationFn: (eventId: string) => api.del(`/events/${eventId}`),
    onSuccess: invalidate,
  })
}

export function useChat() {
  return useMutation({
    mutationFn: (data: { messages: ChatMessage[]; pursuitId: string }) =>
      api.post<ChatResponse>('/chat', { messages: data.messages, pursuit_id: data.pursuitId }),
  })
}
