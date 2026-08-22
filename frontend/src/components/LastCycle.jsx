import { useState, useRef, useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { submitLastCycle } from '../api/onboarding'
import { errorMessage } from '../api/client'
import { toYMD } from '../cycle/dates'

const DAY_NAMES = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const WEEKS_BACK = 16
const WEEKS_AHEAD = 2

function getWeekStart(d) {
  const date = new Date(d)
  const day = date.getDay()
  date.setDate(date.getDate() - day)
  date.setHours(0, 0, 0, 0)
  return date
}

/** Label for a single month */
function getMonthLabel(month, year) {
  const d = new Date(year, month, 1)
  return d.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
}

/** For a week, return one or two { month, year } for the month(s) in the week */
function getWeekMonths(days) {
  const first = days[0]
  const last = days[6]
  if (first.getMonth() === last.getMonth() && first.getFullYear() === last.getFullYear()) {
    return [{ month: first.getMonth(), year: first.getFullYear() }]
  }
  return [
    { month: first.getMonth(), year: first.getFullYear() },
    { month: last.getMonth(), year: last.getFullYear() },
  ]
}

function buildWeeks() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const start = getWeekStart(today)
  start.setDate(start.getDate() - WEEKS_BACK * 7)
  const weeks = []
  for (let w = 0; w < WEEKS_BACK + WEEKS_AHEAD; w++) {
    const weekStart = new Date(start)
    weekStart.setDate(weekStart.getDate() + w * 7)
    const days = []
    for (let d = 0; d < 7; d++) {
      const day = new Date(weekStart)
      day.setDate(weekStart.getDate() + d)
      days.push(day)
    }
    weeks.push(days)
  }
  return weeks
}

function getCurrentWeekIndex(weeks, todayYMD) {
  return weeks.findIndex((days) => days.some((d) => toYMD(d) === todayYMD))
}

export default function LastCycle() {
  const navigate = useNavigate()
  const location = useLocation()
  const cycleLength = location.state?.cycleLength ?? 28
  const [selected, setSelected] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const scrollRef = useRef(null)
  const weekRefs = useRef([])
  const [viewWeekIndex, setViewWeekIndex] = useState(null)

  const weeks = buildWeeks()
  const todayYMD = toYMD(new Date())
  const currentWeekIndex = getCurrentWeekIndex(weeks, todayYMD)

  useEffect(() => {
    if (viewWeekIndex === null && currentWeekIndex >= 0) {
      setViewWeekIndex(currentWeekIndex)
      return
    }
    if (viewWeekIndex !== null && weekRefs.current[viewWeekIndex]) {
      weekRefs.current[viewWeekIndex].scrollIntoView({ inline: 'center', block: 'nearest', behavior: 'smooth' })
    }
  }, [viewWeekIndex, currentWeekIndex])

  const goPrevWeek = () => setViewWeekIndex((i) => (i === null ? 0 : Math.max(0, i - 1)))
  const goNextWeek = () => setViewWeekIndex((i) => (i === null ? 0 : Math.min(weeks.length - 1, (i ?? 0) + 1)))

  async function handleSubmit(e) {
    e.preventDefault()
    if (!selected) {
      setError('Please select a date.')
      return
    }
    setError(null)
    setIsSubmitting(true)
    try {
      await submitLastCycle(toYMD(selected))
      navigate('/blooming', { replace: true, state: { cycleLength } })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-night-bordeaux">
      <div className="max-w-lg w-full text-center">
        <h1 className="text-3xl font-bold text-peach-fuzz mb-2">
          When was your last cycle?
        </h1>
        <p className="text-powder-blush/90 mb-6">
          Tap the first day of your last period.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="flex items-center justify-center gap-3">
            <button
              type="button"
              onClick={goPrevWeek}
              disabled={viewWeekIndex === 0}
              className="flex-shrink-0 w-12 h-12 rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 disabled:opacity-40 disabled:pointer-events-none text-peach-fuzz font-medium text-xl transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50"
              aria-label="Previous week"
            >
              ←
            </button>
            <div ref={scrollRef} className="overflow-x-auto overflow-y-hidden flex-1 min-w-0 -mx-2 px-2 pb-2 touch-pan-x scroll-smooth">
              <div className="flex gap-4 min-w-max">
              {weeks.map((days, wi) => {
                const months = getWeekMonths(days)
                const isTwoMonths = months.length === 2
                const cards = isTwoMonths
                  ? [
                      { label: getMonthLabel(months[0].month, months[0].year), focus: months[0] },
                      { label: getMonthLabel(months[1].month, months[1].year), focus: months[1] },
                    ]
                  : [{ label: getMonthLabel(months[0].month, months[0].year), focus: months[0] }]

                return cards.map((card, ci) => (
                  <div
                    key={`${wi}-${ci}`}
                    ref={ci === 0 ? (el) => { weekRefs.current[wi] = el } : undefined}
                    className="flex-shrink-0 w-[280px] rounded-xl bg-dusty-mauve/20 border border-powder-blush/30 p-3"
                  >
                    <p className="text-powder-blush font-medium text-sm mb-2 text-center">
                      {card.label}
                    </p>
                    <div className="grid grid-cols-7 gap-1 mb-2">
                      {DAY_NAMES.map((name) => (
                        <div
                          key={name}
                          className="text-powder-blush/70 text-xs font-medium text-center py-1"
                        >
                          {name}
                        </div>
                      ))}
                    </div>
                    <div className="grid grid-cols-7 gap-1">
                      {days.map((day) => {
                        const ymd = toYMD(day)
                        const isSelected = selected && toYMD(selected) === ymd
                        const isToday = ymd === todayYMD
                        const isInFocusMonth =
                          day.getMonth() === card.focus.month && day.getFullYear() === card.focus.year
                        const baseStyle = isInFocusMonth
                          ? 'bg-night-bordeaux/60 text-peach-fuzz hover:bg-dusty-mauve/40'
                          : 'bg-night-bordeaux/30 text-peach-fuzz/50 hover:bg-dusty-mauve/30'
                        return (
                          <button
                            key={ymd}
                            type="button"
                            onClick={() => setSelected(day)}
                            className={`
                              w-9 h-9 rounded-lg text-sm font-medium transition-colors
                              ${isSelected
                                ? 'bg-dusty-mauve text-white ring-2 ring-powder-blush'
                                : baseStyle
                              }
                              ${isToday && !isSelected ? 'ring-2 ring-powder-blush/50' : ''}
                            `}
                          >
                            {day.getDate()}
                          </button>
                        )
                      })}
                    </div>
                  </div>
                ))
              })}
              </div>
            </div>
            <button
              type="button"
              onClick={goNextWeek}
              disabled={viewWeekIndex !== null && viewWeekIndex >= weeks.length - 1}
              className="flex-shrink-0 w-12 h-12 rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 disabled:opacity-40 disabled:pointer-events-none text-peach-fuzz font-medium text-xl transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50"
              aria-label="Next week"
            >
              →
            </button>
          </div>

          {selected && (
            <p className="text-powder-blush/80 text-sm">
              Selected: {selected.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric', year: 'numeric' })}
            </p>
          )}

          {error && (
            <div
              className="rounded-xl bg-burnt-rose/30 border border-burnt-rose text-peach-fuzz p-3 text-sm"
              role="alert"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !selected}
            className="w-full rounded-xl bg-dusty-mauve hover:bg-burnt-rose disabled:opacity-50 text-white font-semibold py-3 px-6 transition-colors"
          >
            {isSubmitting ? 'Saving…' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}
