import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import Logo from './Logo'
import {
  acceptFollow,
  getFollowing,
  getInbox,
  patchNickname,
  refuseFollow,
  revokeFollow,
  searchNicknames,
  sendFollow,
} from '../api/follows'
import { api } from '../api/client'

const BTN =
  'rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium px-4 py-2 transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50'
const INPUT =
  'w-full rounded-xl border-2 border-dusty-mauve/50 bg-night-bordeaux/80 text-peach-fuzz px-4 py-3 focus:border-powder-blush outline-none'

export default function Circle() {
  const navigate = useNavigate()
  const [nickname, setNickname] = useState('')
  const [nickDraft, setNickDraft] = useState('')
  const [query, setQuery] = useState('')
  const [hits, setHits] = useState([])
  const [linkType, setLinkType] = useState('friend')
  const [inbox, setInbox] = useState([])
  const [following, setFollowing] = useState([])
  const [error, setError] = useState(null)
  const [info, setInfo] = useState(null)

  const refresh = async () => {
    const [me, box, list] = await Promise.all([
      api.get('/auth/me'),
      getInbox(),
      getFollowing(),
    ])
    setNickname(me.data.nickname || '')
    setNickDraft(me.data.nickname || '')
    setInbox(box)
    setFollowing(list)
  }

  useEffect(() => {
    refresh().catch(() => setError('Could not load circle.'))
  }, [])

  const saveNick = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const data = await patchNickname(nickDraft)
      setNickname(data.nickname)
      setInfo('Nickname saved. Others can find you with this name only — not your email.')
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not save nickname.')
    }
  }

  const doSearch = async (e) => {
    e.preventDefault()
    setError(null)
    try {
      const data = await searchNicknames(query)
      setHits(data)
      if (data.length === 0) setInfo('No matches.')
      else setInfo(null)
    } catch (err) {
      setError(err.response?.data?.detail || 'Search failed.')
    }
  }

  const requestFollow = async (nick) => {
    setError(null)
    setInfo(null)
    try {
      await sendFollow({ nickname: nick, link_type: linkType })
      setInfo(`Request sent to ${nick} as ${linkType === 'partner' ? 'girlfriend / partner' : 'friend'}.`)
      await refresh()
    } catch (err) {
      setError(err.response?.data?.detail || 'Could not send request.')
    }
  }

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
          They will see your current cycle <strong className="text-peach-fuzz">phase</strong>, not your flow or dates.
        </p>

        {error && (
          <div className="rounded-xl bg-burnt-rose/30 border border-burnt-rose p-3 text-sm mb-4" role="alert">
            {error}
          </div>
        )}
        {info && (
          <p className="text-powder-blush text-sm mb-4" role="status">{info}</p>
        )}

        <form onSubmit={saveNick} className="mb-10 space-y-3">
          <label htmlFor="nick" className="block font-semibold">Your nickname</label>
          <input
            id="nick"
            value={nickDraft}
            onChange={(e) => setNickDraft(e.target.value)}
            className={INPUT}
            placeholder="e.g. luna_28"
            autoComplete="off"
          />
          <button type="submit" className={`${BTN} w-full py-3 font-semibold`}>
            {nickname ? 'Update nickname' : 'Save nickname'}
          </button>
        </form>

        <form onSubmit={doSearch} className="mb-4 space-y-3">
          <label htmlFor="find" className="block font-semibold">Find someone</label>
          <input
            id="find"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className={INPUT}
            placeholder="Search nickname"
            autoComplete="off"
          />
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setLinkType('friend')}
              className={`${BTN} flex-1 ${linkType === 'friend' ? 'ring-2 ring-powder-blush' : ''}`}
            >
              Friend
            </button>
            <button
              type="button"
              onClick={() => setLinkType('partner')}
              className={`${BTN} flex-1 ${linkType === 'partner' ? 'ring-2 ring-powder-blush' : ''}`}
            >
              Girlfriend / partner
            </button>
          </div>
          <button type="submit" className={`${BTN} w-full py-3 font-semibold bg-dusty-mauve text-white`}>
            Search
          </button>
        </form>

        <ul className="space-y-2 mb-10">
          {hits.map((h) => (
            <li
              key={h.nickname}
              className="flex items-center justify-between rounded-xl border border-powder-blush/30 p-3"
            >
              <span className="font-medium">{h.nickname}</span>
              <button type="button" className={BTN} onClick={() => requestFollow(h.nickname)}>
                Send request
              </button>
            </li>
          ))}
        </ul>

        <h2 className="text-xl font-bold mb-3">Inbox</h2>
        {inbox.length === 0 && (
          <p className="text-powder-blush/80 text-sm mb-8">No pending requests.</p>
        )}
        <ul className="space-y-2 mb-10">
          {inbox.map((row) => (
            <li key={row.id} className="rounded-xl border border-powder-blush/30 p-3">
              <p className="mb-2">
                <strong>{row.nickname || 'Someone'}</strong>
                {' '}wants to follow as{' '}
                {row.link_type === 'partner' ? 'girlfriend / partner' : 'friend'}
              </p>
              <div className="flex gap-2">
                <button
                  type="button"
                  className={`${BTN} bg-dusty-mauve text-white`}
                  onClick={async () => {
                    try {
                      await acceptFollow(row.id)
                      await refresh()
                    } catch (err) {
                      setError(err.response?.data?.detail || 'Could not accept.')
                    }
                  }}
                >
                  Accept
                </button>
                <button
                  type="button"
                  className={BTN}
                  onClick={async () => {
                    await refuseFollow(row.id)
                    await refresh()
                  }}
                >
                  Refuse
                </button>
              </div>
            </li>
          ))}
        </ul>

        <h2 className="text-xl font-bold mb-3">Following</h2>
        {following.length === 0 && (
          <p className="text-powder-blush/80 text-sm">You are not following anyone yet.</p>
        )}
        <ul className="space-y-2">
          {following.map((row) => (
            <li
              key={row.id}
              className="flex items-center justify-between rounded-xl border border-powder-blush/30 p-3"
            >
              <Link to={`/circle/${row.id}`} className="font-medium underline decoration-powder-blush">
                {row.nickname || 'Unknown'} · {row.link_type === 'partner' ? 'partner' : 'friend'}
              </Link>
              <button
                type="button"
                className={BTN}
                onClick={async () => {
                  await revokeFollow(row.id)
                  await refresh()
                }}
              >
                Unfollow
              </button>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
