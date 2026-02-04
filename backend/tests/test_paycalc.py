import pytest
from datetime import datetime
from app.models.schemas.paycalc_schema import ShiftSchema, BreakWindow, DaySummary
from app.services.pay_calculator import calculate_pay
from app.configs.paycalc_cfg import (
    DEFAULT_MULTIPLIER,
    SATURDAY_MULTIPLIER,
    SUNDAY_MULTIPLIER,
    HOLIDAY_MULTIPLIER,
)


# --- Helpers ---


def _make_shift(
    start: str,
    end: str,
    pay_rate: float = 25.0,
    overtime_end: str | None = None,
    break_start: str | None = None,
    break_end: str | None = None,
) -> ShiftSchema:
    return ShiftSchema(
        pay_rate=pay_rate,
        shift_start=datetime.fromisoformat(start),
        shift_end=datetime.fromisoformat(end),
        overtime_end=datetime.fromisoformat(overtime_end) if overtime_end else None,
        break_window=BreakWindow(
            break_start=datetime.fromisoformat(break_start),
            break_end=datetime.fromisoformat(break_end),
        )
        if break_start and break_end
        else None,
    )


def _single(shifts) -> DaySummary:
    """Run calculator and return the single result."""
    results = calculate_pay(shifts)
    assert len(results["pay_summaries"]) == 1
    return results["pay_summaries"][0]


# --- ShiftSchema Validation ---


class TestShiftValidation:
    def test_end_before_start_raises(self):
        with pytest.raises(ValueError, match="shift_end must be after shift_start"):
            _make_shift("2025-01-13T10:00", "2025-01-13T08:00")

    def test_overtime_end_before_shift_end_raises(self):
        with pytest.raises(ValueError, match="overtime_end must be after shift_end"):
            _make_shift(
                "2025-01-13T08:00", "2025-01-13T16:00", overtime_end="2025-01-13T15:00"
            )

    def test_break_outside_shift_raises(self):
        with pytest.raises(
            ValueError, match="Break times must be within shift and overtime period"
        ):
            _make_shift(
                "2025-01-13T08:00",
                "2025-01-13T16:00",
                break_start="2025-01-13T07:00",
                break_end="2025-01-13T07:30",
            )

    def test_break_end_before_start_raises(self):
        with pytest.raises(ValueError, match="break_end must be after break_start"):
            _make_shift(
                "2025-01-13T08:00",
                "2025-01-13T16:00",
                break_start="2025-01-13T13:00",
                break_end="2025-01-13T12:00",
            )

    def test_zero_pay_rate_raises(self):
        with pytest.raises(
            ValueError, match="pay_rate must be positive, you are not a slave!"
        ):
            _make_shift("2025-01-13T08:00", "2025-01-13T16:00", pay_rate=0)

    def test_negative_pay_rate_raises(self):
        with pytest.raises(
            ValueError, match="pay_rate must be positive, you are not a slave!"
        ):
            _make_shift("2025-01-13T08:00", "2025-01-13T16:00", pay_rate=-10)


# --- Basic Pay (Weekday, no extras) ---
# 2025-01-13 is a Monday


class TestBasePay:
    def test_simple_8_hour_shift(self):
        # 8hrs * 1.0 * $25 = $200
        summary = _single([_make_shift("2025-01-13T08:00", "2025-01-13T16:00")])
        assert summary.hours_worked == 8.0
        assert summary.base_hours == 8.0
        assert summary.base_pay_multiplier == DEFAULT_MULTIPLIER
        assert summary.base_total == 200.0
        assert summary.day_total == 200.0

    def test_shift_with_break(self):
        # 8hrs shift - 0.5hr break = 7.5hrs * 1.0 * $25 = $187.50
        summary = _single(
            [
                _make_shift(
                    "2025-01-13T08:00",
                    "2025-01-13T16:00",
                    break_start="2025-01-13T12:00",
                    break_end="2025-01-13T12:30",
                )
            ]
        )
        assert summary.hours_worked == 7.5
        assert summary.base_hours == 7.5
        assert summary.base_total == 187.50
        assert summary.day_total == 187.50

    def test_empty_input(self):
        results = calculate_pay([])
        assert results["pay_summaries"] == []
        assert results["total_hours"] == 0
        assert results["total_pay"] == 0


# --- Weekend Pay ---
# 2026-01-31 is a Saturday, 2026-02-01 is a Sunday


class TestWeekendPay:
    def test_saturday(self):
        # 8hrs * 1.25 * $25 = $250
        summary = _single([_make_shift("2026-01-31T08:00", "2026-01-31T16:00")])
        assert summary.day_type == "Saturday"
        assert summary.base_pay_multiplier == SATURDAY_MULTIPLIER
        assert summary.base_total == 250.0

    def test_sunday(self):
        # 8hrs * 1.5 * $25 = $300
        summary = _single([_make_shift("2026-02-01T08:00", "2026-02-01T16:00")])
        assert summary.day_type == "Sunday"
        assert summary.base_pay_multiplier == SUNDAY_MULTIPLIER
        assert summary.base_total == 300.0


# --- Holiday Pay ---


class TestHolidayPay:
    def test_nsw_holiday_detected(self):
        # 2025-01-01 is New Year's Day
        summary = _single([_make_shift("2025-01-01T08:00", "2025-01-01T16:00")])
        assert summary.day_type == "New Year's Day"
        assert summary.base_pay_multiplier == HOLIDAY_MULTIPLIER
        # 8hrs * 2.0 * $25 = $400
        assert summary.base_total == 400.0

    def test_holiday_on_sunday_uses_holiday_rate(self):
        # If a holiday falls on a Sunday, holiday rate takes priority
        # Use 2026's Easter Sunday (2026-04-05)
        summary = _single(
            [_make_shift("2026-04-05T08:00", "2026-04-05T16:00")]
        )  # Easter Sunday
        assert summary.day_type == "Easter Sunday"
        assert summary.base_pay_multiplier == HOLIDAY_MULTIPLIER


# --- Evening Pay ---
# Evening window is 17:00–21:00


class TestEveningPay:
    def test_partial_evening_overlap(self):
        # 1hr before evening window, 3hrs in evening window
        # base: 1hr * 1.0 * $25 = $25
        # evening: 3hrs * 1.15 * $25 = $86.25
        # Total: $111.25
        summary = _single([_make_shift("2025-01-13T17:00", "2025-01-13T21:00")])
        assert summary.base_hours == 1.0
        assert summary.base_total == 25.0
        assert summary.evening_hours == 3.0
        assert summary.evening_total == 86.25
        assert summary.day_total == 111.25

    def test_full_evening_overlap(self):
        # Entire shift within evening window (18:00–21:00)
        # base: 0hrs
        # evening: 3hrs * 1.15 * $25 = $86.25
        # Total: $86.25
        summary = _single([_make_shift("2025-01-13T18:00", "2025-01-13T21:00")])
        assert summary.base_hours == 0.0
        assert summary.base_total == 0.0
        assert summary.evening_hours == 3.0
        assert summary.evening_total == 86.25
        assert summary.day_total == 86.25

    def test_break_during_evening_and_day(self):
        # 15:00 - 21:00, break 17:45 - 18:15
        # Base: 3hrs (18:00 - 15:00) - 0.25hr break = 2.75hrs * 1.0 * $25 = $68.75
        # Evening: 3hrs (21:00 - 18:00) - 0.25hr break = 2.75hrs * 1.15 * $25 = $79.06
        # Total: $147.81
        summary = _single(
            [
                _make_shift(
                    "2025-01-13T15:00",
                    "2025-01-13T21:00",
                    break_start="2025-01-13T17:45",
                    break_end="2025-01-13T18:15",
                )
            ]
        )
        assert summary.base_hours == 2.75
        assert summary.base_total == 68.75
        assert summary.evening_hours == 2.75
        assert summary.evening_total == 79.06
        assert summary.day_total == 147.81

    def test_no_evening_overlap(self):
        # Shift entirely before evening window
        summary = _single([_make_shift("2025-01-13T08:00", "2025-01-13T16:00")])
        assert summary.evening_hours == 0.0
        assert summary.evening_total == 0.0


# --- Overtime Pay ---


class TestOvertimePay:
    def test_overtime_hours_calculated(self):
        # Shift 08:00–16:00, overtime until 18:00 = 2hrs OT
        # base: 8hrs * $25 = $200
        # overtime: 2hrs * 2.0 * $25 = $100
        summary = _single(
            [
                _make_shift(
                    "2025-01-13T08:00",
                    "2025-01-13T16:00",
                    overtime_end="2025-01-13T18:00",
                )
            ]
        )
        assert summary.overtime_hours == 2.0
        assert summary.overtime_total == 100.0
        assert summary.day_total == 300.0

    def test_no_overtime(self):
        summary = _single([_make_shift("2025-01-13T08:00", "2025-01-13T16:00")])
        assert summary.overtime_hours == 0.0
        assert summary.overtime_total == 0.0


# --- Combined / Edge Cases ---


class TestCombined:
    def test_saturday_evening_and_overtime(self):
        # Saturday 15:00–19:00, overtime until 20:00
        # base: 4hrs (15:00–19:00) * 1.25 * $25 = $125.00
        # evening: 0 BECAUSE Saturday multiplier prioritizes over evening multiplier
        # overtime: 1hr (19:00–20:00) * 2.0 * $25 = $50.00
        # Total: $172.50
        summary = _single(
            [
                _make_shift(
                    "2025-01-18T15:00",
                    "2025-01-18T19:00",
                    overtime_end="2025-01-18T20:00",
                )
            ]
        )
        assert summary.day_type == "Saturday"
        assert summary.base_total == 125.00
        assert summary.evening_total == 0.0
        assert summary.overtime_total == 50.00
        assert summary.day_total == 175.00

    def test_multiple_shifts_returns_multiple_summaries(self):
        # Monday 08:00–16:00 and Tuesday 09:00–17:00
        # Each shift: 8hrs * $25 = $200
        # Total: $400
        shifts = [
            _make_shift("2025-01-13T08:00", "2025-01-13T16:00"),  # Monday
            _make_shift("2025-01-14T09:00", "2025-01-14T17:00"),  # Tuesday
        ]
        results = calculate_pay(shifts)
        assert len(results["pay_summaries"]) == 2
        assert results["total_hours"] == 16.0
        assert results["total_pay"] == 400.0

    def test_shift_with_break_and_overtime(self):
        # Monday 08:00–16:00, break 12:00–12:30, OT until 17:00
        # hours_worked: 8hrs - 0.5hr break = 7.5hrs
        # base: 7.5hrs * $25 = $187.50
        # overtime: 1hr * 1.5 * $25 = $37.50
        summary = _single(
            [
                _make_shift(
                    "2026-02-02T08:00",
                    "2026-02-02T16:00",
                    overtime_end="2026-02-02T17:00",
                    break_start="2026-02-02T12:00",
                    break_end="2026-02-02T12:30",
                )
            ]
        )
        assert summary.hours_worked == 7.5
        assert summary.base_total == 187.50
        assert summary.overtime_total == 50.00
        assert summary.day_total == 237.50
