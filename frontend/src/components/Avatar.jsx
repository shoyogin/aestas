import { useEffect, useState } from 'react'
import { avatarUrl, myAvatarUrl } from '../api/avatar'

/** Two letters to stand in for a face. Leading underscores read as noise. */
function initials(name, email) {
  const s = (name || email || '?').replace(/^_+/, '') || '?'
  return s.slice(0, 2).toUpperCase()
}

/**
 * Someone's profile picture, falling back to their initials.
 *
 * `version` is the `avatar_updated_at` the API sent with them; without one
 * there is no picture to fetch and the initials are the answer, so a user who
 * has never uploaded anything costs no request at all. `self` asks for the
 * signed-in user's own picture, which needs no nickname.
 */
export default function Avatar({
  nickname,
  email,
  version,
  self = false,
  className = 'w-12 h-12',
  alt,
}) {
  const src = self ? myAvatarUrl(version) : avatarUrl(nickname, version)
  // A picture can vanish between the list load and the image request (removed,
  // or a follow ended in between). Falling back beats a broken-image icon.
  const [failed, setFailed] = useState(false)
  useEffect(() => setFailed(false), [src])

  const shape = `flex-shrink-0 rounded-full object-cover bg-burnt-rose ${className}`

  if (!src || failed) {
    return (
      <span
        className={`${shape} text-peach-fuzz font-semibold flex items-center justify-center`}
        aria-hidden={alt ? undefined : true}
        role={alt ? 'img' : undefined}
        aria-label={alt}
      >
        {initials(nickname, email)}
      </span>
    )
  }

  return (
    <img
      src={src}
      alt={alt ?? ''}
      className={shape}
      loading="lazy"
      decoding="async"
      onError={() => setFailed(true)}
    />
  )
}
