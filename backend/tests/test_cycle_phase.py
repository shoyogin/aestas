"""The phase engine, driven by the golden cases shared with the frontend."""
from datetime import date, timedelta

import pytest

from app.cycle_phase import (
    _default_menstrual_days,
    _ovulation_days,
    _ovulation_window,
    get_phase_for_date,
    get_phase_for_today,
    today_in,
)


def _dates(values):
    return [date.fromisoformat(v) for v in values]


def test_golden_cases(phase_cases):
    """Every case in shared/phase-cases.json. The frontend engine runs the same
    file, so a divergence between the two implementations fails a build."""
    failures = []
    for case in phase_cases:
        got = get_phase_for_date(
            date.fromisoformat(case["selected"]),
            case["cycle_length"],
            _dates(case["start_dates"]),
            _dates(case["end_dates"]),
        )
        expected = case["expect"]
        if (got["phase"], got["cycle_day"]) != (expected["phase"], expected["cycle_day"]):
            failures.append(
                f"{case['name']}: expected {expected}, got "
                f"{{'phase': {got['phase']!r}, 'cycle_day': {got['cycle_day']!r}}}"
            )
    assert not failures, "\n".join(failures)


def test_phase_label_accompanies_phase():
    result = get_phase_for_date(date(2026, 3, 1), 28, [date(2026, 3, 1)], [])
    assert result["phase"] == "menstrual"
    assert result["phase_label"] == "Menstrual"


def test_no_phase_has_no_label():
    assert get_phase_for_date(date(2026, 3, 1), None, [], [])["phase_label"] is None


@pytest.mark.parametrize("length", range(15, 46))
def test_every_allowed_cycle_length_covers_every_day(length):
    """Onboarding allows 15-45 days; no day in any of those cycles may be
    unclassified, and the day number must always be within the cycle."""
    start = date(2026, 3, 1)
    for offset in range(length):
        result = get_phase_for_date(start + timedelta(days=offset), length, [start], [])
        assert result["phase"] in {"menstrual", "follicular", "ovulation", "luteal"}
        assert result["cycle_day"] == offset + 1


@pytest.mark.parametrize("length", range(15, 46))
def test_phases_never_run_backwards(length):
    """Within one cycle the phases must appear in order and never repeat, so
    the UI can never show follicular after luteal."""
    start = date(2026, 3, 1)
    order = ["menstrual", "follicular", "ovulation", "luteal"]
    seen = []
    for offset in range(length):
        phase = get_phase_for_date(start + timedelta(days=offset), length, [start], [])["phase"]
        if not seen or seen[-1] != phase:
            seen.append(phase)
    assert seen == [p for p in order if p in seen]


@pytest.mark.parametrize("length", range(15, 46))
def test_every_cycle_length_has_all_four_phases(length):
    """Ovulation scales with the cycle instead of sitting at a fixed 3 days on a
    fixed day, so no supported length can lose a phase entirely. A 15-day cycle
    used to report ovulation on day 1 and no menstrual phase at all."""
    start = date(2026, 3, 1)
    seen = {
        get_phase_for_date(start + timedelta(days=offset), length, [start], [])["phase"]
        for offset in range(length)
    }
    assert seen == {"menstrual", "follicular", "ovulation", "luteal"}


@pytest.mark.parametrize("length", range(15, 46))
def test_ovulation_window_is_as_wide_as_the_rules_say(length):
    ov_start, ov_end, _ = _ovulation_window(length)
    assert ov_end - ov_start + 1 == _ovulation_days(length)


def test_ovulation_widens_with_the_cycle():
    """~3 days on a 28-day cycle, scaled from there."""
    assert _ovulation_days(28) == 3
    assert _ovulation_days(35) == 4
    assert _ovulation_days(45) == 5
    # Never narrower than three days, however short the cycle.
    assert _ovulation_days(15) == 3


@pytest.mark.parametrize("length", range(15, 46))
def test_ovulation_never_overlaps_the_menstrual_window(length):
    """The window must leave room for the period and at least one follicular day."""
    ov_start, ov_end, _ = _ovulation_window(length)
    assert ov_start >= _default_menstrual_days(length) + 2
    assert ov_end <= length


@pytest.mark.parametrize("length", range(21, 46))
def test_normal_cycles_still_count_back_fourteen_days(length):
    """For cycles of 21 days and up, the standard constant-luteal rule is
    unchanged — the scaling only rescues cycles too short for it."""
    _, _, ov_day = _ovulation_window(length)
    assert ov_day == length - 14


def test_twenty_eight_day_cycle_is_unchanged():
    """The common case must land exactly where it always did."""
    ov_start, ov_end, ov_day = _ovulation_window(28)
    assert (ov_start, ov_end, ov_day) == (13, 15, 14)


def test_rounding_matches_javascript_on_a_42_day_cycle():
    """42 * 3 / 28 is exactly 4.5. Python's round() would answer 4 and
    JavaScript's Math.round() 5, so the engines would silently disagree."""
    assert _ovulation_days(42) == 5


def test_today_respects_the_users_timezone():
    """Kiritimati is UTC+14 and Niue UTC-11, so they are never on the same day."""
    assert today_in("Pacific/Kiritimati") != today_in("Pacific/Niue")


def test_unknown_timezone_falls_back_to_utc():
    assert today_in("Not/AZone") == today_in("UTC")


def test_phase_for_today_uses_the_users_own_day():
    """A user whose local date is already tomorrow is one cycle day ahead."""
    early = today_in("Pacific/Niue")
    late = today_in("Pacific/Kiritimati")
    start = early - timedelta(days=3)
    result_early = get_phase_for_today(28, [start], [], "Pacific/Niue")
    result_late = get_phase_for_today(28, [start], [], "Pacific/Kiritimati")
    assert result_late["cycle_day"] - result_early["cycle_day"] == (late - early).days
