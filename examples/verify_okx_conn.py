import asyncio
import logging
import os
from quant_system.core.event import EventEngine, EventType, Event
from quant_system.exchange.okx_adapter import OkxExchangeAdapter

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

def on_tick(event: Event):
    tick = event.data
    # 打印标准化后的 TickData
    print(f"✅ [Tick Received] {tick.symbol} Price:{tick.last_price} Bid:{tick.bid_price_1} Ask:{tick.ask_price_1}")

async def main():
    """
    手动测试脚本 v2: 验证 Ticker 解析功能
    """
    config = {
        "api_key": os.getenv("OKX_API_KEY", ""),
        "secret_key": os.getenv("OKX_SECRET", ""),
        "passphrase": os.getenv("OKX_PASSPHRASE", "")
    }
    
    engine = EventEngine()
    engine.start()
    
    # 注册回调
    engine.register(EventType.TICK, on_tick)

    adapter = OkxExchangeAdapter(engine, config)
    
    try:
        await adapter.connect()
        target_symbol = "BTC/USDT:USDT" 
        await adapter.subscribe([target_symbol])
        
        print("Connected. Waiting for Standardized Ticks... (Press Ctrl+C to stop)")
        await asyncio.sleep(10)
        
    except KeyboardInterrupt:
        pass
    finally:
        await adapter.close()
        engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
