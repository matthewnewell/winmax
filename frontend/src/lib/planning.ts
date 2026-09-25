/** Display helpers for a pursuit's planning numbers: estimated value, weighted value (value x
 * P(Win)) and expected award date, written the way capture pipelines usually show them. */

/** $185M, $1.2B, $850K, $12,500. */
export function formatMoney(value: number): string {
  const abs = Math.abs(value)
  const compact = (n: number, unit: string) => `$${n >= 100 ? Math.round(n) : Number(n.toFixed(1))}${unit}`
  if (abs >= 1e9) return compact(value / 1e9, 'B')
  if (abs >= 1e6) return compact(value / 1e6, 'M')
  if (abs >= 1e4) return compact(value / 1e3, 'K')
  return `$${value.toLocaleString('en-US')}`
}

/** What someone types for a dollar amount: "185000000", "$185,000,000", "185M", "1.2b", "850k".
 * Returns whole dollars, null for blank, or NaN when it isn't a number. */
export function parseMoney(input: string): number | null {
  const s = input.trim().replace(/[$,\s]/g, '').toLowerCase()
  if (!s) return null
  const m = s.match(/^(\d+(?:\.\d+)?)([kmb]?)$/)
  if (!m) return NaN
  const scale = { '': 1, k: 1e3, m: 1e6, b: 1e9 }[m[2] as '' | 'k' | 'm' | 'b']
  return Math.round(Number(m[1]) * scale)
}

/** "Feb 2027" from "2027-02-21". Parsed as a calendar date, so no timezone shift. */
export function formatAwardDate(iso: string): string {
  const [y, m] = iso.split('-').map(Number)
  return new Date(y, m - 1, 1).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}
