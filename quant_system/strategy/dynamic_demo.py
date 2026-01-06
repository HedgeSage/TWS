from typing import List
from quant_system.strategy.base import BaseStrategy
from quant_system.core.types import TickData, OrderData
import asyncio

class DynamicRebalanceStrategy(BaseStrategy):
    def __init__(self, engine, exchange, symbols: List[str]):
        super().__init__(engine, exchange, symbols)
        
        # 策略参数
        self.symbol = symbols[0]
        self.leverage = 10
        self.base_pos_rate = 0.10 # 每次调仓 10%
        self.price_threshold = 0.01 # 1%
        
        # 策略状态
        self.level = 0
        self.last_rebalance_price = 0.0
        self.is_running = True
    
    def on_start(self):
        self.logger.info("Dynamic Rebalance Strategy Started")
        
        # 0. 初始化: 设置 10x 杠杆
        # (此时无法 await, 只能 fire-and-forget, 或者在 run 脚本里做)
        # 这里的 on_start 是同步的, 我们假设外部已经做好了初始化
        pass

    def on_tick(self, tick: TickData):
        if not self.is_running:
            return
            
        # 1. 初始化基准价格
        if self.last_rebalance_price == 0.0:
            self.last_rebalance_price = tick.last_price
            self.logger.info(f"Initialized Base Price: {self.last_rebalance_price}")
            # 初始建仓? 用户没说。
            # 假设初始必须得有仓位才能 "增加10%" (0 的 10% 还是 0)
            # 为了演示，我们假设初始开 10 张
            if self.pos == 0:
                self.logger.info("Initial Entry: 10 contracts Long")
                asyncio.create_task(self.set_target_position(10, self.symbol, tick.last_price))
            return

        # 2. 检查价格波动
        pct_change = (tick.last_price - self.last_rebalance_price) / self.last_rebalance_price
        
        triggered = False
        
        if pct_change >= self.price_threshold: # 上涨 1%
            self.level += 1
            new_target = self.pos * (1 + self.base_pos_rate) # 仓位增加 10%
            self.logger.info(f"📈 Price UP {pct_change:.2%}. Level -> {self.level}. Target -> {new_target:.2f}")
            
            asyncio.create_task(self.set_target_position(new_target, self.symbol, tick.last_price))
            triggered = True
            
        elif pct_change <= -self.price_threshold: # 下跌 1%
            self.level -= 1
            new_target = self.pos * (1 - self.base_pos_rate) # 仓位减少 10%
            self.logger.info(f"📉 Price DOWN {pct_change:.2%}. Level -> {self.level}. Target -> {new_target:.2f}")
            
            asyncio.create_task(self.set_target_position(new_target, self.symbol, tick.last_price))
            triggered = True
            
        if triggered:
            self.last_rebalance_price = tick.last_price # 重置基准
            
        # 3. 检查结束条件
        if abs(self.level) >= 2:
            self.logger.info(f"🛑 Level Reached Limit ({self.level}). Stopping Strategy & Closing All.")
            self.is_running = False
            asyncio.create_task(self.set_target_position(0, self.symbol, tick.last_price))
