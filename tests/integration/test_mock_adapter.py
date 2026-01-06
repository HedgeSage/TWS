import pytest
import asyncio
from quant_system.core.event import EventEngine, EventType, Event
from quant_system.core.types import OrderRequest, Direction, Offset, OrderType, Exchange, OrderStatus
from quant_system.exchange.mock_adapter import MockExchangeAdapter

@pytest.mark.asyncio
async def test_mock_exchange_lifecycle():
    """
    集成测试: 验证 Mock 交易所的完整生命周期
    """
    # 1. Init
    engine = EventEngine()
    engine.start()
    
    mock = MockExchangeAdapter(engine, config={"latency_ms": 10}) # 10ms 极速模式
    await mock.connect()
    
    # 2. Subscribe
    await mock.subscribe(["BTC-USDT-SWAP"])
    
    # 3. Setup Events Capture
    received_status = []
    
    def on_order(event: Event):
        received_status.append(event.data.status)
    
    engine.register(EventType.ORDER_STATUS, on_order)
    
    # 4. Place Order (Buy Limit @ 20000)
    # 假设当前价格 10000, 买 20000 肯定成交 (Market Price logic in Generator is around 10000)
    # Generator starts at 10000. Limit Buy 20000 > Ask(10000). Should fill.
    req = OrderRequest(
        symbol="BTC-USDT-SWAP",
        exchange=Exchange.MOCK,
        direction=Direction.LONG,
        offset=Offset.OPEN,
        type=OrderType.LIMIT,
        price=20000.0,
        volume=1.0
    )
    
    order_id = await mock.send_order(req)
    assert order_id is not None
    
    # 5. Wait for loop (Submit -> Fill)
    # Latency 10ms + Tick Loop 500ms. Wait 2s is enough.
    await asyncio.sleep(2.0)
    
    # 6. Verify flow
    # Should see SUBMITTED then FILLED
    assert OrderStatus.SUBMITTED in received_status
    assert OrderStatus.FILLED in received_status
    
    await mock.close()
    engine.stop()
