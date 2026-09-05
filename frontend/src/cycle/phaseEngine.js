/**
 * Map a selected calendar date to a cycle phase using recorded starts and cycle length.
 *
 * Examples (28-day cycle, start 2026-03-01):
 *   2026-03-01 → day 1, menstrual
 *   2026-03-08 → day 8, follicular
 *   2026-03-14 → day 14, ovulation
 *   2026-03-20 → day 20, luteal
 */

import { addDays, diffDays, parseYMD, startOfDay, toYMD } from './dates'

export const PHASE_IDS = ['menstrual', 'follicular', 'ovulation', 'luteal']

export const PHASE_LABELS = {
  menstrual: 'Menstrual',
  follicular: 'Follicular',
  ovulation: 'Ovulation',
  luteal: 'Luteal',
}

// Phase lengths are expressed per 28-day cycle and scaled from there.
// Keep in step with backend/app/cycle_phase.py — shared/phase-cases.json is
// what proves the two still agree.
const MENSTRUAL_DAYS_PER_28 = 5
const OVULATION_DAYS_PER_28 = 3
const LUTEAL_DAYS = 14

/**
 * Latest recorded cycle start on or before selectedDate.
 */
export function latestStartOnOrBefore(startDates, selectedDate) {
  const selected = startOfDay(selectedDate)
  let best = null
  for (const raw of startDates || []) {
    const d = parseYMD(raw)
    if (!d || d > selected) continue
    if (!best || d > best) best = d
  }
  return best
}

function nextStartAfter(startDates, start) {
  const t = startOfDay(start)
  let best = null
  for (const raw of startDates || []) {
    const d = parseYMD(raw)
    if (!d || d <= t) continue
    if (!best || d < best) best = d
  }
  return best
}

/**
 * Recorded period-end day number (1-based) for this cycle start, if any.
 */
function recordedMenstrualEndDay(start, endDates, startDates, length) {
  const cycleEndCap = startOfDay(addDays(start, length))
  const nextStart = nextStartAfter(startDates, start)
  const cap = nextStart && nextStart < cycleEndCap ? nextStart : cycleEndCap
  let bestEnd = null
  for (const raw of endDates || []) {
    const d = parseYMD(raw)
    if (!d || d < start || d >= cap) continue
    if (!bestEnd || d > bestEnd) bestEnd = d
  }
  if (!bestEnd) return null
  return diffDays(bestEnd, start) + 1
}

/**
 * Default menstrual length scaled from ~5 days on a 28-day cycle.
 */
function defaultMenstrualDays(length) {
  return Math.max(3, Math.round((length * MENSTRUAL_DAYS_PER_28) / 28))
}

/**
 * Width of the ovulation window, scaled to the cycle like every other phase:
 * ~3 days at 28, wider on longer cycles.
 */
function ovulationDays(length) {
  return Math.max(3, Math.round((length * OVULATION_DAYS_PER_28) / 28))
}

/**
 * The ovulation window and the day it centres on. The window leans earlier
 * than ovulation itself, because the fertile window is mostly the days
 * leading up to it.
 */
export function ovulationWindow(length) {
  const width = ovulationDays(length)
  const before = Math.ceil((width - 1) / 2)

  // The luteal phase runs ~14 days whatever the cycle length, so ovulation is
  // counted back from the end. Below roughly 21 days that rule puts ovulation
  // on or before the period itself; keep menstrual plus one follicular day
  // ahead of it instead, so every phase still exists.
  const earliestStart = defaultMenstrualDays(length) + 2
  let ovDay = Math.max(length - LUTEAL_DAYS, earliestStart + before)

  let ovStart = ovDay - before
  let ovEnd = ovStart + width - 1
  if (ovEnd > length) {
    ovEnd = length
    ovStart = Math.max(1, ovEnd - width + 1)
    ovDay = Math.min(ovDay, ovEnd)
  }
  return { ovStart, ovEnd, ovDay }
}

function assignPhase(cycleDay, mEnd, ovStart, ovEnd, length) {
  if (cycleDay <= mEnd) return 'menstrual'
  if (cycleDay < ovStart) return 'follicular'
  if (cycleDay <= ovEnd) return 'ovulation'
  if (cycleDay <= length) return 'luteal'
  return 'luteal'
}

/**
 * @param {object} opts
 * @param {Date} opts.selectedDate
 * @param {number | null} opts.cycleLength
 * @param {string[]} opts.startDates YYYY-MM-DD
 * @param {string[]} opts.endDates YYYY-MM-DD
 * @returns {{ phase: string | null, cycleDay: number | null, cycleStart: string | null }}
 */
export function getPhaseForDate({ selectedDate, cycleLength, startDates, endDates }) {
  const length = Number(cycleLength)
  if (!selectedDate || !Number.isFinite(length) || length < 1) {
    return { phase: null, cycleDay: null, cycleStart: null }
  }

  const start = latestStartOnOrBefore(startDates, selectedDate)
  if (!start) {
    return { phase: null, cycleDay: null, cycleStart: null }
  }

  const rawDay = diffDays(selectedDate, start) + 1
  if (rawDay < 1) {
    return { phase: null, cycleDay: null, cycleStart: null }
  }
  const cycleDay = ((rawDay - 1) % length) + 1

  const { ovStart, ovEnd, ovDay } = ovulationWindow(length)
  const maxMenstrual = Math.max(0, ovStart - 1)
  const recorded = recordedMenstrualEndDay(start, endDates, startDates, length)
  const defaultM = defaultMenstrualDays(length)
  const mEnd = Math.min(Math.max(recorded ?? defaultM, 0), maxMenstrual)

  const phase = assignPhase(cycleDay, mEnd, ovStart, ovEnd, length)
  const windows = {
    menstrual: mEnd >= 1 ? { start: 1, end: mEnd } : null,
    follicular: mEnd + 1 <= ovStart - 1 ? { start: mEnd + 1, end: ovStart - 1 } : null,
    ovulation: { start: ovStart, end: ovEnd },
    luteal: ovEnd + 1 <= length ? { start: ovEnd + 1, end: length } : null,
  }
  return {
    phase,
    cycleDay,
    cycleStart: toYMD(start),
    cycleLength: length,
    windows,
    ovulationDay: ovDay,
  }
}
