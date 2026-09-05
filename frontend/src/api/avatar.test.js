import { describe, expect, it } from 'vitest'
import { AVATAR_MAX_BYTES, avatarFileError, avatarUrl, myAvatarUrl } from './avatar'

/** A stand-in for the File the picker hands us: only size and type are read. */
const file = (size, type) => ({ size, type })

describe('avatarFileError', () => {
  it('accepts the formats the server can decode', () => {
    for (const type of ['image/jpeg', 'image/png', 'image/webp', 'image/gif']) {
      expect(avatarFileError(file(1024, type))).toBeNull()
    }
  })

  it('asks for a file when there is none', () => {
    expect(avatarFileError(null)).toMatch(/choose an image/i)
  })

  it('rejects an empty file', () => {
    expect(avatarFileError(file(0, 'image/png'))).toMatch(/empty/i)
  })

  it('rejects a file over the limit, and names the limit', () => {
    expect(avatarFileError(file(AVATAR_MAX_BYTES + 1, 'image/png'))).toMatch(/5 MB/)
    expect(avatarFileError(file(AVATAR_MAX_BYTES, 'image/png'))).toBeNull()
  })

  it('rejects formats the server will not decode', () => {
    expect(avatarFileError(file(1024, 'image/svg+xml'))).toMatch(/JPEG/)
    expect(avatarFileError(file(1024, 'application/pdf'))).toMatch(/JPEG/)
  })

  it('lets a file the browser could not identify through to the server', () => {
    // The server decides by decoding; guessing here would only reject valid images.
    expect(avatarFileError(file(1024, ''))).toBeNull()
  })
})

describe('avatarUrl', () => {
  it('is null without a version, because that means there is no picture', () => {
    expect(avatarUrl('luna', null)).toBeNull()
    expect(myAvatarUrl(null)).toBeNull()
  })

  it('carries the version, so a changed picture beats the cached one', () => {
    expect(avatarUrl('luna', '2026-09-05T10:00:00+00:00')).toContain(
      '/users/luna/avatar?v=2026-09-05T10%3A00%3A00%2B00%3A00',
    )
  })

  it('escapes the nickname rather than pasting it into a path', () => {
    expect(avatarUrl('a/b', 'v1')).toContain('/users/a%2Fb/avatar')
  })

  it('asks for my own picture by identity, not by name', () => {
    expect(myAvatarUrl('v1')).toContain('/users/me/avatar?v=v1')
  })
})
