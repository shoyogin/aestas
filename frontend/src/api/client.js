import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const api = axios.create({
  baseURL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

/** Paths that are allowed to 401 without meaning "your session expired". */
const SILENT_401 = ['/auth/me', '/auth/logout']

/**
 * Turn an axios error into something worth showing a user. The backend sends
 * `detail`; anything else is a network or server failure.
 */
export function errorMessage(err, fallback = 'Something went wrong. Please try again.') {
  const detail = err?.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (!err?.response) return 'Could not reach the server. Check your connection.'
  return fallback
}

let onSessionExpired = null

/** Called once when a request fails because the session is no longer valid. */
export function setSessionExpiredHandler(handler) {
  onSessionExpired = handler
}

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const url = error?.config?.url ?? ''
    if (status === 401 && !SILENT_401.some((path) => url.includes(path))) {
      // Without this an expired session silently renders empty screens forever.
      onSessionExpired?.()
    }
    return Promise.reject(error)
  },
)
