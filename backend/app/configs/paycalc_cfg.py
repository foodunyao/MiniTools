from datetime import time

# Config
EVENING_START = time(18, 0)
EVENING_END = time(23, 59, 59) # Just going to assume Miniso always closes before midnight

DEFAULT_MULTIPLIER = 1.0
SATURDAY_MULTIPLIER = 1.25
SUNDAY_MULTIPLIER = 1.5
HOLIDAY_MULTIPLIER = 2.0
EVENING_MULTIPLIER = 1.15
OVERTIME_MULTIPLIER = 2.0