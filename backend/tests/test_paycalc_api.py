from typing import Dict, Any
from app.configs.paycalc_cfg import (
    DEFAULT_MULTIPLIER,
    OVERTIME_MULTIPLIER,
    SATURDAY_MULTIPLIER,
    SUNDAY_MULTIPLIER,
    HOLIDAY_MULTIPLIER,
    EVENING_MULTIPLIER,
)


def _make_shift(
    start: str,
    end: str,
    pay_rate: float = 25.0,
    overtime_end: str | None = None,
    break_start: str | None = None,
    break_end: str | None = None,
) -> Dict[str, Any]:
    """Helper to create a shift JSON dict for testing API endpoints."""
    return {
        "pay_rate": pay_rate,
        "shift_start": start,
        "shift_end": end,
        "overtime_end": overtime_end,
        "break_window": {
            "break_start": break_start,
            "break_end": break_end,
        }
        if break_start and break_end
        else None,
    }


class TestShiftValidation:
    def test_end_before_start_raises(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2024-01-01T10:00:00",
                    end="2024-01-01T09:00:00",
                )
            ],
        )
        assert response.status_code == 422
        assert "Value error, shift_end must be after shift_start" in response.text

    def test_overtime_end_before_shift_end_raises(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2024-01-01T09:00:00",
                    end="2024-01-01T17:00:00",
                    overtime_end="2024-01-01T16:00:00",
                )
            ],
        )
        assert response.status_code == 422
        assert "Value error, overtime_end must be after shift_end" in response.text

    def test_break_outside_shift_raises(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T08:00",
                    end="2025-01-13T16:00",
                    break_start="2025-01-13T07:00",
                    break_end="2025-01-13T07:30",
                )
            ],
        )
        assert response.status_code == 422
        assert (
            "Value error, Break times must be within shift and overtime period"
            in response.text
        )

    def test_break_end_before_break_start_raises(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T08:00",
                    end="2025-01-13T16:00",
                    break_start="2025-01-13T12:00",
                    break_end="2025-01-13T11:30",
                )
            ],
        )
        assert response.status_code == 422
        assert "Value error, break_end must be after break_start" in response.text

    def test_zero_pay_rate_raises(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T08:00",
                    end="2025-01-13T16:00",
                    pay_rate=0.0,
                )
            ],
        )
        assert response.status_code == 422
        assert (
            "Value error, pay_rate must be positive, you are not a slave!"
            in response.text
        )

    def test_negative_pay_rate_raises(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T08:00",
                    end="2025-01-13T16:00",
                    pay_rate=-15.0,
                )
            ],
        )
        assert response.status_code == 422
        assert (
            "Value error, pay_rate must be positive, you are not a slave!"
            in response.text
        )


class TestBasePay:
    def test_simple_8_hour_shift(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T08:00",
                    end="2025-01-13T16:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["hours_worked"] == 8.0
        assert shift["base_hours"] == 8.0
        assert shift["base_pay_multiplier"] == DEFAULT_MULTIPLIER
        assert shift["base_total"] == 200.0
        assert shift["day_total"] == 200.0

        assert day_summary["total_hours"] == 8.0
        assert day_summary["total_pay"] == 200.0

    def test_shift_with_break(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T08:00",
                    end="2025-01-13T16:00",
                    break_start="2025-01-13T12:00",
                    break_end="2025-01-13T12:30",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["hours_worked"] == 7.5
        assert shift["base_hours"] == 7.5
        assert shift["base_pay_multiplier"] == DEFAULT_MULTIPLIER
        assert shift["base_total"] == 187.50
        assert shift["day_total"] == 187.50

        assert day_summary["total_hours"] == 7.5
        assert day_summary["total_pay"] == 187.50

    def test_empty_input(self, client):
        response = client.post("/paycalc/calc", json=[])
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 0
        assert day_summary["total_hours"] == 0.0
        assert day_summary["total_pay"] == 0.0


class TestWeekendPay:
    def test_saturday(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2026-01-31T08:00",
                    end="2026-01-31T16:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["day_type"] == "Saturday"
        assert shift["hours_worked"] == 8.0
        assert shift["base_hours"] == 8.0
        assert shift["base_pay_multiplier"] == SATURDAY_MULTIPLIER
        assert shift["base_total"] == 200.0 * SATURDAY_MULTIPLIER
        assert shift["day_total"] == 200.0 * SATURDAY_MULTIPLIER

        assert day_summary["total_hours"] == 8.0
        assert day_summary["total_pay"] == 200.0 * SATURDAY_MULTIPLIER

    def test_sunday(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2026-02-01T08:00",
                    end="2026-02-01T16:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["day_type"] == "Sunday"
        assert shift["hours_worked"] == 8.0
        assert shift["base_hours"] == 8.0
        assert shift["base_pay_multiplier"] == SUNDAY_MULTIPLIER
        assert shift["base_total"] == 200.0 * SUNDAY_MULTIPLIER
        assert shift["day_total"] == 200.0 * SUNDAY_MULTIPLIER

        assert day_summary["total_hours"] == 8.0
        assert day_summary["total_pay"] == 200.0 * SUNDAY_MULTIPLIER


class TestHolidayPay:
    def test_nsw_holiday_detected(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-01T08:00",
                    end="2025-01-01T16:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["day_type"] == "New Year's Day"
        assert shift["hours_worked"] == 8.0
        assert shift["base_hours"] == 8.0
        assert shift["base_pay_multiplier"] == HOLIDAY_MULTIPLIER
        assert shift["base_total"] == 200.0 * HOLIDAY_MULTIPLIER
        assert shift["day_total"] == 200.0 * HOLIDAY_MULTIPLIER

        assert day_summary["total_hours"] == 8.0
        assert day_summary["total_pay"] == 200.0 * HOLIDAY_MULTIPLIER

    def test_holiday_on_sunday_uses_holiday_rate(self, client):
        # If a holiday falls on a Sunday, holiday rate takes priority
        # Using 2026 Easter Sunday (2026-04-05)
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2026-04-05T08:00",
                    end="2026-04-05T16:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["day_type"] == "Easter Sunday"
        assert shift["hours_worked"] == 8.0
        assert shift["base_hours"] == 8.0
        assert shift["base_pay_multiplier"] == HOLIDAY_MULTIPLIER
        assert shift["base_total"] == 200.0 * HOLIDAY_MULTIPLIER
        assert shift["day_total"] == 200.0 * HOLIDAY_MULTIPLIER

        assert day_summary["total_hours"] == 8.0
        assert day_summary["total_pay"] == 200.0 * HOLIDAY_MULTIPLIER


class TestEveningPay:
    def test_partial_evening_overlap(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T17:00",
                    end="2025-01-13T21:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["day_type"] == "Weekday"
        assert shift["hours_worked"] == 4.0
        assert shift["base_hours"] == 1.0
        assert shift["base_pay_multiplier"] == DEFAULT_MULTIPLIER
        assert shift["base_total"] == 25.0 * DEFAULT_MULTIPLIER
        assert shift["evening_hours"] == 3.0
        assert shift["evening_pay_multiplier"] == EVENING_MULTIPLIER
        assert shift["evening_total"] == 75.0 * EVENING_MULTIPLIER
        assert shift["day_total"] == (25.0 * DEFAULT_MULTIPLIER) + (
            75.0 * EVENING_MULTIPLIER
        )

        assert day_summary["total_hours"] == 4.0
        assert day_summary["total_pay"] == (25.0 * DEFAULT_MULTIPLIER) + (
            75.0 * EVENING_MULTIPLIER
        )

    def test_full_evening_overlap(self, client):
        # Entire shift within evening window (18:00 - 21:00)
        # Base: 0 hrs
        # Evening: 3hrs * EVENING_MULTIPLIER * pay_rate
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T18:00",
                    end="2025-01-13T21:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["base_hours"] == 0.0
        assert shift["base_total"] == 0.0
        assert shift["evening_hours"] == 3.0
        assert shift["evening_total"] == 75.0 * EVENING_MULTIPLIER
        assert shift["day_total"] == 75.0 * EVENING_MULTIPLIER

        assert day_summary["total_hours"] == 3.0
        assert day_summary["total_pay"] == 75.0 * EVENING_MULTIPLIER

    def test_break_during_evening_and_day(self, client):
        # 15:00 - 21:00, break 17:45 - 18:15
        # Base: 2.75 hrs (15:00-17:45)
        # Evening: 2.75 hrs (18:15-21:00)
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T15:00",
                    end="2025-01-13T21:00",
                    break_start="2025-01-13T17:45",
                    break_end="2025-01-13T18:15",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["base_hours"] == 2.75
        assert shift["base_total"] == round(2.75 * DEFAULT_MULTIPLIER * 25.0, 2)
        assert shift["evening_hours"] == 2.75
        assert shift["evening_total"] == round(2.75 * EVENING_MULTIPLIER * 25.0, 2)
        assert shift["day_total"] == round(
            (2.75 * DEFAULT_MULTIPLIER * 25.0) + (2.75 * EVENING_MULTIPLIER * 25.0), 2
        )

        assert day_summary["total_hours"] == 5.5
        assert day_summary["total_pay"] == round(
            (2.75 * DEFAULT_MULTIPLIER * 25.0) + (2.75 * EVENING_MULTIPLIER * 25.0), 2
        )

    def test_no_evening_overlap(self, client):
        # Shift entirely outside evening window
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T09:00",
                    end="2025-01-13T17:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["base_hours"] == 8.0
        assert shift["base_total"] == 200.0
        assert shift["evening_hours"] == 0.0
        assert shift["evening_total"] == 0.0
        assert shift["day_total"] == 200.0

        assert day_summary["total_hours"] == 8.0
        assert day_summary["total_pay"] == 200.0


class TestOvertimePay:
    def test_overtime_hours_calculated(self, client):
        # Shift 08:00-16:00, overtime until 18:00 = 2hrs OT
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T08:00",
                    end="2025-01-13T16:00",
                    overtime_end="2025-01-13T18:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["base_hours"] == 8.0
        assert shift["overtime_hours"] == 2.0
        assert shift["overtime_total"] == 50.0 * OVERTIME_MULTIPLIER
        assert shift["day_total"] == (200.0) + (50.0 * OVERTIME_MULTIPLIER)

    def test_no_overtime(self, client):
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T08:00",
                    end="2025-01-13T16:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["base_hours"] == 8.0
        assert shift["overtime_hours"] == 0.0
        assert shift["overtime_total"] == 0.0
        assert shift["day_total"] == 200.0


class TestCombined:
    def test_saturday_evening_and_overtime(self, client):
        # Saturday 15:00-19:00, overtime until 20:00
        # Base 4 hrs (15:00-19:00)
        # Evening: 0hrs because Saturday Multiplier takes priority
        # Overtime: 1hr (19:00-20:00)
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2026-01-31T15:00",
                    end="2026-01-31T19:00",
                    overtime_end="2026-01-31T20:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["day_type"] == "Saturday"
        assert shift["base_hours"] == 4.0
        assert shift["base_pay_multiplier"] == SATURDAY_MULTIPLIER
        assert shift["base_total"] == 100.0 * SATURDAY_MULTIPLIER
        assert shift["evening_hours"] == 0.0
        assert shift["evening_total"] == 0.0
        assert shift["overtime_hours"] == 1.0
        assert shift["overtime_total"] == 25.0 * OVERTIME_MULTIPLIER
        assert shift["day_total"] == (100.0 * SATURDAY_MULTIPLIER) + (
            25.0 * OVERTIME_MULTIPLIER
        )

        assert day_summary["total_hours"] == 5.0
        assert day_summary["total_pay"] == (100.0 * SATURDAY_MULTIPLIER) + (
            25.0 * OVERTIME_MULTIPLIER
        )

    def test_multiple_shifts_returns_multiple_summaries(self, client):
        # Monday 08:00-16:00 and Tuesday 09:00-17:00
        # Each shift: 8hrs
        shifts = [
            _make_shift(
                start="2025-01-13T08:00",
                end="2025-01-13T16:00",
            ),
            _make_shift(
                start="2025-01-14T09:00",
                end="2025-01-14T17:00",
            ),
        ]

        response = client.post("/paycalc/calc", json=shifts)
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 2

        assert day_summary["total_hours"] == 16.0
        assert day_summary["total_pay"] == 400.0

    def test_shift_with_break_and_overtime(self, client):
        # Monday 08:00-16:00, break 12:00-12:30, OT till 17:00
        # Base 7.5hrs (8:00-16:00 minus 0.5hr break)
        # Overtime: 1hr (16:00-17:00)
        response = client.post(
            "/paycalc/calc",
            json=[
                _make_shift(
                    start="2025-01-13T08:00",
                    end="2025-01-13T16:00",
                    break_start="2025-01-13T12:00",
                    break_end="2025-01-13T12:30",
                    overtime_end="2025-01-13T17:00",
                )
            ],
        )
        assert response.status_code == 200
        day_summary = response.json()
        assert len(day_summary["pay_summaries"]) == 1

        shift = day_summary["pay_summaries"][0]
        assert shift["base_hours"] == 7.5
        assert shift["base_total"] == 187.50
        assert shift["overtime_hours"] == 1.0
        assert shift["overtime_total"] == 25.0 * OVERTIME_MULTIPLIER
        assert shift["day_total"] == (187.50) + (25.0 * OVERTIME_MULTIPLIER)
        assert day_summary["total_hours"] == 8.5
        assert day_summary["total_pay"] == (187.50) + (25.0 * OVERTIME_MULTIPLIER)
