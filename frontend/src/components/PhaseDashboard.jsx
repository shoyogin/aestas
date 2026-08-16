import { useEffect, useRef, useState } from 'react'
import { PHASE_LABELS } from '../cycle/phaseEngine'
import { getPanelsForPhase, PHASE_DISCLAIMER } from '../cycle/phaseContent'

const ARROW_CLASS =
  'flex-shrink-0 w-12 h-12 rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium text-xl transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50'

const PANEL_META = [
  { key: 'food', heading: 'Food' },
  { key: 'activity', heading: 'Physical activity' },
  { key: 'mood', heading: 'Mood' },
  { key: 'drive', heading: 'Sexual drive' },
]

function PanelSlide({ heading, title, bullets, why, imageSrc }) {
  return (
    <article className="w-full h-[40rem] md:h-[44rem] flex flex-col rounded-2xl border border-powder-blush/30 bg-dusty-mauve/15 p-5 md:p-8 text-left overflow-hidden">
      <img
        src={imageSrc}
        alt=""
        className="w-full h-48 md:h-56 object-contain rounded-xl mb-5 bg-[#0b1c2c] flex-shrink-0"
      />
      <h2 className="text-powder-blush text-sm font-semibold uppercase tracking-wide mb-2 flex-shrink-0">
        {heading}
      </h2>
      <h3 className="text-peach-fuzz font-bold text-2xl md:text-3xl mb-4 truncate flex-shrink-0">
        {title}
      </h3>
      <ul className="space-y-3 text-powder-blush text-lg md:text-xl mb-4 flex-shrink-0">
        {bullets.map((line) => (
          <li key={line} className="flex gap-2 min-w-0">
            <span className="flex-shrink-0" aria-hidden>
              •
            </span>
            <span className="truncate whitespace-nowrap" title={line}>{line}</span>
          </li>
        ))}
      </ul>
      <p className="text-peach-fuzz/90 text-base md:text-lg truncate mt-auto">{why}</p>
    </article>
  )
}

export default function PhaseDashboard({ phase, cycleDay }) {
  const [index, setIndex] = useState(0)
  const [dragX, setDragX] = useState(0)
  const [animate, setAnimate] = useState(true)
  const [ms, setMs] = useState(300)
  const drag = useRef({ active: false, startX: 0, width: 1 })
  const panels = getPanelsForPhase(phase)
  const label = phase ? PHASE_LABELS[phase] : null
  const n = PANEL_META.length

  useEffect(() => {
    setIndex(0)
    setDragX(0)
    setAnimate(false)
  }, [phase])

  if (!phase || !panels) {
    return (
      <div className="mt-10 text-center">
        <p className="text-peach-fuzz font-semibold text-2xl mb-2">This cycle’s dashboard</p>
        <p className="text-powder-blush/90 text-base">
          Select or log a cycle start to see food, movement, mood, and intimacy suggestions for each phase.
        </p>
      </div>
    )
  }

  const wrap = (i) => ((i % n) + n) % n

  const goTo = (next) => {
    const i = wrap(next)
    const dist = Math.abs(i - index)
    setMs(dist > 1 ? 700 : 300)
    setAnimate(true)
    setDragX(0)
    setIndex(i)
  }

  const onPointerDown = (e) => {
    drag.current = {
      active: true,
      startX: e.clientX,
      width: e.currentTarget.clientWidth || 1,
    }
    setAnimate(false)
    e.currentTarget.setPointerCapture(e.pointerId)
  }

  const onPointerMove = (e) => {
    if (!drag.current.active) return
    setDragX(e.clientX - drag.current.startX)
  }

  const onPointerUp = (e) => {
    if (!drag.current.active) return
    const dx = e.clientX - drag.current.startX
    const threshold = drag.current.width * 0.2
    drag.current.active = false
    setDragX(0)
    setAnimate(true)
    if (dx <= -threshold) goTo(index + 1)
    else if (dx >= threshold) goTo(index - 1)
  }

  const meta = PANEL_META[index]

  return (
    <div className="mt-10 w-full">
      <p className="text-peach-fuzz font-semibold text-2xl text-center mb-1">
        Day {cycleDay} · {label}
      </p>
      <p className="text-powder-blush/80 text-base text-center mb-6">
        {index + 1} / {n} · {meta.heading}
      </p>

      <div className="flex items-center justify-center gap-3">
        <button type="button" onClick={() => goTo(index - 1)} className={ARROW_CLASS} aria-label="Previous panel">
          ←
        </button>

        <div
          className="flex-1 min-w-0 overflow-hidden rounded-2xl touch-pan-y cursor-grab active:cursor-grabbing"
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          <div
            className={`flex ${animate ? 'ease-out' : ''}`}
            style={{
              transform: `translateX(calc(${-index * 100}% + ${dragX}px))`,
              transition: animate ? `transform ${ms}ms ease-out` : 'none',
            }}
          >
            {PANEL_META.map((item) => {
              const panel = panels[item.key]
              return (
                <div key={item.key} className="w-full min-w-full max-w-full flex-[0_0_100%]">
                  <PanelSlide
                    heading={item.heading}
                    title={panel.title}
                    bullets={panel.bullets}
                    why={panel.why}
                    imageSrc={`/dashboard/panel-${item.key}-${phase}.png`}
                  />
                </div>
              )
            })}
          </div>
        </div>

        <button type="button" onClick={() => goTo(index + 1)} className={ARROW_CLASS} aria-label="Next panel">
          →
        </button>
      </div>

      <p className="text-powder-blush/60 text-sm text-center mt-6">{PHASE_DISCLAIMER}</p>
    </div>
  )
}
