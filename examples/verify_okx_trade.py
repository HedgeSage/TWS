import asyncio
import logging
import os
from dotenv import load_dotenv

from quant_system.core.event import EventEngine, EventType
from quant_system.core.types import OrderRequest, Direction, Offset, OrderType, Exchange
from quant_system.exchange.okx_adapter import OkxExchangeAdapter

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

async def main():
    """
    手动测试脚本 v4: 真实交易验证 (下单 -> 等待 -> 撤单)
    ⚠️ 警告: 涉及真实资金，请确保逻辑安全
    """
    # 1. 配置
    key = os.getenv("OKX_API_KEY")
    if not key:
        print("❌ Error: OKX_API_KEY not found")
        return

    config = {
        "api_key": key,
        "secret_key": os.getenv("OKX_SECRET"),
        "passphrase": os.getenv("OKX_PASSPHRASE")
    }
    
    engine = EventEngine()
    engine.start()
    adapter = OkxExchangeAdapter(engine, config)
    
    try:
        await adapter.connect()
        await adapter.check_login() # 确保登录
        
        symbol = "WLD/USDT:USDT"
        
        # 1.1 设置杠杆 40x (仅测试用，实际策略中应在初始化时统一设置)
        print(f"🔧 Setting Leverage to 40x for {symbol}...")
        try:
            # okx setLeverage (leverage, symbol, params={})
            await adapter.api.set_leverage(40, symbol)
            print("✅ Leverage set to 40x")
        except Exception as e:
            print(f"⚠️ Set Leverage Failed (might be already set): {e}")

        # 2. 获取当前价格 (使用 REST 快速获取一次)
        print(f"📊 Fetching current price for {symbol}...")
        ticker = await adapter.api.fetch_ticker(symbol)
        current_price = ticker['last']
        print(f"💰 Current Price: {current_price}")
        
        # 3. 计算安全挂单价 (当前价的 80%)
        # 注意: WLD 价格较低 (0.x)，不能用 int()
        safe_price = round(current_price * 0.8, 4)
        print(f"🛡️ Safe Limit Price (80%): {safe_price}")
        
        # 4. 构建订单请求
        req = OrderRequest(
            symbol=symbol,
            exchange=Exchange.OKX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=1,          # 1张合约 (对于BTC通常是0.01或0.001BTC，取决于合约面值，OKX 1张=0.01BTC?) 
                               # 实际上 OKX BTC-USDT-SWAP 1张=0.01 BTC
                               # 0.01 * 95000 = 950 USDT. 
                               # 等等，OKX BTC 永续合约 1张可能是 0.01 BTC，也可能是 0.001 BTC
                               # 最好确认一下 contractSize，或者下最小单位
                               # 为了更安全，我们下 ETH/USDT? 
                               # 这里为了测试，我们信任 80% 的价格缓冲区是足够安全的，即使是 1 张 BTC
            price=safe_price,
            offset=Offset.OPEN
        )
        
        # 5. 下单
        print("🚀 Sending Limit Buy Order...")
        order_id = await adapter.send_order(req)
        
        if not order_id:
            print("❌ Order Failed!")
            return
            
        print(f"✅ Order Placed! ID: {order_id}")
        
        # 6. 等待 10 秒 (观察私有流推送)
        print("⏳ Waiting 10s for order status updates...")
        await asyncio.sleep(10)
        
        # 7. 撤单
        print(f"🛑 Cancelling Order {order_id}...")
        await adapter.cancel_order(order_id, symbol)
        print("✅ Cancel Request Sent.")
        
        # 8. 再等 5 秒确认撤单推送
        await asyncio.sleep(5)
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        await adapter.close()
        engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
