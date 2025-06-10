
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional

from alpheast.data.price_bar_client import PriceBarClient
from alpheast.models.price_bar import PriceBar


class DataSourceType(Enum):
    DIRECT = "DIRECT"
    STD_CLIENT = "STD_CLIENT"
    CUSTOM_CLIENT = "CUSTOM_CLIENT"

class SupportedProvider(Enum):
    ALPHA_VANTAGE = "ALPHA_VANTAGE"

@dataclass
class DataSource:
    type: DataSourceType
    price_bar_data: Optional[Dict[str, List[PriceBar]]] = None # Symbol -> its price data
    api_key: Optional[str] = None
    provider: Optional[SupportedProvider] = None
    custom_client: Optional[PriceBarClient] = None