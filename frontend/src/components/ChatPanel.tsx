import { useRef, useState } from 'react'
import { useChat } from '../api/hooks'
import type { ChatMessage } from '../api/types'
import './ChatPanel.css'

interface ChatPanelProps {
  pursuitId: string
  aiConfigured: boolean
  onCollapse: () => void
}

const STARTER_PROMPTS = [
  'Does the P(Win) score actually match its own note?',
  'Are we ignoring a low P(Go) while investing on P(Win) alone?',
  "What's missing before the next gate review?",
]

/** Same shape as every sibling app's chat pane — stateless backend, plain React-state history,
 * collapsible. One persistent assistant per pursuit, not the six specialized agent roles
 * (Capture Manager, Competitive Intel, Price-to-Win, Customer Intel, Proposal Strategist, Color
 * Team Reviewer) the original WinMaxxing teaser sketched. */
export default function ChatPanel({ pursuitId, aiConfigured, onCollapse }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [error, setError] = useState<string | null>(null)
  const chat = useChat()
  const listRef = useRef<HTMLDivElement>(null)

  function scrollToBottom() {
    requestAnimationFrame(() => {
      listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
    })
  }

  function send(text: string) {
    const trimmed = text.trim()
    if (!trimmed || chat.isPending) return

    const nextMessages: ChatMessage[] = [...messages, { role: 'user', content: trimmed }]
    setMessages(nextMessages)
    setInput('')
    setError(null)
    scrollToBottom()

    chat.mutate(
      { messages: nextMessages, pursuitId },
      {
        onSuccess: (result) => {
          if (result.error) {
            setError(result.error)
            return
          }
          setMessages((m) => [...m, { role: 'assistant', content: result.reply }])
          scrollToBottom()
        },
        onError: (err) => setError(err instanceof Error ? err.message : 'Something went wrong'),
      },
    )
  }

  if (!aiConfigured) {
    return (
      <aside className="chat-panel chat-panel--empty">
        <div className="chat-panel__header">
          <h3 className="chat-panel__title">✨ Ask about this pursuit</h3>
          <button className="chat-panel__collapse" onClick={onCollapse} title="Collapse chat">»</button>
        </div>
        <div className="chat-panel__not-configured">
          AI is not configured for this instance. Set <code>AI_PROVIDER</code> to{' '}
          <code>claude</code>, <code>gemini</code>, or <code>ollama</code> to get help
          challenging a score or reasoning about the bid/no-bid call. Everything else — the
          pursuit itself — works fully without it.
        </div>
      </aside>
    )
  }

  return (
    <aside className="chat-panel">
      <div className="chat-panel__header">
        <h3 className="chat-panel__title">✨ Ask about this pursuit</h3>
        <button className="chat-panel__collapse" onClick={onCollapse} title="Collapse chat">»</button>
      </div>

      <div className="chat-panel__messages" ref={listRef}>
        {messages.length === 0 && (
          <div className="chat-panel__intro">
            <p>Ask whether a score is actually backed by its note, or what's missing before the next gate.</p>
            <div className="chat-panel__starters">
              {STARTER_PROMPTS.map((p) => (
                <button key={p} className="chat-panel__starter" onClick={() => send(p)}>{p}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((m, i) => (
          <div key={i} className={`chat-panel__msg chat-panel__msg--${m.role}`}>{m.content}</div>
        ))}

        {chat.isPending && (
          <div className="chat-panel__msg chat-panel__msg--assistant chat-panel__msg--pending">thinking…</div>
        )}

        {error && <div className="chat-panel__error">{error}</div>}
      </div>

      <form className="chat-panel__input-row" onSubmit={(e) => { e.preventDefault(); send(input) }}>
        <textarea
          className="chat-panel__input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(input) }
          }}
          placeholder="Ask a question…"
          rows={2}
        />
        <button type="submit" className="chat-panel__send" disabled={!input.trim() || chat.isPending}>
          Send
        </button>
      </form>
    </aside>
  )
}
