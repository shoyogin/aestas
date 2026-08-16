import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Logo from './Logo'
import { api } from '../api/client'
import { logout } from '../api/auth'
import { patchNickname } from '../api/follows'
import { getCycleContext } from '../api/cycle'

const BTN =
  'rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium px-4 py-3 transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50'
const INPUT =
  'w-full rounded-xl border-2 border-dusty-mauve/50 bg-night-bordeaux/80 text-peach-fuzz px-4 py-3 focus:border-powder-blush outline-none'

function initials(name, email) {
  const s = (name || email || '?').replace(/^_/, '')
  return s.slice(0, 2).toUpperCase()
}

export default function Account() {
  const [email, setEmail] = useState('')
  const [nickname, setNickname] = useState('')
  const [nickDraft, setNickDraft] = useState('')
  const [cycleLength, setCycleLength] = useState(null)
  const [error, setError] = useState(null)
  const [info, setInfo] = useState(null)
  const [signingOut, setSigningOut] = useState(false)

  useEffect(() => {
    let cancelled = false
    Promise.all([api.get('/auth/me'), getCycleContext()])
      .then(([me, cycle]) => {
        if (cancelled) return
        setEmail(me.data.email || '')
        setNickname(me.data.nickname || '')
        setNickDraft(me.data.nickname || '')
        setCycleLength(cycle.cycle_length ?? null)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load account.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  const saveNick = async (e) => {
    e.preventDefault()
    setError(null)
    setInfo(null)
    try {
      const data = await patchNickname(nickDraft)
      setNickname(data.nickname)
      setNickDraft(data.nickname)
      setInfo('Nickname saved. Others find you by this name, not your email.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save nickname.')
    }
  }

  const signOut = async () => {
    setSigningOut(true)
    setError(null)
    try {
      await logout()
      window.location.assign('/')
    } catch {
      setSigningOut(false)
      setError('Could not sign out.')
    }
  }

  return (
    <div className="flex flex-col items-center px-6 py-8">
      <h1 className="text-2xl font-bold text-peach-fuzz mb-2">Account</h1>
      <Logo className="w-16 h-16 text-powder-blush mb-6" />
      <div className="w-full max-w-md space-y-8">
        {error && (
          <div className="rounded-xl bg-burnt-rose/30 border border-burnt-rose p-3 text-sm" role="alert">
            {error}
          </div>
        )}
        {info && (
          <p className="text-powder-blush text-sm text-center" role="status">{info}</p>
        )}

        <div className="flex items-center gap-4 rounded-2xl border border-powder-blush/30 bg-dusty-mauve/15 px-4 py-4">
          <span className="flex-shrink-0 w-14 h-14 rounded-full bg-burnt-rose text-peach-fuzz font-semibold flex items-center justify-center text-lg">
            {initials(nickname, email)}
          </span>
          <div className="min-w-0">
            <p className="font-semibold text-peach-fuzz truncate">{nickname || 'No nickname yet'}</p>
            <p className="text-powder-blush text-sm truncate">{email || '—'}</p>
          </div>
        </div>

        <form onSubmit={saveNick} className="space-y-3">
          <label htmlFor="account-nick" className="block font-semibold">Nickname</label>
          <p className="text-powder-blush/80 text-sm">
            3–24 characters: letters, numbers, underscore. Unique, lowercase.
          </p>
          <input
            id="account-nick"
            value={nickDraft}
            onChange={(e) => setNickDraft(e.target.value)}
            className={INPUT}
            placeholder="e.g. luna_28"
            autoComplete="off"
          />
          <button type="submit" className={`${BTN} w-full font-semibold`}>
            {nickname ? 'Update nickname' : 'Save nickname'}
          </button>
        </form>

        <div>
          <p className="font-semibold mb-1">Typical cycle length</p>
          <p className="text-powder-blush">
            {cycleLength ? `${cycleLength} days` : 'Not set'}
          </p>
        </div>

        <Link
          to="/circle"
          className="block text-center rounded-xl border border-powder-blush/40 py-3 font-semibold text-peach-fuzz hover:bg-dusty-mauve/20"
        >
          Manage circle
        </Link>

        <button
          type="button"
          onClick={signOut}
          disabled={signingOut}
          className="w-full rounded-2xl font-semibold py-4 bg-burnt-rose/80 text-peach-fuzz hover:bg-burnt-rose disabled:opacity-50"
        >
          {signingOut ? 'Signing out…' : 'Sign out'}
        </button>
      </div>
    </div>
  )
}
