import { createContext, useContext } from 'react'

export const AuthContext = createContext(null)

/**
 * The signed-in user, fetched once for the whole app.
 * `user` is null while loading and when signed out — check `isLoading` first.
 */
export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
