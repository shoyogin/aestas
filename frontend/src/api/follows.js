import { api } from './client'

export async function patchNickname(nickname) {
  const { data } = await api.patch('/users/me', { nickname })
  return data
}

export async function searchNicknames(nickname) {
  const { data } = await api.get('/users/search', { params: { nickname } })
  return data
}

export async function sendFollow({ nickname, link_type }) {
  const { data } = await api.post('/follows', { nickname, link_type })
  return data
}

export async function getInbox() {
  const { data } = await api.get('/follows/inbox')
  return data
}

export async function getFollowing() {
  const { data } = await api.get('/follows')
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

export async function revokeFollow(id) {
  await api.delete(`/follows/${id}`)
}

export async function getSharedCycle(id) {
  const { data } = await api.get(`/follows/${id}/cycle`)
  return data
}
