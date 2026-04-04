import { useState, useEffect, useCallback } from 'react'
import Logo from './Logo'
import { api } from '../api/client'
import { getDailyLogs, upsertDailyLog } from '../api/dailyLogs'

const FLOW_OPTIONS = [
  { id: 'spots', label: 'Spots' },
  { id: 'light', label: 'Light' },
  { id: 'normal', label: 'Normal' },
  { id: 'heavy', label: 'Heavy' },
]

function toYMD(d) {
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function addDays(d, n) {
  const out = new Date(d)
  out.setDate(out.getDate() + n)
  return out
}

function getWindowDays(centerDate) {
  return [
    addDays(centerDate, -2),
    addDays(centerDate, -1),
    centerDate,
    addDays(centerDate, 1),
    addDays(centerDate, 2),
  ]
}

// Arc: outer days lower; scale ~1.5 for larger layout
const ARC_TRANSLATE_Y = [15, 6, 0, 6, 15]
const ARC_OPACITY = [0.3, 0.6, 1, 0.6, 0.3]

/** Default arc day (no flow selected). */
const DEFAULT_DAY_STYLE = { backgroundColor: '#fed0bb', color: '#461220' }

/** Background + text per flow (spots → heavy). */
const FLOW_DAY_STYLE = {
  spots: { backgroundColor: '#fcb9b2', color: '#461220' },
  light: { backgroundColor: '#b23a48', color: '#fed0bb' },
  normal: { backgroundColor: '#8c2f39', color: '#fed0bb' },
  heavy: { backgroundColor: '#461220', color: '#fed0bb' },
}

export default function Main() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const [selectedDate, setSelectedDate] = useState(() => new Date(today))
  const [logs, setLogs] = useState({})
  const [loading, setLoading] = useState(true)
  /** True after "Period started" until "Period ended" is saved (same for all days). */
  const [awaitingPeriodEnd, setAwaitingPeriodEnd] = useState(false)

  const windowDays = getWindowDays(selectedDate)
  const fromDate = toYMD(windowDays[0])
  const toDate = toYMD(windowDays[4])

  const fetchLogs = useCallback(async () => {
    setLoading(true)
    try {
      const list = await getDailyLogs(fromDate, toDate)
      const map = {}
      list.forEach((entry) => {
        map[entry.date] = { is_period: entry.is_period, flow: entry.flow }
      })
      setLogs(map)
    } catch {
      setLogs({})
    } finally {
      setLoading(false)
    }
  }, [fromDate, toDate])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  useEffect(() => {
    let cancelled = false
    api
      .get('/auth/me')
      .then(({ data }) => {
        if (!cancelled) setAwaitingPeriodEnd(!!data.awaiting_period_end)
      })
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  const selectedYMD = toYMD(selectedDate)
  // Default is_period to false for any day with no log
  const selectedLog = logs[selectedYMD] || { is_period: false, flow: null }

  const monthLabel = selectedDate.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })

  // Period: selected date → POST `date` + period_event → DB appends to cycle_start_dates / cycle_end_dates.
  const handlePeriodClick = async () => {
    const ymd = selectedYMD
    try {
      const res = await upsertDailyLog(ymd, {
        is_period: true,
        period_event: awaitingPeriodEnd ? 'end' : 'start',
      })
      setAwaitingPeriodEnd(!!res.awaiting_period_end)
      setLogs((prev) => ({
        ...prev,
        [ymd]: { ...(prev[ymd] || { is_period: false, flow: null }), is_period: true },
      }))
    } catch {
      // keep UI unchanged
    }
  }

  // Flow: only one option per day; selection is persisted. Clearing (click same again) sends null.
  const handleFlowSelect = async (flowId) => {
    const value = selectedLog.flow === flowId ? null : flowId
    try {
      await upsertDailyLog(selectedYMD, { flow: value })
      setLogs((prev) => ({
        ...prev,
        [selectedYMD]: { ...selectedLog, flow: value },
      }))
    } catch {
      // keep UI unchanged
    }
  }

  const goPrev = () => setSelectedDate((d) => addDays(d, -1))
  const goNext = () => setSelectedDate((d) => addDays(d, 1))

  const todayYMD = toYMD(today)

  return (
    <div className="min-h-screen flex flex-col items-center px-6 py-10 bg-night-bordeaux">
      <h1 className="text-2xl font-bold text-peach-fuzz mb-2">Aestas</h1>
      <Logo className="w-20 h-20 text-powder-blush mb-8" />

      <div className="w-full max-w-lg">
        {/* Month header */}
        <p className="text-peach-fuzz font-semibold text-xl text-center mb-6">
          {monthLabel}
        </p>

        {/* Arced calendar: 5 days, arrows at same height as lowest day squares (+2 / -2) */}
        <div className="flex items-end justify-center gap-3 mb-10">
          <button
            type="button"
            onClick={goPrev}
            className="flex-shrink-0 w-12 h-12 rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium text-xl transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50"
            aria-label="Previous day"
          >
            ←
          </button>
          <div className="overflow-x-auto overflow-y-hidden flex-1 min-w-0 -mx-2 px-2 pb-2 touch-pan-x scroll-smooth">
            <div className="flex items-end justify-center gap-3 min-h-[87px]">
              {windowDays.map((day, i) => {
                const ymd = toYMD(day)
                const isCenter = ymd === selectedYMD
                const isToday = ymd === todayYMD
                const log = logs[ymd] || { is_period: false, flow: null }
                const flowDay = log.flow && FLOW_DAY_STYLE[log.flow]
                const dayStyle = flowDay || DEFAULT_DAY_STYLE
                return (
                  <button
                    key={ymd}
                    type="button"
                    onClick={() => setSelectedDate(new Date(day))}
                    style={{
                      transform: `translateY(${ARC_TRANSLATE_Y[i]}px)`,
                      opacity: ARC_OPACITY[i],
                      ...dayStyle,
                    }}
                    className={`
                      w-[72px] h-[72px] rounded-2xl flex flex-col items-center justify-center text-base font-medium transition-colors flex-shrink-0
                      ${isCenter
                        ? 'ring-2 ring-powder-blush ring-offset-2 ring-offset-night-bordeaux'
                        : `ring-2 ${isToday ? 'ring-powder-blush/50' : 'ring-powder-blush/35'}`
                      }
                    `}
                  >
                    <span className="text-sm opacity-90">
                      {day.toLocaleDateString(undefined, { weekday: 'short' }).slice(0, 2)}
                    </span>
                    <span className="tabular-nums">{day.getDate()}</span>
                  </button>
                )
              })}
            </div>
          </div>
          <button
            type="button"
            onClick={goNext}
            className="flex-shrink-0 w-12 h-12 rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium text-xl transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50"
            aria-label="Next day"
          >
            →
          </button>
        </div>

        {/* Period button: global cycle — "Period Ended" until end date is saved; then "Period Started" again */}
        <div className="mb-8">
          <button
            type="button"
            onClick={handlePeriodClick}
            disabled={loading}
            className={`
              w-full rounded-2xl font-semibold py-4 px-8 text-lg transition-colors
              ${awaitingPeriodEnd
                ? 'bg-burnt-rose text-white hover:bg-dusty-mauve'
                : 'bg-dusty-mauve/60 text-peach-fuzz hover:bg-dusty-mauve'
              }
              disabled:opacity-50
            `}
          >
            {awaitingPeriodEnd ? 'Period Ended' : 'Period Started'}
          </button>
        </div>

        {/* Flow icons */}
        <p className="text-powder-blush/90 text-base text-center mb-3">Flow</p>
        <div className="flex justify-center gap-5 flex-wrap">
          {FLOW_OPTIONS.map((opt) => (
            <button
              key={opt.id}
              type="button"
              onClick={() => handleFlowSelect(opt.id)}
              disabled={loading}
              className={`
                rounded-2xl px-6 py-3 text-base font-medium transition-colors
                ${selectedLog.flow === opt.id
                  ? 'bg-dusty-mauve text-white ring-2 ring-powder-blush/50'
                  : 'bg-dusty-mauve/30 text-powder-blush/80 hover:bg-dusty-mauve/50'
                }
                disabled:opacity-50
              `}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
