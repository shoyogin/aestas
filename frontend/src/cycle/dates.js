export const CALENDAR_WIDTH = 'mx-auto w-full max-w-[400px]'

export function toYMD(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

export function addDays(d, n) {
  const out = new Date(d)
  out.setDate(out.getDate() + n)
  return out
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
