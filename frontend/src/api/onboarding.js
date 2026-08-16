import { api } from './client'

/**
 * Submit onboarding data (cycle length) for the current user.
 * Requires an active session (cookie).
 */
export async function submitOnboarding(cycleLength) {
  const { data } = await api.post('/users/onboarding', { cycle_length: cycleLength })
  return data
}

/**
 * Submit last cycle start date (YYYY-MM-DD). Requires an active session.
 */
export async function submitLastCycle(lastCycleStart) {
  const { data } = await api.post('/users/onboarding/last-cycle', {
    last_cycle_start: lastCycleStart,
  })
  return data
}
