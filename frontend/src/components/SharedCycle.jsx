import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import Logo from './Logo'
import ErrorBanner from './ErrorBanner'
import { getSharedCycle } from '../api/follows'
import { getPhaseContent } from '../api/content'
import { errorMessage } from '../api/client'

const BTN =
  'rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium px-4 py-2 transition-colors'

// Fallbacks only; the server sends the authoritative order and headings.
const PANEL_ORDER = ['food', 'activity', 'mood', 'drive']
const HEADINGS = {
  food: 'Food',
  activity: 'Physical activity',
  mood: 'Mood',
  drive: 'Sexual drive',
}

export default function SharedCycle() {
  const { followId } = useParams()
  const navigate = useNavigate()
  const [data, setData] = useState(null)
  const [content, setContent] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    getSharedCycle(followId)
      .then((res) => !cancelled && setData(res))
      .catch((err) => !cancelled && setError(errorMessage(err, 'Could not load.')))
    getPhaseContent()
      .then((res) => !cancelled && setContent(res))
      .catch(() => {})
    return () => {
      cancelled = true
    }
  }, [followId])

  if (error) {
    return (
      <div className="min-h-screen bg-night-bordeaux text-peach-fuzz px-6 py-10">
        <button type="button" className={BTN} onClick={() => navigate('/circle')}>← Circle</button>
        <ErrorBanner message={error} className="mt-6" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen bg-night-bordeaux text-powder-blush flex items-center justify-center">
        Loading…
      </div>
    )
  }

  const panels = data.panels || {}
  const order = content?.panel_order ?? PANEL_ORDER
  const headings = content?.panel_headings ?? HEADINGS
  const keys = order.filter((k) => panels[k])

  return (
    <div className="min-h-screen bg-night-bordeaux text-peach-fuzz px-6 py-10">
      <div className="max-w-lg mx-auto">
        <div className="flex items-center justify-between mb-6">
          <button type="button" className={BTN} onClick={() => navigate('/circle')}>
            ← Circle
          </button>
          <Logo className="w-12 h-12 text-powder-blush" />
        </div>
        <h1 className="text-3xl font-bold mb-1">{data.nickname}</h1>
        <p className="text-powder-blush mb-2">
          {data.phase_label
            ? `Day ${data.cycle_day} · ${data.phase_label}`
            : 'No cycle start on file yet.'}
        </p>
        <p className="text-powder-blush/80 text-sm mb-4">
          Viewing as {data.link_type === 'partner' ? 'girlfriend / partner' : 'friend'}
        </p>
        {panels.support && (
          <p className="rounded-xl border border-powder-blush/30 bg-dusty-mauve/20 p-4 mb-6 text-lg">
            {panels.support}
          </p>
        )}
        <div className="space-y-4">
          {keys.map((key) => {
            const p = panels[key]
            return (
              <article
                key={key}
                className="rounded-2xl border border-powder-blush/30 bg-dusty-mauve/15 p-5"
              >
                <h2 className="text-powder-blush text-sm uppercase tracking-wide mb-1">
                  {headings[key] ?? key}
                </h2>
                <h3 className="font-bold text-xl mb-3">{p.title}</h3>
                <ul className="list-disc list-inside space-y-2 text-powder-blush">
                  {p.bullets.map((b) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
                <p className="mt-3 text-peach-fuzz/90 text-sm">{p.why}</p>
              </article>
            )
          })}
        </div>
        <p className="text-powder-blush/60 text-xs text-center mt-8">{data.disclaimer}</p>
      </div>
    </div>
  )
}
