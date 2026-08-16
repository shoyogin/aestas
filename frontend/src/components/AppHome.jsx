import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { api } from '../api/client'
import { getDailyLogs, upsertDailyLog } from '../api/dailyLogs'
import { getCycleContext } from '../api/cycle'
import { getPhaseForDate } from '../cycle/phaseEngine'
import { toYMD, startOfMonth, endOfMonth } from './CalendarArc'

const CycleContext = createContext(null)

export function useCycle() {
  const ctx = useContext(CycleContext)
  if (!ctx) throw new Error('useCycle must be used inside AppHome')
  return ctx
}

const FLOW_OPTIONS = [
  { id: 'spots', label: 'Spots' },
  { id: 'light', label: 'Light' },
  { id: 'normal', label: 'Normal' },
  { id: 'heavy', label: 'Heavy' },
]

export default function AppHome() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const [selectedDate, setSelectedDate] = useState(() => new Date(today))
  const [logs, setLogs] = useState({})
  const [loading, setLoading] = useState(true)
  const [awaitingPeriodEnd, setAwaitingPeriodEnd] = useState(false)
  const [cycleLength, setCycleLength] = useState(null)
  const [cycleStartDates, setCycleStartDates] = useState([])
  const [cycleEndDates, setCycleEndDates] = useState([])

  const fromDate = toYMD(startOfMonth(selectedDate))
  const toDate = toYMD(endOfMonth(selectedDate))

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

  const fetchCycleContext = useCallback(async () => {
    try {
      const data = await getCycleContext()
      setCycleLength(data.cycle_length ?? null)
      setCycleStartDates(data.cycle_start_dates ?? [])
      setCycleEndDates(data.cycle_end_dates ?? [])
    } catch {
      setCycleLength(null)
      setCycleStartDates([])
      setCycleEndDates([])
    }
  }, [])

  useEffect(() => {
    fetchCycleContext()
  }, [fetchCycleContext])

  const selectedYMD = toYMD(selectedDate)
  const selectedLog = logs[selectedYMD] || { is_period: false, flow: null }
  const monthLabel = selectedDate.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })

  const phaseInfo = useMemo(
    () =>
      getPhaseForDate({
        selectedDate,
        cycleLength,
        startDates: cycleStartDates,
        endDates: cycleEndDates,
      }),
    [selectedDate, cycleLength, cycleStartDates, cycleEndDates],
  )

  const handlePeriodClick = async () => {
    const ymd = selectedYMD
    try {
      const res = await upsertDailyLog(ymd, {
        is_period: true,
        period_event: awaitingPeriodEnd ? 'end' : 'start',
      })
      setAwaitingPeriodEnd(!!res.awaiting_period_end)
      if (res.cycle_start_dates) setCycleStartDates(res.cycle_start_dates)
      if (res.cycle_end_dates) setCycleEndDates(res.cycle_end_dates)
      setLogs((prev) => ({
        ...prev,
        [ymd]: { ...(prev[ymd] || { is_period: false, flow: null }), is_period: true },
      }))
    } catch {
      /* keep UI */
    }
  }

  const handleFlowSelect = async (flowId) => {
    const value = selectedLog.flow === flowId ? null : flowId
    try {
      await upsertDailyLog(selectedYMD, { flow: value })
      setLogs((prev) => ({
        ...prev,
        [selectedYMD]: { ...selectedLog, flow: value },
      }))
    } catch {
      /* keep UI */
    }
  }

  const value = {
    selectedDate,
    setSelectedDate,
    logs,
    loading,
    awaitingPeriodEnd,
    cycleLength,
    selectedLog,
    monthLabel,
    phaseInfo,
    handlePeriodClick,
    handleFlowSelect,
    FLOW_OPTIONS,
  }

  return (
    <CycleContext.Provider value={value}>
      <Outlet />
    </CycleContext.Provider>
  )
}
