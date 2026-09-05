# 9. Profile pictures

Each account can carry one picture. It is optional; anyone without one shows the
first two letters of their nickname on a burnt-rose circle, exactly as before.

Set it on **Account** (`/app/account`): **Add a picture** opens the file picker,
**Remove** takes it away again.

## Nothing is served back as it arrived

An upload is decoded, centre-cropped to a square, resized to at most **512px**,
and re-encoded as **WebP** (`backend/app/avatars.py`). The bytes the user sent
are then thrown away. That single step does most of the work here:

- **It settles what the file is.** A browser's `Content-Type` is a claim, not a
  fact. `evil.exe` renamed to `me.png` fails the decode, and the upload is
  refused with a 400.
- **It rules out SVG.** An SVG is a document that can run script, so serving one
  back from our own origin would be stored XSS. Only JPEG, PNG, WebP, GIF, BMP,
  and TIFF are decoded at all — and whatever comes in, WebP goes out.
- **It drops EXIF.** Phone photos routinely carry GPS coordinates in EXIF, and
  a cycle-tracking app is the last place they should leak from. The one thing
  read out of EXIF first is the orientation flag, applied to the pixels so the
  avatar is not sideways once the metadata is gone.
- **It bounds the cost.** A 1200×700 JPEG became 544 bytes in testing. Uploads
  over 5 MB are refused with a 413 (`AVATAR_MAX_UPLOAD_BYTES`), and a source
  over 40 megapixels is rejected from its header, before a decompression bomb
  can allocate anything.

Small pictures are never upscaled: a 64px upload stays 64px rather than being
blurred up to 512.

## Where the bytes live

In Postgres, in a `profile_pictures` table keyed by `user_id` — one picture per
account, and the `ON DELETE CASCADE` takes it with the account.

It is a separate table rather than a column on `users` because every query that
loads a user would otherwise drag the image along, and almost none of them want
it. The `data` column is deferred on top of that, so even a query against
`profile_pictures` only pays for the bytes when something reads them; an
`If-None-Match` revalidation that ends in 304 never reads the image at all.

Postgres holds them because it is the only store in this stack that is already
persistent and already backed up. A file under the backend's working directory
would not survive the next container rebuild.

## Who can see whose

The rule matches what the Circle screen already shows you by name: **you can see
someone's picture exactly when a follow edge exists between you — pending or
accepted, in either direction.**

| | Sees your picture |
|--|--|
| You | Yes |
| Someone whose request you have not answered | Yes — the inbox shows who is asking |
| Someone you follow, or who follows you | Yes |
| A `refused`, `withdrawn`, or `revoked` edge | No |
| A stranger, or a name from search | No |

Search results are deliberately outside that set. Nicknames are searchable so
people can find each other; faces are not, or a stranger could walk the nickname
space collecting them.

Someone you may not see is reported as **404**, the same answer as a nickname
that does not exist — so the endpoint cannot be used to enumerate accounts or to
tell which of them have uploaded a picture.

## API (session cookie)

| Method | Path | Notes |
|--|--|--|
| `PUT` | `/users/me/avatar` | `multipart/form-data`, field `file`. 400 if undecodable, 413 if over the limit. |
| `DELETE` | `/users/me/avatar` | Idempotent — removing nothing is still a 200. |
| `GET` | `/users/me/avatar` | My own picture. |
| `GET` | `/users/{nickname}/avatar` | Someone else's, subject to the rule above. |

Every response that mentions a person — `/auth/me`, the four `/follows` lists,
`/follows/{id}/cycle` — carries an **`avatar_updated_at`**. `null` means no
picture, so a user who has never uploaded one costs no image request at all.
When set, it doubles as the cache key: the frontend appends it as `?v=`, so a
picture the user just changed replaces the one their browser already has.

Served images are `private, max-age=0, must-revalidate` with an `ETag`, plus
`X-Content-Type-Options: nosniff`. `private` because this is one signed-in
user's view of another's picture and no shared cache should hold it; the ETag
makes the revalidation cheap.

Uploads have their own rate-limit bucket (`RATE_LIMIT_AVATAR_WRITE`, default
10 per 5 minutes) because each one costs a decode and a re-encode.

## Why the `<img>` tag works

The pictures are fetched by ordinary `<img src>` rather than through the axios
client, which keeps browser caching. The session cookie rides along because the
frontend and backend are the **same site** whatever ports they sit on — the
same assumption `COOKIE_SAMESITE=lax` already makes for the rest of the app. A
genuinely cross-site deployment would need `COOKIE_SAMESITE=none`, which is
already true of every other authenticated request here.
