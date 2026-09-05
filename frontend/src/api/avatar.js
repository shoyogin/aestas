import { api } from './client'

/** Kept in step with `avatar_max_upload_bytes` in the backend settings. */
export const AVATAR_MAX_BYTES = 5 * 1024 * 1024

/** What the file picker offers, and what the server will actually decode. */
export const AVATAR_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
export const AVATAR_ACCEPT = AVATAR_TYPES.join(',')

/**
 * Reject what we can reject without a round trip, and say why in words worth
 * reading. The server checks all of this again by actually decoding the file —
 * this only saves the user a five-megabyte upload that was never going to work.
 */
export function avatarFileError(file) {
  if (!file) return 'Choose an image first.'
  if (file.size === 0) return 'That file is empty.'
  if (file.size > AVATAR_MAX_BYTES) {
    const mb = (AVATAR_MAX_BYTES / (1024 * 1024)).toFixed(0)
    return `That image is too big. The limit is ${mb} MB.`
  }
  // An empty type means the browser could not tell; let the server decide.
  if (file.type && !AVATAR_TYPES.includes(file.type)) {
    return 'That has to be a JPEG, PNG, WebP, or GIF.'
  }
  return null
}

/**
 * The URL an <img> should load for someone's avatar, or null when they have
 * none — `version` is the `avatar_updated_at` the API sent alongside them.
 *
 * The version rides along as a query parameter so a picture the user just
 * changed replaces the one their browser cached, rather than waiting out the
 * revalidation. The <img> carries the session cookie by itself: frontend and
 * backend are the same site, whatever ports they sit on.
 */
export function avatarUrl(nickname, version) {
  if (!version || !nickname) return null
  return `${api.defaults.baseURL}/users/${encodeURIComponent(nickname)}/avatar?v=${encodeURIComponent(version)}`
}

/** My own picture, which needs no nickname — I may always see it. */
export function myAvatarUrl(version) {
  if (!version) return null
  return `${api.defaults.baseURL}/users/me/avatar?v=${encodeURIComponent(version)}`
}

export async function uploadAvatar(file) {
  const form = new FormData()
  form.append('file', file)
  // The instance defaults to application/json, which axios would take as a cue
  // to JSON-stringify the form. Naming multipart here stops that; the browser
  // then replaces this header with the real one, boundary included.
  const { data } = await api.put('/users/me/avatar', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
  return data
}

export async function deleteAvatar() {
  const { data } = await api.delete('/users/me/avatar')
  return data
}
