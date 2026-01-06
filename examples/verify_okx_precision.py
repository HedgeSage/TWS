import asyncio
import logging
import os
from dotenv import load_dotenv

from quant_system.core.event import EventEngine
from quant_system.core.types import OrderRequest, Direction, Offset, OrderType, Exchange
from quant_system.exchange.okx_adapter import OkxExchangeAdapter

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

async def main():
    """
    手动测试脚本 v5: 精度修剪与杠杆验证
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
    
    try:
        await adapter.connect()
        await adapter.check_login()
        
        symbol = "WLD/USDT:USDT"

        # 1. 验证元数据加载
        inst = adapter.instruments.get(symbol)
        if inst:
            print(f"📦 Instrument Loaded: {inst.symbol}")
            print(f"   Contract Size: {inst.contract_size}")
            print(f"   Price Tick: {inst.price_tick}")
            print(f"   Min Volume: {inst.min_volume}")
        else:
            print("❌ Failed to load instrument metadata!")
            return

        # 2. 设置杠杆 (使用新封装的方法)
        await adapter.init_leverage(symbol, 40)
        
        # 3. 构造一个"脏"价格下单 (故意弄很多小数位)
        # WLD 价格 ~0.6, Tick 可能是 0.0001
        # 我们传入 0.512345678, 期望被修剪为 0.5123 (或 0.5123/0.5124)
        dirty_price = 0.512345678
        print(f"🧪 Testing Auto-Rounding with Dirty Price: {dirty_price}")
        
        req = OrderRequest(
            symbol=symbol,
            exchange=Exchange.OKX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=1,       
            price=dirty_price, # 直接传入脏数据
            offset=Offset.OPEN
        )
        
        # 4. 下单 (Adapter 内部应该会自动修剪并 Log)
        order_id = await adapter.send_order(req)
        
        if order_id:
            print(f"✅ Order Placed! ID: {order_id} (Check logs above for 'Rounding')")
            # 撤单
            await asyncio.sleep(2)
            await adapter.cancel_order(order_id, symbol)
        else:
            print("❌ Order Failed")
            
    finally:
        await adapter.close()
        engine.stop()

if __name__ == "__main__":
    asyncio.run(main())
