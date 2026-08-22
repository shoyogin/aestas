"""The phase engine, driven by the golden cases shared with the frontend."""
from datetime import date, timedelta

import pytest

from app.cycle_phase import get_phase_for_date, get_phase_for_today, today_in


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
