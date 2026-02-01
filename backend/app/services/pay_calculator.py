from datetime import datetime
from typing import Iterable, Any, List, Dict
from app.models.schemas.paycalc_schema import ShiftSchema, DaySummary
import holidays

# Config
from ..configs.paycalc_cfg import *

_nsw_holidays = holidays.country_holidays('AU', subdiv='NSW')

# Private helpers
def _duration_hours(start: datetime, end: datetime) -> float:
    return (end - start).total_seconds() / 3600.0

# CHecks how many hours overlap between two time ranges
def _overlap_hours(start1: datetime, end1: datetime, start2: datetime, end2: datetime) -> float:
    latest_start = max(start1, start2)
    earliest_end = min(end1, end2)
    if latest_start >= earliest_end:
        return 0.0
    return _duration_hours(latest_start, earliest_end)

def _get_evening_window(shift: ShiftSchema) -> tuple[datetime, datetime]:
    day = shift.shift_start.date()
    return (
        datetime.combine(day, EVENING_START),
        datetime.combine(day, EVENING_END)
    )

def _get_day_type(day: datetime) -> tuple[str, float]:
    # RETURN: (day_type_str, multiplier)
    # Order of priority is: Holiday > Sunday > Saturday > Weekday
    holiday_name = _nsw_holidays.get(day)

    # Conveniently gives the name of the holiday as well!
    if holiday_name:
        return holiday_name, HOLIDAY_MULTIPLIER
    
    weekday = day.weekday()
    if weekday == 5:
        return "Saturday", SATURDAY_MULTIPLIER
    elif weekday == 6:
        return "Sunday", SUNDAY_MULTIPLIER
    else:
        return "Weekday", DEFAULT_MULTIPLIER

# The big pay calulator
def calculate_pay(shifts: Iterable[ShiftSchema]) -> Dict[str, List[DaySummary]]:
    summaries = []
    
    for shift in shifts:
        day_type, base_multiplier = _get_day_type(shift.shift_start)

        break_hours = _duration_hours(shift.break_window.break_start, shift.break_window.break_end) if shift.break_window else 0.0

        total_shift_hours = _duration_hours(shift.shift_start, shift.shift_end)
        hours_worked = total_shift_hours - break_hours
        
        overtime_hours = _duration_hours(shift.shift_end, shift.overtime_end) if shift.overtime_end else 0.0
    
        evening_start, evening_end = _get_evening_window(shift)
        # Evening hours only occur on weekday shifts. Weekend/holiday shifts use their own multipliers and DON'T STACK
        evening_hours = _overlap_hours(shift.shift_start, shift.shift_end, evening_start, evening_end) if base_multiplier == DEFAULT_MULTIPLIER else 0.0

        # Subtract break overlap with evening hours
        if shift.break_window:
            evening_break_overlap = _overlap_hours(
                shift.break_window.break_start,
                shift.break_window.break_end,
                evening_start,
                evening_end
            )
            evening_hours -= evening_break_overlap
        
        base_hours = hours_worked - evening_hours

        base_total = round(base_hours * base_multiplier * shift.pay_rate, 2)
        evening_total = round(evening_hours * EVENING_MULTIPLIER * shift.pay_rate, 2)
        overtime_total = round(overtime_hours * OVERTIME_MULTIPLIER * shift.pay_rate, 2)
        day_total = round(base_total + evening_total + overtime_total, 2)

        summaries.append(DaySummary(
            date=shift.shift_start,
            day_type=day_type,
            pay_rate=shift.pay_rate,

            base_hours=round(base_hours, 2),
            base_pay_multiplier=base_multiplier,
            base_total=base_total,

            evening_hours=round(evening_hours, 2),
            evening_pay_multiplier=EVENING_MULTIPLIER,
            evening_total=evening_total,

            overtime_hours=round(overtime_hours, 2),
            overtime_multiplier=OVERTIME_MULTIPLIER,
            overtime_total=overtime_total,

            hours_worked=round(hours_worked, 2),
            day_total=day_total,
        ))
    
    total_hours = sum(s.hours_worked for s in summaries)
    total_pay = sum(s.day_total for s in summaries)
    return {
        "pay_summaries": summaries,
        "total_hours": total_hours,
        "total_pay": total_pay
    }