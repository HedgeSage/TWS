import asyncio
import logging
import os
from dotenv import load_dotenv

from quant_system.core.event import EventEngine, EventType, Event
from quant_system.exchange.okx_adapter import OkxExchangeAdapter

# 加载 .env 环境变量
load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

async def main():
    """
    手动测试脚本 v3: 验证账户私有数据 (鉴权+订单)
    """
    # 1. 检查 Env
    key = os.getenv("OKX_API_KEY")
    if not key:
        print("❌ Error: OKX_API_KEY not found in .env")
        return

    config = {
        "api_key": key,
        "secret_key": os.getenv("OKX_SECRET"),
        "passphrase": os.getenv("OKX_PASSPHRASE")
    }
    
    # 2. 启动
    engine = EventEngine()
    engine.start()
    adapter = OkxExchangeAdapter(engine, config)
    
    try:
        await adapter.connect()
        
        # 3. 验证登录 & 拉取历史
        print("🔍 Checking Login and History Orders...")
        logged_in = await adapter.check_login()
        if not logged_in:
            print("❌ Login Failed. Check your keys.")
            return
            
        print("✅ Login Success! keys are valid.")
        
        # 4. 启动订阅 (Ticker + Orders)
        # 只要没有报错，就说明 WS 鉴权通过了
        print("🚀 Subscribing to Private Channels...")
        await adapter.subscribe(["BTC/USDT:USDT"])
        
        print("Listening... (Press Ctrl+C to stop)")
        # 您可以在手机 App 上下一个小单来测试推送
        await asyncio.sleep(30)
        
    except KeyboardInterrupt:
        pass
    finally:
        await adapter.close()
        engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
