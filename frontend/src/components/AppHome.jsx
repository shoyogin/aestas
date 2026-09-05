import { useCallback, useEffect, useMemo, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { errorMessage } from '../api/client'
import { getDailyLogs, upsertDailyLog } from '../api/dailyLogs'
import { getCycleContext } from '../api/cycle'
import { getPhaseContent } from '../api/content'
import { useAuth } from '../context/authContext'
import { getPhaseForDate } from '../cycle/phaseEngine'
import { toYMD, today, startOfMonth, endOfMonth } from '../cycle/dates'
import { CycleContext } from '../hooks/useCycle'

const FLOW_OPTIONS = [
  { id: 'spots', label: 'Spots' },
  { id: 'light', label: 'Light' },
  { id: 'normal', label: 'Normal' },
  { id: 'heavy', label: 'Heavy' },
]

const EMPTY_LOG = { is_period: false, flow: null }

export default function AppHome() {
  const { user, setUser } = useAuth()
  const [selectedDate, setSelectedDate] = useState(today)
  const [logs, setLogs] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState(null)
  const [cycleLength, setCycleLength] = useState(null)
  const [cycleStartDates, setCycleStartDates] = useState([])
  const [cycleEndDates, setCycleEndDates] = useState([])
  const [phaseContent, setPhaseContent] = useState(null)

  const awaitingPeriodEnd = !!user?.awaiting_period_end

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
    } catch (err) {
      setLogs({})
      setError(errorMessage(err, 'Could not load your logs.'))
    } finally {
      setLoading(false)
    }
  }, [fromDate, toDate])

  useEffect(() => {
    fetchLogs()
  }, [fetchLogs])

  const fetchCycleContext = useCallback(async () => {
    try {
      const data = await getCycleContext()
      setCycleLength(data.cycle_length ?? null)
      setCycleStartDates(data.cycle_start_dates ?? [])
      setCycleEndDates(data.cycle_end_dates ?? [])
    } catch (err) {
      setError(errorMessage(err, 'Could not load your cycle.'))
    }
  }, [])

  useEffect(() => {
    fetchCycleContext()
  }, [fetchCycleContext])

  useEffect(() => {
    // Panel copy lives on the server so it is never written in two places.
    let cancelled = false
    getPhaseContent()
      .then((data) => !cancelled && setPhaseContent(data))
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [])

  const selectedYMD = toYMD(selectedDate)
  const selectedLog = logs[selectedYMD] || EMPTY_LOG
  const monthLabel = selectedDate.toLocaleDateString(undefined, {
    month: 'long',
    year: 'numeric',
  })

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
    setSaving(true)
    setError(null)
    try {
      const res = await upsertDailyLog(selectedYMD, {
        is_period: true,
        period_event: awaitingPeriodEnd ? 'end' : 'start',
      })
      setUser((prev) =>
        prev ? { ...prev, awaiting_period_end: !!res.awaiting_period_end } : prev,
      )
      if (res.cycle_start_dates) setCycleStartDates(res.cycle_start_dates)
      if (res.cycle_end_dates) setCycleEndDates(res.cycle_end_dates)
      setLogs((prev) => ({
        ...prev,
        [selectedYMD]: { ...(prev[selectedYMD] || EMPTY_LOG), is_period: true },
      }))
    } catch (err) {
      // Silently ignoring this made the button look like it did nothing.
      setError(errorMessage(err, 'Could not save that. Please try again.'))
    } finally {
      setSaving(false)
    }
  }

  const handleFlowSelect = async (flowId) => {
    const value = selectedLog.flow === flowId ? null : flowId
    setSaving(true)
    setError(null)
    try {
      const res = await upsertDailyLog(selectedYMD, { flow: value })
      setLogs((prev) => ({
        ...prev,
        [selectedYMD]: { ...(prev[selectedYMD] || EMPTY_LOG), flow: res.flow ?? null },
      }))
    } catch (err) {
      setError(errorMessage(err, 'Could not save that flow. Please try again.'))
    } finally {
      setSaving(false)
    }
  }

  const value = useMemo(
    () => ({
      selectedDate,
      setSelectedDate,
      logs,
      loading,
      saving,
      error,
      dismissError: () => setError(null),
      awaitingPeriodEnd,
      cycleLength,
      selectedLog,
      monthLabel,
      phaseInfo,
      phaseContent,
      handlePeriodClick,
      handleFlowSelect,
      FLOW_OPTIONS,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [
      selectedDate, logs, loading, saving, error, awaitingPeriodEnd,
      cycleLength, selectedLog, monthLabel, phaseInfo, phaseContent,
    ],
  )

  return (
    <CycleContext.Provider value={value}>
      <Outlet />
    </CycleContext.Provider>
  )
}
