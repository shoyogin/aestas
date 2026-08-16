import { PHASE_LABELS } from '../cycle/phaseEngine'
import { HORMONE_SERIES, sampleHormones } from '../cycle/hormoneCurves'

const W = 640
const H = 220
const PAD = { top: 16, right: 16, bottom: 36, left: 28 }

function polyline(points, key, xScale, yScale) {
  return points
    .map((p, i) => `${i === 0 ? 'M' : 'L'} ${xScale(p.day).toFixed(1)} ${yScale(p[key]).toFixed(1)}`)
    .join(' ')
}

export default function HormoneChart({ phase, cycleDay, cycleLength, windows, ovulationDay }) {
  const length = Number(cycleLength)
  if (!Number.isFinite(length) || length < 2) {
    return null
  }

  const ovDay = ovulationDay || Math.max(1, length - 14)
  const points = sampleHormones(length, ovDay)
  const innerW = W - PAD.left - PAD.right
  const innerH = H - PAD.top - PAD.bottom
  const xScale = (day) => PAD.left + ((day - 1) / (length - 1)) * innerW
  const yScale = (v) => PAD.top + (1 - v) * innerH

  const band = phase ? windows?.[phase] : null
  const highlight = band
    ? {
        x: xScale(band.start),
        width: Math.max(2, xScale(band.end) - xScale(band.start)),
      }
    : null

  const dayX = cycleDay ? xScale(cycleDay) : null
  const phaseLabel = phase ? PHASE_LABELS[phase] : null

  return (
    <div className="mb-2 w-full">
      <p className="text-peach-fuzz font-semibold text-lg text-center mb-1">
        Hormones this cycle
      </p>
      <p className="text-powder-blush/80 text-sm text-center mb-3">
        {phaseLabel ? `Schematic curves · ${phaseLabel} highlighted` : 'Schematic curves'}
      </p>
      <div className="rounded-2xl border border-powder-blush/30 bg-dusty-mauve/10 p-3 overflow-x-auto">
        <svg
          viewBox={`0 0 ${W} ${H}`}
          className="w-full h-auto min-h-[180px]"
          role="img"
          aria-label={
            phaseLabel
              ? `Hormone plot for a ${length}-day cycle, ${phaseLabel} phase highlighted`
              : `Hormone plot for a ${length}-day cycle`
          }
        >
          {highlight && (
            <rect
              x={highlight.x}
              y={PAD.top}
              width={highlight.width}
              height={innerH}
              fill="#fcb9b2"
              opacity="0.22"
              rx="4"
            />
          )}
          {[0.25, 0.5, 0.75].map((g) => (
            <line
              key={g}
              x1={PAD.left}
              x2={W - PAD.right}
              y1={yScale(g)}
              y2={yScale(g)}
              stroke="#fcb9b2"
              strokeOpacity="0.15"
            />
          ))}
          {HORMONE_SERIES.map((h) => (
            <path
              key={h.id}
              d={polyline(points, h.id, xScale, yScale)}
              fill="none"
              stroke={h.color}
              strokeWidth="2.25"
              strokeLinejoin="round"
              strokeLinecap="round"
            />
          ))}
          {dayX != null && (
            <line
              x1={dayX}
              x2={dayX}
              y1={PAD.top}
              y2={H - PAD.bottom}
              stroke="#fed0bb"
              strokeWidth="1.5"
              strokeDasharray="4 3"
            />
          )}
          <text x={PAD.left} y={H - 10} fill="#fcb9b2" fontSize="11">
            Day 1
          </text>
          <text x={W - PAD.right} y={H - 10} fill="#fcb9b2" fontSize="11" textAnchor="end">
            Day {length}
          </text>
          {cycleDay != null && (
            <text x={dayX} y={PAD.top - 2} fill="#fed0bb" fontSize="11" textAnchor="middle">
              Day {cycleDay}
            </text>
          )}
        </svg>
        <div className="flex flex-wrap justify-center gap-4 mt-2">
          {HORMONE_SERIES.map((h) => (
            <span key={h.id} className="flex items-center gap-1.5 text-xs text-powder-blush">
              <span
                className="inline-block w-3 h-0.5 rounded"
                style={{ backgroundColor: h.color }}
                aria-hidden
              />
              {h.label}
            </span>
          ))}
          {phaseLabel && (
            <span className="flex items-center gap-1.5 text-xs text-powder-blush">
              <span className="inline-block w-3 h-3 rounded-sm bg-powder-blush/30" aria-hidden />
              {phaseLabel}
            </span>
          )}
        </div>
      </div>
      <p className="text-powder-blush/50 text-xs text-center mt-2">
        Illustrative only — not measured from your labs.
      </p>
    </div>
  )
}
