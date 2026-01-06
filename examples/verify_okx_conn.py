import asyncio
import logging
import os
from quant_system.core.event import EventEngine
from quant_system.exchange.okx_adapter import OkxExchangeAdapter

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

async def main():
    """
    手动测试脚本: 验证能否连接 OKX 并收到 Ticker 推送
    """
    # 1. 配置 (即使是空的 Key，CCXT 也可以推送 Public Ticker)
    config = {
        "api_key": os.getenv("OKX_API_KEY", ""),
        "secret_key": os.getenv("OKX_SECRET", ""),
        "passphrase": os.getenv("OKX_PASSPHRASE", "")
    }
    
    # 2. 初始化
    engine = EventEngine()
    adapter = OkxExchangeAdapter(engine, config)
    
    try:
        await adapter.connect()
        
        # 3. 订阅 BTC 永续
        # 注意: CCXT 的 Symbol 格式通常是 "BTC/USDT:USDT" (Swap)
        # 我们先用 CCXT 标准格式测试，后续再做 Symbol 映射
        target_symbol = "BTC/USDT:USDT" 
        await adapter.subscribe([target_symbol])
        
        print("Connected. Waiting for data... (Press Ctrl+C to stop)")
        
        # 4. 保持运行 10秒 看看效果
        await asyncio.sleep(10)
        
    except KeyboardInterrupt:
        pass
    finally:
        await adapter.close()

if __name__ == "__main__":
    asyncio.run(main())
