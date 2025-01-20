from datetime import datetime
from ring_buffer import Ringbuffer
import math


class RingbufferTimePrice(Ringbuffer[tuple[datetime, float]]):
    HIGH = 0
    LOW = 1
    BOTH = -1

    def __init__(self, period: int, high_low: int = BOTH):
        """
        Initialize the RingbufferTimePrice with the given period and mode (High, Low, or Both).
        """
        super().__init__(period)
        self._quote_sum: float = 0.0
        self._highest: tuple[datetime, float] = (datetime.min, -math.inf)
        self._lowest: tuple[datetime, float] = (datetime.min, math.inf)
        self._high_low: int = high_low

    @property
    def lowest_value(self) -> tuple[datetime, float]:
        """
        Get the lowest value in the buffer.
        """
        return self._lowest

    @property
    def highest_value(self) -> tuple[datetime, float]:
        """
        Get the highest value in the buffer.
        """
        return self._highest

    def add(self, item: tuple[datetime, float]):
        """
        Add a new time-price tuple to the buffer.
        """
        if math.isnan(item[1]):
            return

        _, fallout = self.add_with_details(item, out_ndx=True, out_fallout=True)
        self._quote_sum += item[1]

        if self._is_fallout_valid:
            self._quote_sum -= fallout[1]

            # If old extremum has fallen out, find a new one
            extrema = None
            if self._high_low != self.LOW and fallout[1] == self._highest[1]:
                extrema = self.get_extrema()
                self._highest = extrema[self.HIGH]

            if self._high_low != self.HIGH and fallout[1] == self._lowest[1]:
                if extrema is None:
                    extrema = self.get_extrema()
                self._lowest = extrema[self.LOW]

        # Update extrema
        if item[1] > self._highest[1]:
            self._highest = item

        if item[1] < self._lowest[1]:
            self._lowest = item

    def get_average(self) -> float:
        """
        Get the average value of the prices in the buffer.
        """
        return self._quote_sum / self._count

    def get_extrema(self, count: int = 0, start_ndx: int = 0) -> list[tuple[datetime, float]]:
        """
        Get the extrema (highest and lowest values) over the specified range.
        """
        if count is 0:
            count = self._count

        extrema = [self._buffer[(self._position - count) % self._size]] * 2  # Start with the first value
        for i in range(count):
            ndx = (self._position - count + i) % self._size
            cmp_val = self._buffer[ndx]

            # Update high
            if cmp_val[1] > extrema[self.HIGH][1]:  # type: ignore
                extrema[self.HIGH] = cmp_val

            # Update low
            if cmp_val[1] < extrema[self.LOW][1]:  # type: ignore
                extrema[self.LOW] = cmp_val

        return extrema  # type: ignore
