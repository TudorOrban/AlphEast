
from enum import Enum


class Interval(Enum):
    DAILY = "1d"
    HOURLY = "1h"
    MINUTE_30 = "30m"
    MINUTE_15 = "15m"
    MINUTE_5 = "5m"
    MINUTE_1 = "1m"

    def __str__(self):
        return self.value