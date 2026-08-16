import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import Logo from './Logo'
import CalendarArc from './CalendarArc'
import { getFollowing } from '../api/follows'

function initials(name) {
  const s = (name || '?').replace(/^_/, '')
  return s.slice(0, 2).toUpperCase()
}

export default function Friends() {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const [selectedDate, setSelectedDate] = useState(() => new Date(today))
  const [friends, setFriends] = useState([])
  const [hint, setHint] = useState(null)

  useEffect(() => {
    getFollowing()
      .then((list) => setFriends((list || []).filter((f) => f.link_type === 'friend')))
      .catch(() => setFriends([]))
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
        <CalendarArc
          selectedDate={selectedDate}
          onSelectDate={setSelectedDate}
          logs={{}}
          readOnly
        />
        <p className="text-powder-blush/80 text-sm text-center mb-4">
          Friends you follow — tap a profile for advice later
        </p>
        {friends.length === 0 && (
          <p className="text-powder-blush/80 text-center text-sm">
            No friends yet. Use Manage circle to send a friend request.
          </p>
        )}
        <ul className="space-y-3">
          {friends.map((f) => (
            <li key={f.id}>
              <button
                type="button"
                onClick={() => setHint('Coming soon: static advice for this phase.')}
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
                    {f.phase_label
                      ? `Day ${f.cycle_day} · ${f.phase_label}`
                      : 'No phase yet'}
                  </span>
                </span>
              </button>
            </li>
          ))}
        </ul>
        {hint && (
          <p className="text-powder-blush/80 text-sm text-center mt-4" role="status">
            {hint}
          </p>
        )}
      </div>
    </div>
  )
}
