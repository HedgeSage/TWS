from abc import ABC, abstractmethod
from typing import Deque, List
import collections

from quant_system.core.types import TickData

class BaseSignal(ABC):
    """
    信号基类 (Alpha Layer)
    职责: 纯粹的计算逻辑，输入行情，输出信号值。
    特性: 无状态(相对于账户而言)，无IO，无副作用。
    """
    def __init__(self, name: str):
        self.name = name
        self.value: float = 0.0 # 当前信号值 (-1.0 ~ 1.0)

    @abstractmethod
    def on_tick(self, tick: TickData) -> float:
        """
        处理Tick数据，返回最新的信号值
        """
        pass

class DualMASignal(BaseSignal):
    """
    示例: 双均线信号
    逻辑: 
      - 快线 > 慢线 -> 1.0 (多)
      - 快线 < 慢线 -> -1.0 (空)
      - 否则保持
    """
    def __init__(self, fast_window: int = 10, slow_window: int = 20):
        super().__init__("DualMA")
        self.fast_window = fast_window
        self.slow_window = slow_window
        
        # 使用 Deque 缓存价格历史
        self.prices: Deque[float] = collections.deque(maxlen=slow_window)
        
    def on_tick(self, tick: TickData) -> float:
        self.prices.append(tick.last_price)
        
        # 数据不足时不产生信号
        if len(self.prices) < self.slow_window:
            return 0.0
            
        # 计算均线
        # 注意: 实际高频中可能用增量更新，这里演示用全量
        price_list = list(self.prices)
        fast_ma = sum(price_list[-self.fast_window:]) / self.fast_window
        slow_ma = sum(price_list[-self.slow_window:]) / self.slow_window
        
        if fast_ma > slow_ma:
            self.value = 1.0
        elif fast_ma < slow_ma:
            self.value = -1.0
            
        return self.value
