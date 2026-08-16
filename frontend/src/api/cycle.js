import { api } from './client'

/**
 * Cycle length and recorded start/end dates for the logged-in user.
 * @returns {Promise<{ cycle_length: number | null, cycle_start_dates: string[], cycle_end_dates: string[] }>}
 */
export async function getCycleContext() {
  const { data } = await api.get('/users/cycle-context')
  return data
}
