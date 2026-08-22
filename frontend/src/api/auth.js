import { api } from './client'

export async function getMe() {
  const { data } = await api.get('/auth/me')
  return data
}

export async function logout() {
  await api.post('/auth/logout')
}
