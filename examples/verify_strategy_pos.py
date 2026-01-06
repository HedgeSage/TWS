import asyncio
import logging
import os
from dotenv import load_dotenv

from quant_system.core.event import EventEngine, Event, EventType
from quant_system.core.types import TickData, OrderData, Exchange
from quant_system.strategy.base import BaseStrategy
from quant_system.exchange.okx_adapter import OkxExchangeAdapter

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

class TestPosStrategy(BaseStrategy):
    def on_tick(self, tick: TickData):
        pass # 手动控制
        
    def on_order_status(self, order: OrderData):
        self.logger.info(f"Strategy received order: {order.status} Traded: {order.traded}")

async def main():
    """
    验证目标仓位管理逻辑
    """
    key = os.getenv("OKX_API_KEY")
    config = {
        "api_key": key,
        "secret_key": os.getenv("OKX_SECRET"),
        "passphrase": os.getenv("OKX_PASSPHRASE")
    }
    
    engine = EventEngine()
    engine.start()
    adapter = OkxExchangeAdapter(engine, config)
    
    # 初始化
    await adapter.connect()
    
    symbol = "WLD/USDT:USDT"
    strategy = TestPosStrategy(engine, adapter, [symbol])
    
    # 模拟启动
    await adapter.subscribe([symbol]) # Strategy start does this
    strategy.engine.register(EventType.ORDER_STATUS, strategy._on_order_status_wrapper)

    # 1. 确保当前仓位为0 (为了测试方便，最好手动平仓)
    # 我们假设初始是0.
    
    # 获取价格
    print("Waiting for tick...")
    await asyncio.sleep(2)
    # 获取任意最新价格 (Mock check)
    current_price = 0.6 # 假设，还是需要真实价格
    # 稍微等一下 adapter 收到 tick
    # 简便起见，直接取个安全值
    
    # 2. 设置目标: +2 张
    print("\n--- Test 1: Target +2 ---")
    await strategy.set_target_position(2, symbol, current_price) 
    # 此时应发单 Buy 2
    
    await asyncio.sleep(5)
    print(f"Current Pos: {strategy.pos}")
    
    # 3. 设置目标: -1 张 (反手: 平2多，开1空)
    # 我们的逻辑一次只会做一个动作: 如果 Target < Pos (2), 先平仓。
    # 第一次调用: Target(-1) < Pos(2) -> Sell Close 2. (Pos -> 0)
    print("\n--- Test 2: Target -1 (First Step: Close Long) ---")
    await strategy.set_target_position(-1, symbol, current_price)
    
    await asyncio.sleep(5)
    print(f"Current Pos: {strategy.pos}")
    
    # 此时 Pos 应该是 0. 需要再次 tick 驱动或者循环驱动。
    # 手动再次调用
    print("\n--- Test 2: Target -1 (Second Step: Open Short) ---")
    await strategy.set_target_position(-1, symbol, current_price)
    
    await asyncio.sleep(5)
    print(f"Current Pos: {strategy.pos}")
    
    # 4. 平仓
    print("\n--- Test 3: IDLE (Target 0) ---")
    await strategy.set_target_position(0, symbol, current_price)
    
    await asyncio.sleep(5)
    
    await adapter.close()
    engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
