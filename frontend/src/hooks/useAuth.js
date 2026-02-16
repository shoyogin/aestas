import { useState, useEffect } from 'react'
import { api } from '../api/client'

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [hasCompletedOnboarding, setHasCompletedOnboarding] = useState(false)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    async function checkSession() {
      try {
        const { data } = await api.get('/auth/me')
        setIsAuthenticated(true)
        setHasCompletedOnboarding(data.has_completed_onboarding ?? false)
      } catch {
        setIsAuthenticated(false)
        setHasCompletedOnboarding(false)
      } finally {
        setIsLoading(false)
      }
    }
    checkSession()
  }, [])

  return { isAuthenticated, hasCompletedOnboarding, isLoading }
}
