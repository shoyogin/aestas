import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitOnboarding } from '../api/onboarding'
import { errorMessage } from '../api/client'
import { useAuth } from '../context/authContext'

const CYCLE_LENGTH_MIN = 15
const CYCLE_LENGTH_MAX = 45
const DEFAULT_CYCLE_LENGTH = 28

function clamp(value) {
  return Math.min(CYCLE_LENGTH_MAX, Math.max(CYCLE_LENGTH_MIN, Number(value) || DEFAULT_CYCLE_LENGTH))
}

export default function Onboarding() {
  const navigate = useNavigate()
  const { refresh } = useAuth()
  const [cycleLength, setCycleLength] = useState(DEFAULT_CYCLE_LENGTH)
  const [inputValue, setInputValue] = useState(String(DEFAULT_CYCLE_LENGTH))
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const syncFromInput = (raw) => {
    setInputValue(raw)
    const num = Number(raw)
    if (!Number.isNaN(num) && raw !== '') {
      setCycleLength(clamp(num))
    }
  }

  const setDays = (n) => {
    const clamped = clamp(n)
    setCycleLength(clamped)
    setInputValue(String(clamped))
  }

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    const num = Number(inputValue)
    const valueToSubmit = Number.isNaN(num) || inputValue === '' ? cycleLength : clamp(num)
    setCycleLength(valueToSubmit)
    setInputValue(String(valueToSubmit))
    setIsSubmitting(true)
    try {
      await submitOnboarding(valueToSubmit)
      // Without this the route guard still believes onboarding is unfinished.
      await refresh()
      navigate('/onboarding/last-cycle', { replace: true, state: { cycleLength: valueToSubmit } })
    } catch (err) {
      setError(errorMessage(err))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-night-bordeaux">
      <div className="max-w-lg w-full text-center">
        <h1 className="text-3xl font-bold text-peach-fuzz mb-2">
          Almost there
        </h1>
        <p className="text-powder-blush/90 mb-8">
          Tell us one thing so we can personalize your experience.
        </p>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="cycle-length"
              className="block text-m font-bold text-powder-blush mb-3"
            >
              How many days is your typical cycle?
            </label>
            <div className="flex items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => setDays(cycleLength - 1)}
                disabled={cycleLength <= CYCLE_LENGTH_MIN}
                className="flex-shrink-0 w-12 h-12 rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 disabled:opacity-40 disabled:pointer-events-none text-peach-fuzz font-medium text-xl transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50"
                aria-label="Decrease days"
              >
                −
              </button>
              <input
                id="cycle-length"
                type="number"
                min={CYCLE_LENGTH_MIN}
                max={CYCLE_LENGTH_MAX}
                value={inputValue}
                onChange={(e) => syncFromInput(e.target.value)}
                onBlur={() => {
                  const num = Number(inputValue)
                  const clamped = Number.isNaN(num) || inputValue === '' ? DEFAULT_CYCLE_LENGTH : clamp(num)
                  setCycleLength(clamped)
                  setInputValue(String(clamped))
                }}
                className="flex-1 min-w-0 rounded-xl border-2 border-dusty-mauve/50 bg-night-bordeaux/80 text-peach-fuzz text-center text-2xl font-semibold tabular-nums py-4 px-4 focus:border-powder-blush focus:ring-2 focus:ring-powder-blush/20 outline-none transition placeholder:text-powder-blush/40 [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />
              <button
                type="button"
                onClick={() => setDays(cycleLength + 1)}
                disabled={cycleLength >= CYCLE_LENGTH_MAX}
                className="flex-shrink-0 w-12 h-12 rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 disabled:opacity-40 disabled:pointer-events-none text-peach-fuzz font-medium text-xl transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50"
                aria-label="Increase days"
              >
                +
              </button>
            </div>
          </div>

          <div
            className="rounded-xl bg-dusty-mauve/20 border border-powder-blush/30 p-4 text-powder-blush text-sm"
            role="status"
          >
            <strong className="text-peach-fuzz">Did you know?</strong> A typical
            cycle is about 28 days, but it can vary. We use this to give you
            better predictions.
          </div>

          {error && (
            <div
              className="rounded-xl bg-burnt-rose/30 border border-burnt-rose text-peach-fuzz p-3 text-sm"
              role="alert"
            >
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-xl bg-dusty-mauve hover:bg-burnt-rose disabled:opacity-50 text-white font-semibold py-3 px-6 transition-colors"
          >
            {isSubmitting ? 'Saving…' : 'Continue'}
          </button>
        </form>
      </div>
    </div>
  )
}
