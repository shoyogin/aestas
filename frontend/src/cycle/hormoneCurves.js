/**
 * Schematic (not lab) hormone curves for a typical ovulatory cycle, scaled to cycle length.
 * Values are 0–1 for plotting only.
 */

function clamp01(v) {
  return Math.min(1, Math.max(0, v))
}

function gauss(x, mu, sigma) {
  const s = Math.max(0.35, sigma)
  return Math.exp(-0.5 * ((x - mu) / s) ** 2)
}

function logistic(x, mid, k) {
  return 1 / (1 + Math.exp(-k * (x - mid)))
}

/**
 * @param {number} day 1-based cycle day
 * @param {number} length
 * @param {number} ovDay estimated ovulation day
 */
export function hormoneLevels(day, length, ovDay) {
  const t = day
  const ov = ovDay
  const lutealSpan = Math.max(4, length - ov)

  const estrogen = clamp01(
    0.12
      + 0.72 * logistic(t, ov - 3.2, 1.15)
      - 0.42 * gauss(t, ov, 0.85)
      + 0.38 * gauss(t, ov + lutealSpan * 0.42, lutealSpan * 0.22)
      - 0.08 * gauss(t, 2, 1.4),
  )

  const progesterone = clamp01(
    0.08
      + 0.82 * logistic(t, ov + 1.2, 1.4) * (1 - logistic(t, length - 1.6, 1.6)),
  )

  const lh = clamp01(0.12 + 0.88 * gauss(t, ov, 0.55))
  const fsh = clamp01(
    0.18
      + 0.28 * gauss(t, 3.5, 2.2)
      + 0.42 * gauss(t, ov, 0.7),
  )

  return { estrogen, progesterone, lh, fsh }
}

export const HORMONE_SERIES = [
  { id: 'estrogen', label: 'Estrogen', color: '#fed0bb' },
  { id: 'progesterone', label: 'Progesterone', color: '#b23a48' },
  { id: 'lh', label: 'LH', color: '#8fbc8f' },
  { id: 'fsh', label: 'FSH', color: '#7eb8da' },
]

export function sampleHormones(length, ovDay) {
  const points = []
  for (let day = 1; day <= length; day += 1) {
    points.push({ day, ...hormoneLevels(day, length, ovDay) })
  }
  return points
}
