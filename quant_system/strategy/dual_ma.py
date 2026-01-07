from typing import List
from quant_system.core.event import EventEngine
from quant_system.core.types import TickData, OrderData
from quant_system.strategy.base import BaseStrategy
from quant_system.exchange.base import BaseExchange
from quant_system.core.signal import DualMASignal

class DualMAStrategy(BaseStrategy):
    """
    双均线策略 (Portfolio Layer)
    展示如何使用 Signal Layer.
    """
    def __init__(self, engine: EventEngine, exchange: BaseExchange, symbols: List[str]):
        super().__init__(engine, exchange, symbols)
        
        # 1. 初始化 Signal (Alpha Layer)
        # 为每个币种创建一个独立的信号实例
        self.signals = {}
        for s in symbols:
            self.signals[s] = DualMASignal(fast_window=5, slow_window=10) # 短周期演示
            
        # 资金管理参数
        self.lot_size = 1.0 # 每次固定下单量
        
    def on_tick(self, tick: TickData):
        # 2. 将数据喂给对应的 Signal
        signal = self.signals.get(tick.symbol)
        if not signal:
            return
            
        sig_val = signal.on_tick(tick) # 获取最新 Alpha 值 (-1, 0, 1)
        
        # 3. 组合管理 (Portfolio Logic)
        # 简单逻辑: 信号 1 -> 持仓 1; 信号 -1 -> 持仓 -1
        
        target = 0.0
        if sig_val > 0.5:
            target = self.lot_size
        elif sig_val < -0.5:
            target = -self.lot_size
            
        # 4. 执行 (Execution Layer)
        # 使用 create_task 避免阻塞 tick loop? Set_target_position is async.
        # on_tick is sync wrapper, but set_target_position is async.
        # We need to spawn a task.
        import asyncio
        asyncio.create_task(self.set_target_position(target, tick.symbol, tick.last_price))

    def on_order_status(self, order: OrderData):
        pass
    
    async def on_recovery(self):
        self.logger.info("DualMA Strategy Recovered. Checking signals...")
        # 可以在这里重算信号，或者保持不动
        pass
