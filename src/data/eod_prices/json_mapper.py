
from typing import Any, Dict, List

from src.data.eod_prices.model import EODPrice


class EODPriceJsonMapper:

    @staticmethod
    def from_alpha_vantage_response(data: List[Dict[str, Any]]) -> List[EODPrice]:
        eod_prices: List[EODPrice] = []
        for item in data:
            try:
                eod_prices.append(
                    EODPrice(
                        time=item["time"],
                        symbol=item["symbol"],
                        open=item["open"],
                        high=item["high"],
                        low=item["low"],
                        close=item["close"],
                        volume=item["volume"]
                    )
                )
            except KeyError as ke:
                print(f"WARNING: Missing key when mapping EODPrice: {ke} in item: {item}")
            except Exception as e:
                print(f"ERROR: Failed to map EODPrice item: {item}. Error: {e}")
        return eod_prices
    
    @staticmethod
    def to_dict(eod_price: EODPrice) -> Dict[str, Any]:
        """
        Serializes an EODPrice entity back into a dictionary.
        """
        return {
            "time": eod_price.time,
            "symbol": eod_price.symbol,
            "open": float(eod_price.open),
            "high": float(eod_price.high),
            "low": float(eod_price.low),
            "close": float(eod_price.close),
            "volume": eod_price.volume
        }
    