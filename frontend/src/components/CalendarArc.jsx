import { CALENDAR_WIDTH, toYMD, today, endOfMonth, getMonthGrid } from '../cycle/dates'

const FLOW_DAY_STYLE = {
  spots: { backgroundColor: '#fcb9b2', color: '#461220' },
  light: { backgroundColor: '#b23a48', color: '#fed0bb' },
  normal: { backgroundColor: '#8c2f39', color: '#fed0bb' },
  heavy: { backgroundColor: '#461220', color: '#fed0bb' },
}

/** A period day with no flow recorded still has to look like a period day. */
const PERIOD_DAY_STYLE = { backgroundColor: '#b23a48', color: '#fed0bb' }
const DEFAULT_DAY_STYLE = { backgroundColor: '#fed0bb', color: '#461220' }
const WEEKDAYS = [
  { key: 'sun', label: 'S' },
  { key: 'mon', label: 'M' },
  { key: 'tue', label: 'T' },
  { key: 'wed', label: 'W' },
  { key: 'thu', label: 'T' },
  { key: 'fri', label: 'F' },
  { key: 'sat', label: 'S' },
]

function shiftMonth(d, delta) {
  const next = new Date(d.getFullYear(), d.getMonth() + delta, 1)
  const last = endOfMonth(next).getDate()
  next.setDate(Math.min(d.getDate(), last))
  next.setHours(0, 0, 0, 0)
  return next
}

const ARROW =
  'flex-shrink-0 w-9 h-9 rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium text-base transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50'

function dayLabel(day, log) {
  const date = day.toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })
  if (log.flow) return `${date}, ${log.flow} flow`
  if (log.is_period) return `${date}, period day`
  return date
}

export default function CalendarArc({
  selectedDate,
  onSelectDate,
  logs = {},
  readOnly = false,
}) {
  const todayYMD = toYMD(today())
  const selectedYMD = toYMD(selectedDate)
  const viewMonth = selectedDate.getMonth()
  const viewYear = selectedDate.getFullYear()
  const gridDays = getMonthGrid(selectedDate)
  const monthLabel = selectedDate.toLocaleDateString(undefined, {
    month: 'long',
    year: 'numeric',
  })

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
        <p className="text-peach-fuzz font-semibold text-base text-center flex-1" aria-live="polite">
          {monthLabel}
        </p>
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
        {WEEKDAYS.map((weekday) => (
          <div
            key={weekday.key}
            className="text-center text-xs font-semibold text-powder-blush/80 pb-1"
            aria-hidden
          >
            {weekday.label}
          </div>
        ))}
        {gridDays.map((day) => {
          const ymd = toYMD(day)
          const inMonth = day.getMonth() === viewMonth && day.getFullYear() === viewYear
          const isSelected = ymd === selectedYMD
          const isToday = ymd === todayYMD
          const log = logs[ymd] || { is_period: false, flow: null }
          const showLog = !readOnly && inMonth
          const dayStyle =
            (showLog && (FLOW_DAY_STYLE[log.flow] || (log.is_period && PERIOD_DAY_STYLE))) ||
            DEFAULT_DAY_STYLE
          return (
            <button
              key={ymd}
              type="button"
              onClick={() => onSelectDate(new Date(day))}
              style={dayStyle}
              aria-current={isToday ? 'date' : undefined}
              aria-pressed={isSelected}
              aria-label={dayLabel(day, showLog ? log : { is_period: false, flow: null })}
              className={`
                aspect-square w-full min-h-10 rounded-lg flex items-center justify-center text-sm font-medium tabular-nums
                ${inMonth ? '' : 'opacity-50'}
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
