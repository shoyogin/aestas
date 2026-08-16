"""Server-side cycle phase (same rules as frontend/src/cycle/phaseEngine.js)."""
from datetime import date, timedelta


def _latest_start_on_or_before(start_dates: list[date], selected: date) -> date | None:
    best = None
    for d in start_dates or []:
        if d is None or d > selected:
            continue
        if best is None or d > best:
            best = d
    return best


def _next_start_after(start_dates: list[date], start: date) -> date | None:
    best = None
    for d in start_dates or []:
        if d is None or d <= start:
            continue
        if best is None or d < best:
            best = d
    return best


def _recorded_menstrual_end_day(
    start: date, end_dates: list[date], start_dates: list[date], length: int
) -> int | None:
    cycle_end_cap = start + timedelta(days=length)
    next_start = _next_start_after(start_dates, start)
    cap = next_start if next_start and next_start < cycle_end_cap else cycle_end_cap
    best_end = None
    for d in end_dates or []:
        if d is None or d < start or d >= cap:
            continue
        if best_end is None or d > best_end:
            best_end = d
    if best_end is None:
        return None
    return (best_end - start).days + 1


def _default_menstrual_days(length: int) -> int:
    return max(3, round((length * 5) / 28))


def _ovulation_window(length: int) -> tuple[int, int]:
    ov_day = max(1, length - 14)
    ov_start = ov_day - 1
    ov_end = ov_day + 1
    if ov_start < 1:
        ov_start = 1
        ov_end = min(length, 3)
    if ov_end > length:
        ov_end = length
        ov_start = max(1, length - 2)
    return ov_start, ov_end


def _assign_phase(cycle_day: int, m_end: int, ov_start: int, ov_end: int, length: int) -> str:
    if cycle_day <= m_end:
        return "menstrual"
    if cycle_day < ov_start:
        return "follicular"
    if cycle_day <= ov_end:
        return "ovulation"
    if cycle_day <= length:
        return "luteal"
    return "luteal"


def get_phase_for_today(cycle_length: int | None, start_dates: list[date] | None, end_dates: list[date] | None):
    """Return {phase, cycle_day} for today, or phase None."""
    length = int(cycle_length) if cycle_length else 0
    if length < 1:
        return {"phase": None, "cycle_day": None}
    selected = date.today()
    starts = list(start_dates or [])
    ends = list(end_dates or [])
    start = _latest_start_on_or_before(starts, selected)
    if start is None:
        return {"phase": None, "cycle_day": None}
    raw_day = (selected - start).days + 1
    if raw_day < 1:
        return {"phase": None, "cycle_day": None}
    cycle_day = ((raw_day - 1) % length) + 1
    ov_start, ov_end = _ovulation_window(length)
    max_m = max(0, ov_start - 1)
    recorded = _recorded_menstrual_end_day(start, ends, starts, length)
    default_m = _default_menstrual_days(length)
    m_end = min(max(recorded if recorded is not None else default_m, 0), max_m)
    phase = _assign_phase(cycle_day, m_end, ov_start, ov_end, length)
    return {"phase": phase, "cycle_day": cycle_day}
