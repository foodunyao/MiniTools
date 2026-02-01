from pydantic import BaseModel, model_validator
from datetime import datetime
from typing import Optional, List
from app.configs.paycalc_cfg import *


class BreakWindow(BaseModel):
    break_start: datetime
    break_end: datetime

    @model_validator(mode='after')
    def validate_break(self) -> 'BreakWindow':
        if self.break_end <= self.break_start:
            raise ValueError("break_end must be after break_start")
        return self
    
class ShiftSchema(BaseModel):
    pay_rate: float
    shift_start: datetime
    shift_end: datetime
    overtime_end: Optional[datetime] = None
    break_window: Optional[BreakWindow] = None

    @model_validator(mode='after')
    def validate_times(self) -> 'ShiftSchema':
        if self.pay_rate <= 0.0:
            raise ValueError("pay_rate must be positive, you are not a slave!")

        if self.shift_end <= self.shift_start:
            raise ValueError("shift_end must be after shift_start")

        if self.overtime_end is not None and self.overtime_end <= self.shift_end:
            raise ValueError("overtime_end must be after shift_end")

        # Both break start/ends MUST be provided together or neither given AND must be within shift + overtime period
        if self.break_window is not None:
            if not (self.shift_start <= self.break_window.break_start < self.break_window.break_end <= (self.overtime_end or self.shift_end)):
                raise ValueError("Break times must be within shift and overtime period")

        return self

class DaySummary(BaseModel):
    date: datetime
    day_type: str # "Weekday", "Saturday", "Sunday", "Holiday"
    pay_rate: float

    base_hours: float # shift_end - shift_start - break_duration
    base_pay_multiplier: float # default / weekend 1.25 / holiday
    base_total: float # base_hours * base_multiplier  * pay rate
    
    evening_hours: Optional[float]
    evening_pay_multiplier: float = EVENING_MULTIPLIER
    evening_total: Optional[float] # evening_hours * evening_multiplier 

    overtime_hours: Optional[float]
    overtime_multiplier: float = OVERTIME_MULTIPLIER
    overtime_total: Optional[float]

    hours_worked: float
    day_total: float
