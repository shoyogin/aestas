const FLOW_DAY_STYLE = {
  spots: { backgroundColor: '#fcb9b2', color: '#461220' },
  light: { backgroundColor: '#b23a48', color: '#fed0bb' },
  normal: { backgroundColor: '#8c2f39', color: '#fed0bb' },
  heavy: { backgroundColor: '#461220', color: '#fed0bb' },
}

const DEFAULT_DAY_STYLE = { backgroundColor: '#fed0bb', color: '#461220' }
const OUTSIDE_DAY_STYLE = { backgroundColor: '#fed0bb', color: '#461220' }

export const CALENDAR_WIDTH = 'mx-auto w-full max-w-[400px]'

const WEEKDAYS = ['S', 'M', 'T', 'W', 'T', 'F', 'S']

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

function shiftMonth(d, delta) {
  const next = new Date(d.getFullYear(), d.getMonth() + delta, 1)
  const last = endOfMonth(next).getDate()
  next.setDate(Math.min(d.getDate(), last))
  next.setHours(0, 0, 0, 0)
  return next
}

const ARROW =
  'flex-shrink-0 w-9 h-9 rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium text-base transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50'

export default function CalendarArc({
  selectedDate,
  onSelectDate,
  logs = {},
  readOnly = false,
}) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const todayYMD = toYMD(today)
  const selectedYMD = toYMD(selectedDate)
  const viewMonth = selectedDate.getMonth()
  const viewYear = selectedDate.getFullYear()
  const gridDays = getMonthGrid(selectedDate)
  const monthLabel = selectedDate.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })

  return (
    <div className={`mb-6 ${CALENDAR_WIDTH}`}>
      <div className="flex items-center justify-between gap-2 mb-2.5">
        <button
          type="button"
          onClick={() => onSelectDate(shiftMonth(selectedDate, -1))}
          className={ARROW}
          aria-label="Previous month"
        >
          ←
        </button>
        <p className="text-peach-fuzz font-semibold text-base text-center flex-1">{monthLabel}</p>
        <button
          type="button"
          onClick={() => onSelectDate(shiftMonth(selectedDate, 1))}
          className={ARROW}
          aria-label="Next month"
        >
          →
        </button>
      </div>
      <div className="grid grid-cols-7 gap-1">
        {WEEKDAYS.map((label, i) => (
          <div
            key={`${label}-${i}`}
            className="text-center text-xs font-semibold text-powder-blush/80 pb-1"
          >
            {label}
          </div>
        ))}
        {gridDays.map((day) => {
          const ymd = toYMD(day)
          const inMonth = day.getMonth() === viewMonth && day.getFullYear() === viewYear
          const isSelected = ymd === selectedYMD
          const isToday = ymd === todayYMD
          const log = logs[ymd] || { is_period: false, flow: null }
          const flowDay = !readOnly && inMonth && log.flow && FLOW_DAY_STYLE[log.flow]
          const dayStyle = inMonth ? (flowDay || DEFAULT_DAY_STYLE) : OUTSIDE_DAY_STYLE
          return (
            <button
              key={ymd}
              type="button"
              onClick={() => onSelectDate(new Date(day))}
              style={dayStyle}
              aria-current={isToday ? 'date' : undefined}
              aria-pressed={isSelected}
              className={`
                aspect-square w-full min-h-10 rounded-lg flex items-center justify-center text-sm font-medium tabular-nums
                ${inMonth ? '' : 'opacity-35'}
                ${isSelected
                  ? 'ring-2 ring-powder-blush ring-offset-2 ring-offset-night-bordeaux'
                  : isToday
                    ? 'ring-2 ring-powder-blush/60'
                    : 'ring-1 ring-powder-blush/25'
                }
              `}
            >
              {day.getDate()}
            </button>
          )
        })}
      </div>
    </div>
  )
}
