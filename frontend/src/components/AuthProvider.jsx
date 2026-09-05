import { useCallback, useEffect, useMemo, useState } from 'react'
import { AuthContext } from '../context/authContext'
import { api, setSessionExpiredHandler } from '../api/client'
import { getMe } from '../api/auth'
import { updateProfile } from '../api/follows'
import { browserTimezone } from '../cycle/dates'

/**
 * Single owner of "who is signed in". Every screen reads this instead of
 * calling /auth/me for itself, and `refresh()` lets onboarding update the
 * answer without a full page reload.
 */
export default function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [isLoading, setIsLoading] = useState(true)

  const refresh = useCallback(async () => {
    try {
      const data = await getMe()
      setUser(data)
      return data
    } catch {
      setUser(null)
      return null
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    getMe()
      .then((data) => {
        if (cancelled) return
        setUser(data)
        // Keep the server on the same calendar day as this browser, so the
        // phase it computes for friends matches what the user sees.
        const tz = browserTimezone()
        if (data.timezone !== tz) {
          updateProfile({ timezone: tz })
            .then(() => !cancelled && setUser((prev) => (prev ? { ...prev, timezone: tz } : prev)))
            .catch(() => {})
        }
      })
      .catch(() => {
        if (!cancelled) setUser(null)
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    // An expired session used to leave every screen silently empty.
    setSessionExpiredHandler(() => setUser(null))
    return () => setSessionExpiredHandler(null)
  }, [])

  const value = useMemo(
    () => ({
      user,
      isLoading,
      isAuthenticated: !!user,
      hasCompletedOnboarding: !!user?.has_completed_onboarding,
      refresh,
      setUser,
      loginUrl: `${api.defaults.baseURL}/auth/google`,
    }),
    [user, isLoading, refresh],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
