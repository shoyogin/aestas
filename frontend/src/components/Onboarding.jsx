import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { submitOnboarding } from '../api/onboarding'

const CYCLE_LENGTH_MIN = 21
const CYCLE_LENGTH_MAX = 45
const DEFAULT_CYCLE_LENGTH = 28

export default function Onboarding() {
  const navigate = useNavigate()
  const [cycleLength, setCycleLength] = useState(DEFAULT_CYCLE_LENGTH)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setIsSubmitting(true)
    try {
      await submitOnboarding(cycleLength)
      navigate('/app', { replace: true })
    } catch (err) {
      setError(err.response?.data?.detail || 'Something went wrong. Please try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center px-6 bg-night-bordeaux">
      <div className="max-w-lg w-full">
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
              className="block text-sm font-medium text-powder-blush mb-2"
            >
              How many days is your typical cycle?
            </label>
            <input
              id="cycle-length"
              type="number"
              min={CYCLE_LENGTH_MIN}
              max={CYCLE_LENGTH_MAX}
              value={cycleLength}
              onChange={(e) =>
                setCycleLength(
                  Math.min(
                    CYCLE_LENGTH_MAX,
                    Math.max(CYCLE_LENGTH_MIN, Number(e.target.value) || DEFAULT_CYCLE_LENGTH)
                  )
                )
              }
              className="w-full rounded-xl border-2 border-dusty-mauve/50 bg-night-bordeaux/80 text-peach-fuzz px-4 py-3 focus:border-powder-blush focus:ring-2 focus:ring-powder-blush/20 outline-none transition"
            />
            <p className="mt-1 text-sm text-powder-blush/70">
              Between {CYCLE_LENGTH_MIN} and {CYCLE_LENGTH_MAX} days
            </p>
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
