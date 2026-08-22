import { api } from './client'

export async function updateProfile({ nickname, timezone }) {
  const body = {}
  if (nickname !== undefined) body.nickname = nickname
  if (timezone !== undefined) body.timezone = timezone
  const { data } = await api.patch('/users/me', body)
  return data
}

export async function patchNickname(nickname) {
  return updateProfile({ nickname })
}

export async function searchNicknames(nickname) {
  const { data } = await api.get('/users/search', { params: { nickname } })
  return data
}

export async function sendFollow({ nickname, link_type }) {
  const { data } = await api.post('/follows', { nickname, link_type })
  return data
}

/** Requests waiting on me. */
export async function getInbox() {
  const { data } = await api.get('/follows/inbox')
  return data
}

/** People I follow, with the phase they share. */
export async function getFollowing() {
  const { data } = await api.get('/follows')
  return data
}

/** Requests I have sent that are still pending — cancellable, nothing else. */
export async function getOutgoingRequests() {
  const { data } = await api.get('/follows/requests')
  return data
}

/** People who can see my phase, so I can take that access back. */
export async function getFollowers() {
  const { data } = await api.get('/follows/followers')
  return data
}

export async function acceptFollow(id) {
  const { data } = await api.post(`/follows/${id}/accept`)
  return data
}

export async function refuseFollow(id) {
  const { data } = await api.post(`/follows/${id}/refuse`)
  return data
}

/** Withdraw my pending request, unfollow, or remove one of my followers. */
export async function removeFollow(id) {
  await api.delete(`/follows/${id}`)
}

export async function getSharedCycle(id) {
  const { data } = await api.get(`/follows/${id}/cycle`)
  return data
}
