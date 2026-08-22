import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { describe, expect, it } from 'vitest'
import { getPhaseForDate, PHASE_IDS } from './phaseEngine'
import { parseYMD, addDays, toYMD } from './dates'

/**
 * The same file the backend suite runs. backend/app/cycle_phase.py is an
 * independent implementation of these rules, so if either side drifts, one of
 * the two suites goes red.
 */
const cases = JSON.parse(
  readFileSync(fileURLToPath(new URL('../../../shared/phase-cases.json', import.meta.url)), 'utf8'),
).cases

const run = (c) =>
  getPhaseForDate({
    selectedDate: parseYMD(c.selected),
    cycleLength: c.cycle_length,
    startDates: c.start_dates,
    endDates: c.end_dates,
  })

describe('phase engine — golden cases shared with the backend', () => {
  it.each(cases.map((c) => [c.name, c]))('%s', (_name, c) => {
    const got = run(c)
    expect({ phase: got.phase, cycleDay: got.cycleDay }).toEqual({
      phase: c.expect.phase,
      cycleDay: c.expect.cycle_day,
    })
  })
})

describe('phase engine — invariants', () => {
  const lengths = Array.from({ length: 31 }, (_, i) => i + 15)

  it.each(lengths)('every day of a %i-day cycle has a phase', (length) => {
    const start = parseYMD('2026-03-01')
    for (let offset = 0; offset < length; offset += 1) {
      const result = getPhaseForDate({
        selectedDate: addDays(start, offset),
        cycleLength: length,
        startDates: ['2026-03-01'],
        endDates: [],
      })
      expect(PHASE_IDS).toContain(result.phase)
      expect(result.cycleDay).toBe(offset + 1)
    }
  })

  it.each(lengths)('phases never run backwards in a %i-day cycle', (length) => {
    const start = parseYMD('2026-03-01')
    const seen = []
    for (let offset = 0; offset < length; offset += 1) {
      const { phase } = getPhaseForDate({
        selectedDate: addDays(start, offset),
        cycleLength: length,
        startDates: ['2026-03-01'],
        endDates: [],
      })
      if (seen[seen.length - 1] !== phase) seen.push(phase)
    }
    expect(seen).toEqual(PHASE_IDS.filter((p) => seen.includes(p)))
  })

  it('reports the cycle start it measured from', () => {
    const result = getPhaseForDate({
      selectedDate: parseYMD('2026-03-10'),
      cycleLength: 28,
      startDates: ['2026-03-01', '2026-04-01'],
      endDates: [],
    })
    expect(result.cycleStart).toBe('2026-03-01')
  })

  it('window boundaries line up with the reported phases', () => {
    const { windows } = getPhaseForDate({
      selectedDate: parseYMD('2026-03-01'),
      cycleLength: 28,
      startDates: ['2026-03-01'],
      endDates: [],
    })
    const present = PHASE_IDS.filter((p) => windows[p])
    present.forEach((phase) => {
      const { start, end } = windows[phase]
      expect(start).toBeLessThanOrEqual(end)
      for (const day of [start, end]) {
        const got = getPhaseForDate({
          selectedDate: addDays(parseYMD('2026-03-01'), day - 1),
          cycleLength: 28,
          startDates: ['2026-03-01'],
          endDates: [],
        })
        expect(got.phase).toBe(phase)
      }
    })
  })
})

describe('date helpers', () => {
  it('formats and parses local calendar days symmetrically', () => {
    expect(toYMD(parseYMD('2026-03-09'))).toBe('2026-03-09')
  })

  it('parses YYYY-MM-DD as local, not UTC', () => {
    // `new Date('2026-03-09')` is midnight UTC, which is 8 March in the Americas.
    expect(parseYMD('2026-03-09').getDate()).toBe(9)
  })

  it('crosses a month boundary when adding days', () => {
    expect(toYMD(addDays(parseYMD('2026-03-31'), 1))).toBe('2026-04-01')
  })
})
