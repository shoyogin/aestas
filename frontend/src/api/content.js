import { api } from './client'

/**
 * Per-phase panel copy. The backend owns this text (app/content/phase_panels.json)
 * so it is never written twice; the frontend just renders what it is given.
 * @returns {Promise<{ labels: object, panel_order: string[], panel_headings: object, panels: object, disclaimer: string }>}
 */
export async function getPhaseContent() {
  const { data } = await api.get('/content/phases')
  return data
}
