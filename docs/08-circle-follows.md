# 8. Circle: friends and partner follows

Aestas lets you **link profiles by nickname**, with **consent**. There is no gender field. The **link type** is what matters:

- **Friend** — follow someone’s cycle at a respectful distance.
- **Partner** — see fuller “how to support them this week” guidance.

The person whose cycle would be shared **accepts or refuses**. They can revoke later.

## What is never shared

Email, Google id, period **flow**, and exact **start/end dates**. Followers only get a computed **phase** and **cycle day** plus filtered tips.

| | Friend | Partner |
|--|--------|---------|
| Phase + cycle day | Yes | Yes |
| Food / activity / mood | Lite | Full |
| Sexual drive panel | No | Yes |
| “How to treat them” line | No | Yes |

## Nickname

`PATCH /users/me` with `{ "nickname": "luna_28" }`. Stored **lowercase**, unique, 3–24 characters (`a-z`, `0-9`, `_`). Uniqueness is case-insensitive, enforced by a `LOWER(nickname)` index rather than by the availability check alone, so two people picking the same name at the same moment get a clean 409 instead of a 500.

Search never uses email: `GET /users/search?nickname=lu`. It matches a **prefix**, and `%` and `_` in the query are escaped — otherwise searching for `%` would list every user in the database.

Set your nickname on **Account** (`/app/account`) or **Circle** (`/circle`) before others can find you.

## Requests

Follows work the way Instagram’s do. A request sits **pending** until the target
acts on it, and until then the only thing the requester can do is **withdraw**
it and send it again.

1. Search a nickname, pick **Friend** or **Partner**, send request.
2. They see it in **Inbox**. Pending requests do **not** expire.
3. **Accept** or **Refuse**. Refuse does not explain why; the requester just is not connected.
4. At most **one accepted partner** inbound at a time. Many friends are allowed.
5. The requester can **unfollow**; the target can **remove a follower**. Either
   way access ends immediately.

`refused`, `withdrawn`, and `revoked` are all re-requestable, and the same row is
reused (the table is unique on requester + target).

> Earlier versions hid pending requests from the inbox after 14 days but still
> rejected new ones with a 409. A request could therefore end up permanently
> stuck: invisible to the target and unrepeatable by the requester. There is no
> expiry now — withdrawing is the way out.

## API (session cookie)

- `POST /follows` `{ nickname, link_type }` — send or re-send a request
- `GET /follows/inbox` — requests waiting on me
- `GET /follows/requests` — requests **I** sent that are still pending (cancellable)
- `GET /follows` — people I follow, accepted, with their phase
- `GET /follows/followers` — people who can see **my** phase
- `POST /follows/{id}/accept` \| `refuse`
- `DELETE /follows/{id}` — withdraw my request, unfollow, or remove a follower
- `GET /follows/{id}/cycle` — filtered view for the **follower** only

Phase is computed on the **server** (`backend/app/cycle_phase.py`) so raw dates never leave the owner’s account, in the **owner’s own timezone** so their "today" matches what they see in the app.

`GET /follows/followers` exists so consent stays revocable. Without it you could
accept a follow and then have no way to see it or take it back.

## UI

Bottom tabs on `/app` (tab bar always visible):

- **Track** (`/app`) — month calendar, period/flow, hormone plot. No dashboard.
- **Insights** (`/app/insights`) — hormone plot, a two-line hormone note, and phase dashboard. No calendar.
- **Friends** (`/app/friends`) — **friend** follows as profile links (initials, nickname, `Day n · Phase`). **Partners are not listed on this tab.** Tapping one opens their shared view at `/circle/:followId`. **Manage circle** opens `/circle`.
- **Account** (`/app/account`) — email, nickname, cycle length, manage circle, sign out.

`/circle` is where you search, handle the inbox, cancel requests you sent, manage **friend and partner** follows, and remove people who can see your phase. `/circle/:followId` shows one person’s shared view.

`GET /follows` includes `phase`, `cycle_day`, and `phase_label` (server-computed; no dates or flow).

## Code

- `backend/app/models.py` — `User.nickname`, `FollowRequest`
- `backend/app/routers/follows.py`, `app/routers/users.py` (`/me`, `/search`)
- `backend/app/phase_content.py` — decides what a friend vs a partner may see
- `backend/tests/test_follows.py` — the lifecycle rules above, as tests
- `frontend/src/components/Circle.jsx`, `SharedCycle.jsx`
- `frontend/src/api/follows.js`
