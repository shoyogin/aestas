import { createContext, useContext } from 'react'

export const CycleContext = createContext(null)

export function useCycle() {
  const ctx = useContext(CycleContext)
  if (!ctx) throw new Error('useCycle must be used inside AppHome')
  return ctx
}
