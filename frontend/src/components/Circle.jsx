import { useCallback, useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Logo from './Logo'
import ErrorBanner from './ErrorBanner'
import {
  acceptFollow,
  getFollowers,
  getFollowing,
  getInbox,
  getOutgoingRequests,
  patchNickname,
  refuseFollow,
  removeFollow,
  searchNicknames,
  sendFollow,
} from '../api/follows'
import { errorMessage } from '../api/client'
import { useAuth } from '../context/authContext'

const BTN =
  'rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium px-4 py-2 transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50 disabled:opacity-50'
const INPUT =
  'w-full rounded-xl border-2 border-dusty-mauve/50 bg-night-bordeaux/80 text-peach-fuzz px-4 py-3 focus:border-powder-blush outline-none'

const linkLabel = (type) => (type === 'partner' ? 'girlfriend / partner' : 'friend')

function Section({ title, children, empty }) {
  return (
    <section className="mb-10">
      <h2 className="text-xl font-bold mb-3">{title}</h2>
      {empty && <p className="text-powder-blush/80 text-sm">{empty}</p>}
      {children}
    </section>
  )
}

function Row({ children }) {
  return (
    <li className="flex items-center justify-between gap-3 rounded-xl border border-powder-blush/30 p-3">
      {children}
    </li>
  )
}

export default function Circle() {
  const navigate = useNavigate()
  const { user, setUser } = useAuth()
  const [nickDraft, setNickDraft] = useState(user?.nickname || '')
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState([])
  const [linkType, setLinkType] = useState('friend')
  const [inbox, setInbox] = useState([])
  const [following, setFollowing] = useState([])
  const [requests, setRequests] = useState([])
  const [followers, setFollowers] = useState([])
  const [error, setError] = useState(null)
  const [info, setInfo] = useState(null)
  const [busy, setBusy] = useState(false)

  const nickname = user?.nickname || ''

  const refresh = useCallback(async () => {
    const [box, list, outgoing, mine] = await Promise.all([
      getInbox(),
      getFollowing(),
      getOutgoingRequests(),
      getFollowers(),
    ])
    setInbox(box)
    setFollowing(list)
    setRequests(outgoing)
    setFollowers(mine)
  }, [])

  useEffect(() => {
    refresh().catch((err) => setError(errorMessage(err, 'Could not load your circle.')))
  }, [refresh])

  useEffect(() => {
    setNickDraft(user?.nickname || '')
  }, [user?.nickname])

  /** Run a mutation, surface whatever goes wrong, and reload the lists. */
  const run = async (action, successMessage) => {
    setBusy(true)
    setError(null)
    setInfo(null)
    try {
      await action()
      await refresh()
      if (successMessage) setInfo(successMessage)
    } catch (err) {
      setError(errorMessage(err, 'That did not work. Please try again.'))
    } finally {
      setBusy(false)
    }
  }

  const saveNick = (e) => {
    e.preventDefault()
    run(async () => {
      const data = await patchNickname(nickDraft)
      setUser((prev) => (prev ? { ...prev, nickname: data.nickname } : prev))
    }, 'Nickname saved. Others find you by this name, not your email.')
  }

  const doSearch = async (e) => {
    e.preventDefault()
    setError(null)
    setInfo(null)
    try {
      const data = await searchNicknames(query)
      setHits(data)
      if (data.length === 0) setInfo('No matches.')
    } catch (err) {
      setError(errorMessage(err, 'Search failed.'))
    }
  }

  const requestFollow = (nick) =>
    run(
      () => sendFollow({ nickname: nick, link_type: linkType }),
      `Request sent to ${nick} as ${linkLabel(linkType)}. They will see your phase once they accept.`,
    )

  return (
    <div className="min-h-screen px-6 py-10 bg-night-bordeaux text-peach-fuzz">
      <div className="max-w-lg mx-auto">
        <div className="flex items-center justify-between mb-6">
          <button type="button" onClick={() => navigate('/app/account')} className={BTN}>
            ← Account
          </button>
          <Logo className="w-12 h-12 text-powder-blush" />
        </div>
        <h1 className="text-3xl font-bold mb-2">Circle</h1>
        <p className="text-powder-blush/90 text-sm mb-8">
          They will see your current cycle <strong className="text-peach-fuzz">phase</strong>, not
          your flow or dates.
        </p>

        <ErrorBanner message={error} onDismiss={() => setError(null)} className="mb-4" />
        {info && (
          <p className="text-powder-blush text-sm mb-4" role="status">
            {info}
          </p>
        )}

        <form onSubmit={saveNick} className="mb-10 space-y-3">
          <label htmlFor="nick" className="block font-semibold">
            Your nickname
          </label>
          <input
            id="nick"
            value={nickDraft}
            onChange={(e) => setNickDraft(e.target.value)}
            className={INPUT}
            placeholder="e.g. luna_28"
            autoComplete="off"
          />
          <button type="submit" disabled={busy} className={`${BTN} w-full py-3 font-semibold`}>
            {nickname ? 'Update nickname' : 'Save nickname'}
          </button>
        </form>

        <form onSubmit={doSearch} className="mb-4 space-y-3">
          <label htmlFor="find" className="block font-semibold">
            Find someone
          </label>
          <input
            id="find"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className={INPUT}
            placeholder="Search nickname"
            autoComplete="off"
          />
          <div className="flex gap-2" role="group" aria-label="Follow as">
            <button
              type="button"
              onClick={() => setLinkType('friend')}
              aria-pressed={linkType === 'friend'}
              className={`${BTN} flex-1 ${linkType === 'friend' ? 'ring-2 ring-powder-blush' : ''}`}
            >
              Friend
            </button>
            <button
              type="button"
              onClick={() => setLinkType('partner')}
              aria-pressed={linkType === 'partner'}
              className={`${BTN} flex-1 ${linkType === 'partner' ? 'ring-2 ring-powder-blush' : ''}`}
            >
              Girlfriend / partner
            </button>
          </div>
          <button
            type="submit"
            className={`${BTN} w-full py-3 font-semibold bg-dusty-mauve text-white`}
          >
            Search
          </button>
        </form>

        {hits.length > 0 && (
          <ul className="space-y-2 mb-10">
            {hits.map((h) => (
              <Row key={h.nickname}>
                <span className="font-medium truncate">{h.nickname}</span>
                <button
                  type="button"
                  className={BTN}
                  disabled={busy}
                  onClick={() => requestFollow(h.nickname)}
                >
                  Send request
                </button>
              </Row>
            ))}
          </ul>
        )}

        <Section title="Inbox" empty={inbox.length === 0 ? 'No pending requests.' : null}>
          <ul className="space-y-2">
            {inbox.map((row) => (
              <li key={row.id} className="rounded-xl border border-powder-blush/30 p-3">
                <p className="mb-2">
                  <strong>{row.nickname || 'Someone'}</strong> wants to follow as{' '}
                  {linkLabel(row.link_type)}
                </p>
                <div className="flex gap-2">
                  <button
                    type="button"
                    className={`${BTN} bg-dusty-mauve text-white`}
                    disabled={busy}
                    onClick={() => run(() => acceptFollow(row.id), `${row.nickname} can now see your phase.`)}
                  >
                    Accept
                  </button>
                  <button
                    type="button"
                    className={BTN}
                    disabled={busy}
                    onClick={() => run(() => refuseFollow(row.id), 'Request declined.')}
                  >
                    Refuse
                  </button>
                </div>
              </li>
            ))}
          </ul>
        </Section>

        {/* Until they accept, cancelling and asking again is the only move. */}
        <Section
          title="Requests you sent"
          empty={requests.length === 0 ? 'No requests waiting for an answer.' : null}
        >
          <ul className="space-y-2">
            {requests.map((row) => (
              <Row key={row.id}>
                <span className="min-w-0">
                  <span className="block font-medium truncate">{row.nickname || 'Unknown'}</span>
                  <span className="text-powder-blush/80 text-sm">
                    Pending · {linkLabel(row.link_type)}
                  </span>
                </span>
                <button
                  type="button"
                  className={BTN}
                  disabled={busy}
                  onClick={() => run(() => removeFollow(row.id), 'Request cancelled.')}
                >
                  Cancel
                </button>
              </Row>
            ))}
          </ul>
        </Section>

        <Section
          title="Following"
          empty={following.length === 0 ? 'You are not following anyone yet.' : null}
        >
          <ul className="space-y-2">
            {following.map((row) => (
              <Row key={row.id}>
                <Link
                  to={`/circle/${row.id}`}
                  className="min-w-0 font-medium underline decoration-powder-blush truncate"
                >
                  {row.nickname || 'Unknown'} · {linkLabel(row.link_type)}
                </Link>
                <button
                  type="button"
                  className={BTN}
                  disabled={busy}
                  onClick={() => run(() => removeFollow(row.id), 'Unfollowed.')}
                >
                  Unfollow
                </button>
              </Row>
            ))}
          </ul>
        </Section>

        {/* Access already granted has to be revocable, or "consent-based" is
            only true at the moment you accept. */}
        <Section
          title="Who can see your phase"
          empty={followers.length === 0 ? 'Nobody is following you yet.' : null}
        >
          <ul className="space-y-2">
            {followers.map((row) => (
              <Row key={row.id}>
                <span className="min-w-0">
                  <span className="block font-medium truncate">{row.nickname || 'Unknown'}</span>
                  <span className="text-powder-blush/80 text-sm">{linkLabel(row.link_type)}</span>
                </span>
                <button
                  type="button"
                  className={BTN}
                  disabled={busy}
                  onClick={() =>
                    run(() => removeFollow(row.id), 'They can no longer see your phase.')
                  }
                >
                  Remove
                </button>
              </Row>
            ))}
          </ul>
        </Section>
      </div>
    </div>
  )
}
