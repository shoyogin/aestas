import { api } from './client'

/**
 * Fetch daily logs for a date range (inclusive). Returns [{ date, is_period, flow }, ...].
 */
export async function getDailyLogs(fromDate, toDate) {
  const { data } = await api.get('/users/daily-logs', {
    params: { from: fromDate, to: toDate },
  })
  return data
}

/**
 * Upsert daily log for a date. is_period and flow are optional (only send what changed).
 */
export async function upsertDailyLog(date, payload) {
  const { data } = await api.post('/users/daily-logs', { date, ...payload })
  return data
}
