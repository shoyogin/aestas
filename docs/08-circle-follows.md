# 8. Circle: friends and partner follows

Aestas lets you **link profiles by nickname**, with **consent**. There is no gender field. The **link type** is what matters:

- **Friend** — follow someone’s cycle at a respectful distance.
- **Girlfriend / partner** — see fuller “how to support them this week” guidance.

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

`PATCH /users/me` with `{ "nickname": "luna_28" }`. Stored **lowercase**, unique, 3–24 characters (`a-z`, `0-9`, `_`). Search never uses email: `GET /users/search?nickname=lu`.

Set your nickname on **Account** (`/app/account`) or **Circle** (`/circle`) before others can find you.

## Requests

1. Search a nickname, pick **Friend** or **Girlfriend / partner**, send request.
2. They see it in **Inbox** (pending requests older than **14 days** are hidden).
3. **Accept** or **Refuse**. Refuse does not explain why; the requester just is not connected.
4. At most **one accepted partner** inbound at a time. Many friends are allowed.
5. Either side can **unfollow / revoke**.

## API (session cookie)

- `POST /follows` `{ nickname, link_type }`
- `GET /follows/inbox`
- `GET /follows` (people I follow, accepted)
- `POST /follows/{id}/accept` \| `refuse`
- `DELETE /follows/{id}`
- `GET /follows/{id}/cycle` — filtered view for the **follower** only

Phase is computed on the **server** (`backend/cycle_phase.py`) so raw dates never leave the owner’s account.

## UI

Bottom tabs on `/app` (tab bar always visible):

- **Track** (`/app`) — month calendar, period/flow, hormone plot. No dashboard.
- **Insights** (`/app/insights`) — hormone plot, a two-line hormone note, and phase dashboard. No calendar.
- **Friends** (`/app/friends`) — read-only month calendar plus **friend** follows as profile buttons (initials, nickname, `Day n · Phase`). **Partners are not listed on this tab.** Tap is a placeholder until static advice exists. **Manage circle** opens `/circle`.
- **Account** (`/app/account`) — email, nickname, cycle length, manage circle, sign out.

`/circle` is still where you search, handle inbox, and manage **friend and partner** follows. `/circle/:followId` stays for the later advice view.

`GET /follows` includes `phase`, `cycle_day`, and `phase_label` (server-computed; no dates or flow).

## Code

- `backend/models.py` — `User.nickname`, `FollowRequest`
- `backend/routers/follows.py`, `routers/users.py` (`/me`, `/search`)
- `frontend/src/components/Circle.jsx`, `SharedCycle.jsx`
- `frontend/src/api/follows.js`
