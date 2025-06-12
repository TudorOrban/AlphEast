from collections import deque
from decimal import Decimal
import logging
from typing import Any, Optional

from alpheast.events.event import MarketEvent
from alpheast.strategy.base_strategy import BaseStrategy
from alpheast.models.signal import Signal


class MACDStrategy(BaseStrategy):
    """
    A Moving Average Convergence Divergence (MACD) trading strategy.

    Generates BUY signals when the MACD line crosses above its Signal line.
    Generates SELL signals when the MACD line crosses below its Signal line.

    :param symbol: The financial instrument symbol this strategy will trade.
    :param fast_period: The period for the fast Exponential Moving Average (EMA) (e.g., 12).
    :param slow_period: The period for the slow Exponential Moving Average (EMA) (e.g., 26).
    :param signal_period: The period for the EMA of the MACD line (Signal Line) (e.g., 9).
    :param kwargs: Arbitrary keyword arguments passed to the base strategy.
    """
    def __init__(self, symbol: str, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9, **kwargs: Any):
        super().__init__(symbol, **kwargs)
        if not (1 <= fast_period < slow_period):
            raise ValueError("Fast period must be less than slow period and positive.")
        if signal_period <= 0:
            raise ValueError("Signal period must be positive.")

        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period

        self._closes_history = deque(maxlen=self.slow_period)
        self._macd_history = deque(maxlen=self.signal_period) 
        
        self._prev_fast_ema: Optional[Decimal] = None
        self._prev_slow_ema: Optional[Decimal] = None
        self._prev_signal_line: Optional[Decimal] = None

        self._has_position = False

        logging.info(
            f"MACDStrategy initialized for {self.symbol} with Fast={fast_period}, "
            f"Slow={slow_period}, Signal={signal_period}"
        )

    def _calculate_ema(self, prices: deque, period: int, prev_ema: Optional[Decimal]) -> Decimal:
        """
        Calculates the Exponential Moving Average (EMA).
        Uses simple average for the initial EMA.
        """
        if not prices:
            return Decimal("0")

        # Smoothing factor
        k = Decimal("2") / Decimal(period + 1)

        if prev_ema is None:
            if len(prices) < period:
                return Decimal("0")
            initial_sma = sum(list(prices)[-period:], Decimal("0")) / Decimal(period)
            return initial_sma
        else:
            # EMA formula: (Current_Price - Previous_EMA) * K + Previous_EMA
            return (prices[-1] - prev_ema) * k + prev_ema

    def on_market_event(self, event: MarketEvent):
        """
        Handles incoming market events to update MACD indicator and generate trading signals.

        :param event: The MarketEvent containing new market data.
        """
        if event.symbol != self.symbol:
            return
        
        current_close = Decimal(str(event.data["close"]))
        self._closes_history.append(current_close)

        if len(self._closes_history) < self.slow_period:
            logging.debug(f"Not enough history for {self.symbol} on {event.timestamp.date()}. Need {self.slow_period} closes for initial MACD. Have {len(self._closes_history)}.")
            return

        # Calculate Fast and Slow EMA
        current_fast_ema = self._calculate_ema(self._closes_history, self.fast_period, self._prev_fast_ema)
        if current_fast_ema == Decimal("0") and len(self._closes_history) < self.fast_period:
            return 
        
        current_slow_ema = self._calculate_ema(self._closes_history, self.slow_period, self._prev_slow_ema)
        if current_slow_ema == Decimal("0") and len(self._closes_history) < self.slow_period:
            return 
        
        # Update previous EMAs for next iteration
        self._prev_fast_ema = current_fast_ema
        self._prev_slow_ema = current_slow_ema

        # Calculate MACD Line
        macd_line = current_fast_ema - current_slow_ema
        self._macd_history.append(macd_line)

        if len(self._macd_history) < self.signal_period:
            logging.debug(f"Not enough MACD history for {self.symbol} on {event.timestamp.date()}. Need {self.signal_period} MACD values for initial Signal Line.")
            return
        signal_line = self._calculate_ema(self._macd_history, self.signal_period, self._prev_signal_line)
        if signal_line == Decimal("0") and len(self._macd_history) < self.signal_period:
            return
        
        self._prev_signal_line = signal_line

        if macd_line > signal_line and not self._has_position:
            self._put_signal_event(event.timestamp, Signal.BUY)
            self._has_position = True
            logging.info(
                f"MACD BUY signal for {self.symbol} at {event.timestamp.date()}. "
                f"MACD: {macd_line:.4f} > Signal: {signal_line:.4f}"
            )
        elif macd_line < signal_line and self._has_position:
            self._put_signal_event(event.timestamp, Signal.SELL)
            self._has_position = False
            logging.info(
                f"MACD SELL signal for {self.symbol} at {event.timestamp.date()}. "
                f"MACD: {macd_line:.4f} < Signal: {signal_line:.4f}"
            )
        else:
            pass