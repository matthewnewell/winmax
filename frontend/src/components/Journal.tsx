import { useState } from 'react'
import { useAddPursuitEvent, useDeletePursuitEvent, usePursuitEvents } from '../api/hooks'
import type { PursuitEvent } from '../api/types'
import { getAuthor, relativeTime, setAuthor } from '../lib/journal'
import './Journal.css'

interface Group {
  key: string
  ts: string
  author: string | null
  changes: PursuitEvent[]
  note: PursuitEvent | null
}

/** Groups the flat event list back into "one save" clusters — events from a single edit share
 * created_at exactly. Simpler than The Fixer's version: everything here is pursuit-level, no
 * sub-target (why-step/action) to scope to, since P(Win)/P(Go)/bid calls already carry their
 * own required rationale and never land in this feed. */
function groupEvents(events: PursuitEvent[]): Group[] {
  const groups: Group[] = []
  const byKey = new Map<string, Group>()
  for (const e of events) {
    const key = e.created_at
    let g = byKey.get(key)
    if (!g) {
      g = { key, ts: e.created_at, author: e.author, changes: [], note: null }
      byKey.set(key, g)
      groups.push(g)
    }
    if (e.kind === 'change') g.changes.push(e)
    else g.note = e
  }
  return groups
}

export default function Journal({ pursuitId }: { pursuitId: string }) {
  const { data: events, isLoading } = usePursuitEvents(pursuitId)
  const addEvent = useAddPursuitEvent(pursuitId)
  const deleteEvent = useDeletePursuitEvent(pursuitId)

  const [text, setText] = useState('')
  const [name, setName] = useState(getAuthor())
  const author = getAuthor()

  function submit() {
    const note = text.trim()
    if (!note) return
    if (name.trim() && name.trim() !== author) setAuthor(name)
    addEvent.mutate(
      { note, author: (name.trim() || author) || undefined },
      { onSuccess: () => setText(''), onError: (err) => console.error('[journal] add note failed', err) },
    )
  }

  const groups = groupEvents(events ?? [])

  return (
    <div className="journal">
      <div className="journal__composer">
        <textarea
          className="journal__input"
          rows={2}
          placeholder="A decision, a risk, context worth remembering…"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() }
          }}
        />
        <div className="journal__composer-row">
          {!author && (
            <input className="journal__name" placeholder="your name" value={name} onChange={(e) => setName(e.target.value)} />
          )}
          {author && <span className="journal__as">as {author}</span>}
          <button className="journal__add" onClick={submit} disabled={!text.trim() || addEvent.isPending}>
            {addEvent.isPending ? 'Adding…' : 'Add note'}
          </button>
        </div>
        {addEvent.isError && (
          <p className="journal__error">Couldn't add the note: {(addEvent.error as Error)?.message ?? 'unknown error'}</p>
        )}
      </div>

      {deleteEvent.isError && (
        <p className="journal__error">Couldn't delete that entry: {(deleteEvent.error as Error)?.message ?? 'unknown error'}</p>
      )}

      {isLoading ? (
        <p className="journal__empty">Loading…</p>
      ) : groups.length === 0 ? (
        <p className="journal__empty">Nothing logged yet. Edits are recorded automatically; add a note for context.</p>
      ) : (
        <ol className="journal__feed">
          {groups.map((g) => (
            <li key={g.key} className="journal__entry">
              <div className="journal__meta">
                <span className="journal__author">{g.author || 'Someone'}</span>
                <span className="journal__time">{relativeTime(g.ts)}</span>
              </div>
              {g.changes.length > 0 && (
                <ul className="journal__changes">
                  {g.changes.map((c) => (
                    <li key={c.id}>
                      {c.field}: <span className="journal__old">{c.old_value}</span>
                      {' → '}
                      <span className="journal__new">{c.new_value}</span>
                    </li>
                  ))}
                </ul>
              )}
              {g.note && (
                <div className="journal__note">
                  <span>{g.note.note}</span>
                  <button className="journal__del" title="Delete this note" onClick={() => deleteEvent.mutate(g.note!.id)}>✕</button>
                </div>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
