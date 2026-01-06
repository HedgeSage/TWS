import random
import time
from quant_system.core.types import TickData, Exchange

class MarketDataGenerator:
    """
    模拟行情生成器 (Random Walk)
    """
    def __init__(self):
        self._prices = {}
        self._volatility = 0.0002 # 0.02% 波动

    def get_tick(self, symbol: str) -> TickData:
        # 初始化价格
        if symbol not in self._prices:
            self._prices[symbol] = 10000.0 if "BTC" in symbol else 2000.0
            
        # 随机游走
        current = self._prices[symbol]
        change = current * self._volatility * random.choice([-1, 1, 0.5, -0.5])
        new_price = current + change
        self._prices[symbol] = new_price
        
        # 构造 Tick
        return TickData(
            symbol=symbol,
            exchange=Exchange.MOCK,
            timestamp=time.time(),
            last_price=new_price,
            volume=random.uniform(0.1, 5.0),
            bid_price_1=new_price - 0.5,
            ask_price_1=new_price + 0.5,
            funding_rate=0.0001
        )
