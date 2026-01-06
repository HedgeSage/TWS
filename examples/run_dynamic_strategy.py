import asyncio
import logging
import os
from dotenv import load_dotenv

from quant_system.core.event import EventEngine
from quant_system.exchange.okx_adapter import OkxExchangeAdapter
from quant_system.strategy.dynamic_demo import DynamicRebalanceStrategy

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

async def main():
    """
    实盘运行动态调仓策略
    """
    key = os.getenv("OKX_API_KEY")
    if not key:
        print("Please configure .env first")
        return
        
    config = {
        "api_key": key,
        "secret_key": os.getenv("OKX_SECRET"),
        "passphrase": os.getenv("OKX_PASSPHRASE")
    }
    
    engine = EventEngine()
    engine.start()
    adapter = OkxExchangeAdapter(engine, config)
    
    await adapter.connect()
    # 等待元数据加载
    await asyncio.sleep(2)
    
    symbol = "WLD/USDT:USDT"
    
    # 1. 策略初始化前置操作: 设置杠杆
    await adapter.init_leverage(symbol, 10)
    
    # 2. 启动策略
    strategy = DynamicRebalanceStrategy(engine, adapter, [symbol])
    await strategy.start()
    
    print("\n🚀 Strategy Started. Monitoring WLD price...")
    
    # 模拟等待一段时间 (实际应一直运行)
    # 为了演示效果，您可以手动去 OKX 下个单影响价格? 不，您无法影响市场。
    # 只能等待市场波动。
    
    try:
        while strategy.is_running:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        await strategy.stop()
        await adapter.close()
        engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
