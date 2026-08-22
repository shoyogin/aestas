/** Date helpers. Every date in the app is a local calendar day, formatted here
 *  and nowhere else — three copies of toYMD used to drift apart. */

export const CALENDAR_WIDTH = 'mx-auto w-full max-w-[400px]'

const MS_PER_DAY = 24 * 60 * 60 * 1000

/** Local calendar day as YYYY-MM-DD (never UTC — that shifts the date). */
export function toYMD(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

/** Parse YYYY-MM-DD as a local date. `new Date(str)` would parse it as UTC. */
export function parseYMD(s) {
  const [y, m, d] = String(s).split('-').map(Number)
  if (!y || !m || !d) return null
  return new Date(y, m - 1, d)
}

export function startOfDay(d) {
  const out = new Date(d)
  out.setHours(0, 0, 0, 0)
  return out
}

export function today() {
  return startOfDay(new Date())
}

export function addDays(d, n) {
  const out = new Date(d)
  out.setDate(out.getDate() + n)
  return out
}

/** Whole days between two dates, ignoring the time of day and DST shifts. */
export function diffDays(later, earlier) {
  return Math.round((startOfDay(later) - startOfDay(earlier)) / MS_PER_DAY)
}

export function startOfMonth(d) {
  return new Date(d.getFullYear(), d.getMonth(), 1)
}

export function endOfMonth(d) {
  return new Date(d.getFullYear(), d.getMonth() + 1, 0)
}

/** Sunday-start grid covering the month (padding days from adjacent months). */
export function getMonthGrid(viewDate) {
  const first = startOfMonth(viewDate)
  const last = endOfMonth(viewDate)
  const start = addDays(first, -first.getDay())
  const end = addDays(last, 6 - last.getDay())
  const days = []
  for (let d = new Date(start); d <= end; d = addDays(d, 1)) {
    days.push(new Date(d))
  }
  return days
}

/** The browser's IANA timezone, sent to the server so both agree on "today". */
export function browserTimezone() {
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC'
  } catch {
    return 'UTC'
  }
}
