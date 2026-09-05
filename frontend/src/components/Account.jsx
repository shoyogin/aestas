import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import Logo from './Logo'
import Avatar from './Avatar'
import ErrorBanner from './ErrorBanner'
import { errorMessage } from '../api/client'
import { logout } from '../api/auth'
import { patchNickname } from '../api/follows'
import { getCycleContext } from '../api/cycle'
import { AVATAR_ACCEPT, avatarFileError, deleteAvatar, uploadAvatar } from '../api/avatar'
import { useAuth } from '../context/authContext'

const BTN =
  'rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium px-4 py-3 transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50 disabled:opacity-50'
const INPUT =
  'w-full rounded-xl border-2 border-dusty-mauve/50 bg-night-bordeaux/80 text-peach-fuzz px-4 py-3 focus:border-powder-blush outline-none'

export default function Account() {
  const { user, setUser } = useAuth()
  const [nickDraft, setNickDraft] = useState(user?.nickname || '')
  const [cycleLength, setCycleLength] = useState(null)
  const [error, setError] = useState(null)
  const [info, setInfo] = useState(null)
  const [saving, setSaving] = useState(false)
  const [signingOut, setSigningOut] = useState(false)
  const [pictureBusy, setPictureBusy] = useState(false)
  const fileInput = useRef(null)

  const email = user?.email || ''
  const nickname = user?.nickname || ''
  const avatarVersion = user?.avatar_updated_at || null

  useEffect(() => {
    setNickDraft(user?.nickname || '')
  }, [user?.nickname])

  useEffect(() => {
    let cancelled = false
    getCycleContext()
      .then((cycle) => !cancelled && setCycleLength(cycle.cycle_length ?? null))
      .catch((err) => !cancelled && setError(errorMessage(err, 'Could not load your cycle.')))
    return () => {
      cancelled = true
    }
  }, [])

  /** Run a picture change and fold the new version back into the auth user,
   *  which is what every avatar on screen reads its cache key from. */
  const runPictureChange = async (action, successMessage) => {
    setError(null)
    setInfo(null)
    setPictureBusy(true)
    try {
      const data = await action()
      setUser((prev) =>
        prev ? { ...prev, avatar_updated_at: data?.avatar_updated_at ?? null } : prev,
      )
      setInfo(successMessage)
    } catch (err) {
      setError(errorMessage(err, 'Could not update your picture.'))
    } finally {
      setPictureBusy(false)
    }
  }

  const choosePicture = (e) => {
    const file = e.target.files?.[0]
    // Reset first: picking the same file twice has to fire onChange again.
    e.target.value = ''
    if (!file) return
    const problem = avatarFileError(file)
    if (problem) {
      setInfo(null)
      setError(problem)
      return
    }
    runPictureChange(() => uploadAvatar(file), 'Profile picture updated.')
  }

  const removePicture = () =>
    runPictureChange(deleteAvatar, 'Profile picture removed.')

  const saveNick = async (e) => {
    e.preventDefault()
    setError(null)
    setInfo(null)
    setSaving(true)
    try {
      const data = await patchNickname(nickDraft)
      setUser((prev) => (prev ? { ...prev, nickname: data.nickname } : prev))
      setInfo('Nickname saved. Others find you by this name, not your email.')
    } catch (err) {
      setError(errorMessage(err, 'Could not save nickname.'))
    } finally {
      setSaving(false)
    }
  }

  const signOut = async () => {
    setSigningOut(true)
    setError(null)
    try {
      await logout()
      window.location.assign('/')
    } catch (err) {
      setSigningOut(false)
      setError(errorMessage(err, 'Could not sign out.'))
    }
  }

  return (
    <div className="flex flex-col items-center px-6 py-8">
      <h1 className="text-2xl font-bold text-peach-fuzz mb-2">Account</h1>
      <Logo className="w-16 h-16 text-powder-blush mb-6" />
      <div className="w-full max-w-md space-y-8">
        <ErrorBanner message={error} onDismiss={() => setError(null)} />
        {info && (
          <p className="text-powder-blush text-sm text-center" role="status">
            {info}
          </p>
        )}

        <div className="rounded-2xl border border-powder-blush/30 bg-dusty-mauve/15 px-4 py-4">
          <div className="flex items-center gap-4">
            <Avatar
              self
              version={avatarVersion}
              nickname={nickname}
              email={email}
              className="w-16 h-16 text-lg"
            />
            <div className="min-w-0">
              <p className="font-semibold text-peach-fuzz truncate">
                {nickname || 'No nickname yet'}
              </p>
              <p className="text-powder-blush text-sm truncate">{email || '—'}</p>
            </div>
          </div>

          {/* The input itself is unstyled everywhere, so it stays hidden and
              the button drives it. */}
          <input
            ref={fileInput}
            id="account-picture"
            type="file"
            accept={AVATAR_ACCEPT}
            onChange={choosePicture}
            className="sr-only"
          />
          <div className="flex gap-2 mt-4">
            <button
              type="button"
              className={`${BTN} flex-1 py-2`}
              disabled={pictureBusy}
              onClick={() => fileInput.current?.click()}
            >
              {pictureBusy
                ? 'Working…'
                : avatarVersion
                  ? 'Change picture'
                  : 'Add a picture'}
            </button>
            {avatarVersion && (
              <button
                type="button"
                className={`${BTN} py-2`}
                disabled={pictureBusy}
                onClick={removePicture}
              >
                Remove
              </button>
            )}
          </div>
          <p className="text-powder-blush/80 text-xs mt-2">
            JPEG, PNG, WebP, or GIF, up to 5 MB. Only your circle sees it.
          </p>
        </div>

        <form onSubmit={saveNick} className="space-y-3">
          <label htmlFor="account-nick" className="block font-semibold">
            Nickname
          </label>
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
          <button type="submit" disabled={saving} className={`${BTN} w-full font-semibold`}>
            {nickname ? 'Update nickname' : 'Save nickname'}
          </button>
        </form>

        <div>
          <p className="font-semibold mb-1">Typical cycle length</p>
          <p className="text-powder-blush">{cycleLength ? `${cycleLength} days` : 'Not set'}</p>
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
