
from collections import deque
from decimal import Decimal
import logging
from typing import Any
from alpheast.events.event import MarketEvent
from alpheast.models.signal import Signal
from alpheast.strategy.base_strategy import BaseStrategy


class BollingerBandsStrategy(BaseStrategy):
    """
    A Bollinger Bands trading strategy.

    Generates BUY signals when the close price crosses below the lower band
    and SELL signals when it crosses above the upper band

    :param symbol: The financial instrument symbol this strategy will trade.
    :param bb_period: The period over which to calculate the Simple Moving Average (SMA) for the middle band. (e.g., 20)
    :param num_std_dev: The number of standard deviations for the upper and lower bands. (e.g., 2)
    :param kwargs: Arbitrary keyword arguments passed to the base strategy.
    """
    def __init__(self, symbol: str, bb_period: int = 20, num_std_dev: Decimal = Decimal("2"), **kwargs: Any):
        super().__init__(symbol, **kwargs)
        if bb_period <= 1:
            raise ValueError("Bollinger Bands period must be greater than 1.")
        if num_std_dev <= 0:
            raise ValueError("Number of standard deviations must be positive.")
        
        self.bb_period = bb_period
        self.num_std_dev = num_std_dev

        self._closes_history = deque(maxlen=self.bb_period)
        self._has_position = False

        logging.info(
            f"BollingerBandsStrategy initialized for {self.symbol} with period={bb_period}, "
            f"std_dev={num_std_dev}"
        )

    def on_market_event(self, event: MarketEvent):
        if event.symbol != self.symbol:
            return
        
        current_close = Decimal(str(event.data["close"]))
        self._closes_history.append(current_close)

        if len(self._closes_history) < self.bb_period:
            logging.debug(f"Not enough history for {self.symbol} on {event.timestamp.date()}. Need {self.bb_period} closes for BB calculation. Have {len(self._closes_history)}.")
            return
        if len(self._closes_history) < 2 and self.bb_period >= 2:
            logging.debug(f"Insufficient data points for standard deviation calculation for {self.symbol} on {event.timestamp.date()}. Need at least 2.")
            return

        middle_band = self._calculate_sma(self._closes_history)
        std_dev = self._calculate_std_dev(self._closes_history, middle_band)

        upper_band = middle_band + (std_dev * self.num_std_dev)
        lower_band = middle_band - (std_dev * self.num_std_dev)

        lower_band = max(Decimal("0"), lower_band)

        if current_close < lower_band and not self._has_position:
            self._put_signal_event(event.timestamp, Signal.BUY)
            self._has_position = True
            logging.info(
                f"BB BUY signal for {self.symbol} at {event.timestamp.date()}. "
                f"Close: {current_close:.2f} < Lower Band: {lower_band:.2f}"
            )
        elif current_close > upper_band and self._has_position:
            self._put_signal_event(event.timestamp, Signal.SELL)
            self._has_position = False
            logging.info(
                f"BB SELL signal for {self.symbol} at {event.timestamp.date()}. "
                f"Close: {current_close:.2f} > Upper Band: {upper_band:.2f}"
            )
        else:
            pass

    def _calculate_sma(self, prices: deque) -> Decimal:
        """Calculates the Simple Moving Average (SMA)."""
        if not prices:
            return Decimal("0")
        return sum(prices, Decimal("0")) / Decimal(len(prices))
    
    def _calculate_std_dev(self, prices: deque, sma: Decimal) -> Decimal:
        """Calculates the standard deviation."""
        if not prices or len(prices) < 2:
            return Decimal("0")
        variance = sum([(p - sma) ** 2 for p in prices], Decimal("0")) / Decimal(len(prices) - 1)
        return variance.sqrt()
