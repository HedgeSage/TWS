import pytest
import asyncio
from quant_system.core.event import EventEngine, Event, EventType

@pytest.mark.asyncio
async def test_event_engine_pub_sub():
    """测试发布订阅基本功能"""
    engine = EventEngine()
    engine.start()

    # 1. 定义一个接收器
    received_events = []
    
    def sync_handler(event: Event):
        received_events.append(event)

    # 2. 注册
    engine.register(EventType.TICK, sync_handler)

    # 3. 发送
    tick_event = Event(EventType.TICK, data="TickDataPayload")
    engine.put(tick_event)

    # 4. 等待处理 (因为是异步的，稍微等待一下)
    await asyncio.sleep(0.1)

    # 5. 验证
    assert len(received_events) == 1
    assert received_events[0].data == "TickDataPayload"

    # 6. 注销
    engine.unregister(EventType.TICK, sync_handler)
    engine.put(Event(EventType.TICK, data="ShouldNotReceive"))
    await asyncio.sleep(0.1)
    assert len(received_events) == 1 # 应该没有增加

    engine.stop()

@pytest.mark.asyncio
async def test_async_handler():
    """测试异步回调支持"""
    engine = EventEngine()
    engine.start()
    
    # 使用 asyncio.Event 来同步测试状态
    done_event = asyncio.Event()

    async def async_handler(event: Event):
        await asyncio.sleep(0.01) # 模拟IO
        if event.data == "AsyncPayload":
            done_event.set()

    engine.register(EventType.LOG, async_handler)
    engine.put(Event(EventType.LOG, data="AsyncPayload"))

    # 等待异步回调完成
    try:
        await asyncio.wait_for(done_event.wait(), timeout=1.0)
    except asyncio.TimeoutError:
        pytest.fail("Async handler failed to trigger")

    engine.stop()
