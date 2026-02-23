import { useEffect } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import Logo from './Logo'

const DEFAULT_CYCLE_LENGTH = 28

export default function Blooming() {
  const navigate = useNavigate()
  const location = useLocation()
  const cycleLength = location.state?.cycleLength ?? DEFAULT_CYCLE_LENGTH

  useEffect(() => {
    const t = setTimeout(() => {
      navigate('/app', { replace: true })
    }, 3000)
    return () => clearTimeout(t)
  }, [navigate])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-night-bordeaux">
      <div className="max-w-md w-full text-center space-y-8">
        <Logo className="mx-auto w-20 h-20 text-powder-blush" />
        <p
          className="text-2xl md:text-3xl font-medium text-peach-fuzz text-center animate-bloom-fade-in-out"
          role="status"
          aria-live="polite"
        >
          Blooming every day, {cycleLength} days a month.
        </p>
      </div>
    </div>
  )
}
