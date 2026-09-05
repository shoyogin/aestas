import { useCallback, useEffect, useRef, useState } from 'react'

const ARROW_CLASS =
  'flex-shrink-0 w-12 h-12 rounded-xl bg-dusty-mauve/40 hover:bg-dusty-mauve/60 text-peach-fuzz font-medium text-xl transition-colors focus:outline-none focus:ring-2 focus:ring-powder-blush/50'

function PanelSlide({ heading, panel, imageSrc, hidden }) {
  return (
    <article
      className="w-full h-full flex flex-col rounded-2xl border border-powder-blush/30 bg-dusty-mauve/15 p-5 md:p-8 text-left"
      aria-hidden={hidden}
    >
      <img
        src={imageSrc}
        alt=""
        loading="lazy"
        className="w-full h-40 md:h-52 object-contain rounded-xl mb-5 bg-[#0b1c2c] flex-shrink-0"
      />
      <h3 className="text-powder-blush text-sm font-semibold uppercase tracking-wide mb-2">
        {heading}
      </h3>
      <h4 className="text-peach-fuzz font-bold text-2xl md:text-3xl mb-4">{panel.title}</h4>
      <ul className="space-y-3 text-powder-blush text-base md:text-lg mb-5">
        {panel.bullets.map((line) => (
          <li key={line} className="flex gap-2">
            <span className="flex-shrink-0" aria-hidden>
              •
            </span>
            {/* Bullets wrap: truncating them put the advice out of reach on
                touch devices, where a title tooltip never appears. */}
            <span>{line}</span>
          </li>
        ))}
      </ul>
      <p className="text-peach-fuzz/90 text-sm md:text-base mt-auto pt-2">{panel.why}</p>
    </article>
  )
}

export default function PhaseDashboard({ phase, cycleDay, content }) {
  const [index, setIndex] = useState(0)
  const [dragX, setDragX] = useState(0)
  const [animate, setAnimate] = useState(false)
  const drag = useRef({ active: false, startX: 0, width: 1 })

  const order = content?.panel_order ?? []
  const headings = content?.panel_headings ?? {}
  const panels = phase ? content?.panels?.[phase] : null
  const label = phase ? content?.labels?.[phase] : null
  const keys = order.filter((key) => panels?.[key])
  const n = keys.length

  useEffect(() => {
    setIndex(0)
    setDragX(0)
    setAnimate(false)
  }, [phase])

  const goTo = useCallback(
    (next) => {
      if (n === 0) return
      setAnimate(true)
      setDragX(0)
      setIndex(((next % n) + n) % n)
    },
    [n],
  )

  const onKeyDown = (e) => {
    if (e.key === 'ArrowRight') {
      e.preventDefault()
      goTo(index + 1)
    } else if (e.key === 'ArrowLeft') {
      e.preventDefault()
      goTo(index - 1)
    }
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

  if (!phase || !panels || n === 0) {
    return (
      <div className="mt-10 text-center">
        <p className="text-peach-fuzz font-semibold text-2xl mb-2">This cycle’s dashboard</p>
        <p className="text-powder-blush/90 text-base">
          {content
            ? 'Select or log a cycle start to see food, movement, mood, and intimacy suggestions for each phase.'
            : 'Loading suggestions…'}
        </p>
      </div>
    )
  }

  const activeKey = keys[index]

  return (
    <div className="mt-10 w-full">
      <p className="text-peach-fuzz font-semibold text-2xl text-center mb-1">
        Day {cycleDay} · {label}
      </p>
      <p className="text-powder-blush/80 text-base text-center mb-6" aria-live="polite">
        {index + 1} / {n} · {headings[activeKey] ?? activeKey}
      </p>

      <div className="flex items-center justify-center gap-3">
        <button
          type="button"
          onClick={() => goTo(index - 1)}
          className={ARROW_CLASS}
          aria-label="Previous panel"
        >
          ←
        </button>

        <div
          className="flex-1 min-w-0 overflow-hidden rounded-2xl touch-pan-y cursor-grab active:cursor-grabbing focus:outline-none focus:ring-2 focus:ring-powder-blush/50"
          role="group"
          aria-roledescription="carousel"
          aria-label="Phase suggestions"
          tabIndex={0}
          onKeyDown={onKeyDown}
          onPointerDown={onPointerDown}
          onPointerMove={onPointerMove}
          onPointerUp={onPointerUp}
          onPointerCancel={onPointerUp}
        >
          <div
            className="flex items-stretch"
            style={{
              transform: `translateX(calc(${-index * 100}% + ${dragX}px))`,
              transition: animate ? 'transform 300ms ease-out' : 'none',
            }}
          >
            {keys.map((key, i) => (
              <div key={key} className="w-full min-w-full max-w-full flex-[0_0_100%]">
                <PanelSlide
                  heading={headings[key] ?? key}
                  panel={panels[key]}
                  imageSrc={`/dashboard/panel-${key}-${phase}.png`}
                  hidden={i !== index}
                />
              </div>
            ))}
          </div>
        </div>

        <button
          type="button"
          onClick={() => goTo(index + 1)}
          className={ARROW_CLASS}
          aria-label="Next panel"
        >
          →
        </button>
      </div>

      <div className="flex justify-center gap-2 mt-4">
        {keys.map((key, i) => (
          <button
            key={key}
            type="button"
            onClick={() => goTo(i)}
            aria-label={`Show ${headings[key] ?? key}`}
            aria-current={i === index}
            className={`h-2 rounded-full transition-all ${
              i === index ? 'w-6 bg-peach-fuzz' : 'w-2 bg-powder-blush/40'
            }`}
          />
        ))}
      </div>

      {content?.disclaimer && (
        <p className="text-powder-blush/60 text-sm text-center mt-6">{content.disclaimer}</p>
      )}
    </div>
  )
}
