import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Logo from './Logo'
import ErrorBanner from './ErrorBanner'
import { getFollowing } from '../api/follows'
import { errorMessage } from '../api/client'

function initials(name) {
  const s = (name || '?').replace(/^_/, '')
  return s.slice(0, 2).toUpperCase()
}

export default function Friends() {
  const [friends, setFriends] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    getFollowing()
      .then((list) => {
        if (cancelled) return
        setFriends((list || []).filter((f) => f.link_type === 'friend'))
      })
      .catch((err) => {
        if (!cancelled) setError(errorMessage(err, 'Could not load your friends.'))
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <div className="flex flex-col items-center px-6 py-8">
      <h1 className="text-2xl font-bold text-peach-fuzz mb-2">Friends</h1>
      <Logo className="w-16 h-16 text-powder-blush mb-2" />
      <Link
        to="/circle"
        className="mb-6 text-powder-blush underline decoration-powder-blush/50 hover:text-peach-fuzz text-sm"
      >
        Manage circle
      </Link>
      <div className="w-full max-w-3xl">
        <ErrorBanner message={error} onDismiss={() => setError(null)} className="mb-4" />
        <p className="text-powder-blush/80 text-sm text-center mb-4">
          Friends you follow — tap one for advice for their phase
        </p>
        {loading && <p className="text-powder-blush/80 text-center text-sm">Loading…</p>}
        {!loading && friends.length === 0 && (
          <p className="text-powder-blush/80 text-center text-sm">
            No friends yet. Use Manage circle to send a friend request.
          </p>
        )}
        <ul className="space-y-3">
          {friends.map((f) => (
            <li key={f.id}>
              {/* The shared view already exists; this used to be a dead
                  "coming soon" button. */}
              <Link
                to={`/circle/${f.id}`}
                className="w-full flex items-center gap-4 rounded-2xl border border-powder-blush/30 bg-dusty-mauve/15 px-4 py-3 text-left hover:bg-dusty-mauve/25 transition-colors"
              >
                <span className="flex-shrink-0 w-12 h-12 rounded-full bg-burnt-rose text-peach-fuzz font-semibold flex items-center justify-center">
                  {initials(f.nickname)}
                </span>
                <span className="flex-1 min-w-0">
                  <span className="block font-semibold text-peach-fuzz truncate">
                    {f.nickname || 'Unknown'}
                  </span>
                  <span className="text-powder-blush text-sm">
                    {f.phase_label ? `Day ${f.cycle_day} · ${f.phase_label}` : 'No phase yet'}
                  </span>
                </span>
                <span className="text-powder-blush/60" aria-hidden>
                  ›
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
