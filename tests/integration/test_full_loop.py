import pytest
import asyncio
import logging
from quant_system.core.event import EventEngine
from quant_system.exchange.mock_adapter import MockExchangeAdapter
from quant_system.strategy.demo import DemoStrategy

@pytest.mark.asyncio
async def test_full_system_loop(caplog):
    """
    系统级集成测试: 验证 策略 -> 总线 -> Mock交易所 -> 总线 -> 策略 的完整闭环
    """
    caplog.set_level(logging.INFO)
    
    # 1. Init Core
    engine = EventEngine()
    engine.start()
    
    # 2. Init Exchange (Mock)
    mock_exchange = MockExchangeAdapter(engine, config={"latency_ms": 10})
    await mock_exchange.connect()
    
    # 3. Init Strategy
    symbol = "BTC-USDT-SWAP"
    strategy = DemoStrategy(engine, mock_exchange, [symbol])
    await strategy.start() # 订阅行情
    
    # 4. Run Loop
    # Wait for generator to produce ticks -> Strategy triggers buy -> Exchange fills -> Strategy gets update
    await asyncio.sleep(2.0)
    
    # 5. Verify Logs
    # 检查是否有关键日志输出，证明闭环跑通
    logs = caplog.text
    assert "Trigger Buy" in logs
    assert "Strategy received order update" in logs
    assert "Order Fully Filled!" in logs
    
    # 6. Cleanup
    await strategy.stop()
    await mock_exchange.close()
    engine.stop()
