
from collections import deque
from decimal import Decimal
import logging
from typing import Any
from alpheast.events.event import MarketEvent
from alpheast.models.signal import Signal
from alpheast.strategy.base_strategy import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    A Relative Strength Index (RSI) trading strategy.

    Generates BUY/SELL signals based on RSI crossing oversold/overbought thresholds.

    :param symbol: The financial instrument symbol this strategy will trade.
    :param rsi_period: The period over which to calculate the RSI. (e.g., 14 for typical RSI)
    :param oversold_threshold: The RSI value below which an asset is considered oversold (e.g., 30).
    :param overbought_threshold: The RSI value above which an asset is considered overbought (e.g., 70).
    :param kwargs: Arbitrary keyword arguments passed to the base strategy.
    """
    def __init__(
        self,
        symbol: str,
        rsi_period: int = 14,
        oversold_threshold: Decimal = Decimal("30"),
        overbought_threshold: Decimal = Decimal("70"),
        **kwargs: Any
    ):
        super().__init__(symbol, **kwargs)

        if not (1 <= rsi_period <= 200):
            raise ValueError("RSI period must be a reasonable positive integer.")
        if not (0 <= oversold_threshold < overbought_threshold <= 100):
            raise ValueError("Oversold threshold must be < overbought threshold and within [0, 100].")

        self.rsi_period = rsi_period
        self.oversold_threshold = oversold_threshold
        self.overbought_threshold = overbought_threshold

        self._closes_history = deque(maxlen=rsi_period + 1)
        self._has_position = False
        self._gains = deque(maxlen=rsi_period)
        self._losses = deque(maxlen=rsi_period)
        self._avg_gain = Decimal("0")
        self._avg_loss = Decimal("0")

        logging.info(
            f"RSIStrategy initialized for {self.symbol} with period={rsi_period}, "
            f"oversold={oversold_threshold}, overbought={overbought_threshold}"
        )

    def on_market_event(self, event: MarketEvent):
        """
        Handles incoming market events to update RSI and generate trading signals.

        :param event: The MarketEvent containing new market data.
        """
        if event.symbol != self.symbol:
            return
        
        current_close = Decimal(str(event.data["close"]))
        self._closes_history.append(current_close)

        if len(self._closes_history) <= 1:
            logging.debug(f"Not enough history for {self.symbol} on {event.timestamp.date()}. Need at least 2 closes.")
            return
        
        price_diff = self._closes_history[-1] - self._closes_history[-2]
        current_gain = price_diff if price_diff > 0 else Decimal("0")
        current_loss = -price_diff if price_diff < 0 else Decimal("0")

        self._update_avg_gain_loss(current_gain, current_loss)

        if len(self._gains) < self.rsi_period:
            logging.debug(f"Not enough history to calculate RSI for {self.symbol} on {event.timestamp.date()}. "
                          f"Need {self.rsi_period} full periods for initial average.")
            return
        
        rsi = self._calculate_rsi()

        if rsi < self.oversold_threshold and not self._has_position:
            self._put_signal_event(event.timestamp, Signal.BUY)
            self._has_position = True
            logging.info(f"RSI BUY signal for {self.symbol} at {event.timestamp.date()}, RSI: {rsi:.2f}")
        elif rsi > self.overbought_threshold and self._has_position:
            self._put_signal_event(event.timestamp, Signal.SELL)
            self._has_position = False
            logging.info(f"RSI SELL signal for {self.symbol} at {event.timestamp.date()}, RSI: {rsi:.2f}")
        else:
            pass

    def _calculate_rsi(self) -> Decimal:
        """Calculates the Relative Strength Index (RSI)."""
        if len(self._gains) == 0 or len(self._losses) == 0:
            return Decimal("50")

        rs = self._avg_gain / self._avg_loss if self._avg_loss != Decimal("0") else Decimal("999999")
        rsi = Decimal("100") - (Decimal("100") / (Decimal("1") + rs))
        return rsi
    
    def _update_avg_gain_loss(self, current_gain: Decimal, current_loss: Decimal):
        """Updates average gain and loss for RSI calculation."""
        if len(self._gains) < self.rsi_period:
            self._gains.append(current_gain)
            self._losses.append(current_loss)
            self._avg_gain = sum(self._gains, Decimal("0")) / Decimal(len(self._gains))
            self._avg_loss = sum(self._losses, Decimal("0")) / Decimal(len(self._losses))
        else:
            self._avg_gain = ((self._avg_gain * (self.rsi_period - 1)) + current_gain) / self.rsi_period
            self._avg_loss = ((self._avg_loss * (self.rsi_period - 1)) + current_loss) / self.rsi_period