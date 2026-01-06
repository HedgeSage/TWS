import asyncio
from quant_system.core.types import TickData, OrderData, OrderStatus
from quant_system.strategy.base import BaseStrategy

class DemoStrategy(BaseStrategy):
    """
    演示策略: 简单的价格触发下单
    """
    def __init__(self, engine, exchange, symbols):
        super().__init__(engine, exchange, symbols)
        self.entry_price = 0.0
        self.traded_cnt = 0

    def on_tick(self, tick: TickData):
        # 这里的 asyncio.create_task 是为了在同步回调中调用异步下单
        # 实际生产中 BaseStrategy 可以封装这个 boilerplate
        if self.traded_cnt == 0 and tick.last_price > 0:
            self.logger.info(f"Trigger Buy at {tick.last_price}")
            # Fire and forget task
            asyncio.create_task(self.buy(tick.symbol, tick.ask_price_1, 1.0))
            self.traded_cnt += 1

    def on_order_status(self, order: OrderData):
        self.logger.info(f"Strategy received order update: {order.status} {order.traded}/{order.volume}")
        if order.status == OrderStatus.FILLED:
            self.logger.info("Order Fully Filled! Strategy Logic Verified.")
