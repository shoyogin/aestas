# 7. Cycle phases and the dashboard

This page explains how Aestas maps a **selected calendar day** to one of four cycle phases and what the four panels under the calendar mean.

This is **educational**, not medical advice. Real cycles vary (stress, PCOS, perimenopause, contraception). The app estimates phases from the dates **you** logged.

## What you see

On **Insights** (`/app/insights`), after the hormone plot, a **single-panel dashboard** (← → arrows) shows one of:

- **Food** — suggested meals and nutrients for that phase
- **Physical activity** — expected energy and movement ideas
- **Mood** — awareness and gentler/harder social load
- **Sexual drive** — comfort, desire, and intimacy ideas (wellness tone)

Each panel uses large type plus a top-down vector image in `frontend/public/dashboard/` named `panel-{food|activity|mood|drive}-{menstrual|follicular|ovulation|luteal}.png`.

Changing the **selected** day on the month calendar recalculates the phase and updates the hormone plot and all four cards together. A small label (for example `Follicular · day 8`) stays in sync. On Insights, two lines under the plot explain what the curves are doing in that phase.

Under the calendar (after flow, before the dashboard) a **schematic hormone plot** shows estrogen, progesterone, LH, and FSH across the full cycle. The **current phase is a highlighted band**; a dashed line marks the selected cycle day. Curves are educational, not lab values.

If there is **no cycle start on or before** that date, the dashboard asks you to log a start instead of guessing.

## Data used

`GET /users/cycle-context` (session cookie required) returns:

- `cycle_length` — from onboarding (15–45 days)
- `cycle_start_dates` — every onboarding “last cycle” date and every **Period started** tap
- `cycle_end_dates` — every **Period ended** tap

The frontend does **not** store panel text in PostgreSQL. Copy lives in `frontend/src/cycle/phaseContent.js` so a later `GET /users/insights?date=` can replace it without changing the layout.

## How the phase is chosen

Code: `frontend/src/cycle/phaseEngine.js`.

1. Take the **latest** date in `cycle_start_dates` that is **≤ selected date**. That day is **cycle day 1**.
2. `cycleDay = selectedDate − start + 1`. If that is past `cycle_length`, wrap: `((cycleDay − 1) mod length) + 1` so future dates still map.
3. **Ovulation** is a **3-day** window centered on estimated ovulation day `max(1, length − 14)` (luteal is often ~14 days).
4. **Menstrual** is about **5 days** on a 28-day cycle, scaled as `max(3, round(length × 5 / 28))`, **or** through the recorded period end for this start if that is later — but **never into the ovulation window**.
5. **Follicular** is after menstrual until the day before ovulation.
6. **Luteal** is after ovulation through `length`.

### Example (28-day cycle, start 1 March)

| Dates (March) | Cycle day | Phase |
|---------------|-----------|--------|
| 1–5 | 1–5 | Menstrual |
| 6–12 | 6–12 | Follicular |
| 13–15 | 13–15 | Ovulation (centered on day 14) |
| 16–28 | 16–28 | Luteal |

If you logged **Period ended** on 8 March for that start, menstrual can extend through day 8 (still before ovulation).

## Code to look at

- `backend/routers/users.py` — `GET /users/cycle-context`
- `frontend/src/api/cycle.js` — client
- `frontend/src/cycle/phaseEngine.js` — math
- `frontend/src/cycle/phaseContent.js` — panel copy
- `frontend/src/components/HormoneChart.jsx` — schematic hormone plot + phase highlight
- `frontend/src/cycle/hormoneCurves.js` — estrogen, progesterone, LH, FSH samples
- `frontend/src/components/PhaseDashboard.jsx` — UI
- `frontend/src/components/AppHome.jsx` — shared cycle state for Track + Insights
- `frontend/src/components/Track.jsx` — calendar + plot
- `frontend/src/components/Insights.jsx` — plot + dashboard
