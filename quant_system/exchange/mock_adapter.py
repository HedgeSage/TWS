import asyncio
import uuid
import logging
import random
from typing import Dict, List, Optional

from quant_system.core.event import EventEngine, Event, EventType
from quant_system.core.types import (
    OrderRequest, OrderData, OrderStatus, 
    Exchange, Direction, OrderType, TickData
)
from quant_system.core.state import OrderStateMachine, InvalidStateTransitionError
from quant_system.exchange.base import BaseExchange
from quant_system.exchange.generator import MarketDataGenerator

class MockExchangeAdapter(BaseExchange):
    """
    模拟交易所适配器 (Process 1 Core)
    """
    def __init__(self, event_engine: EventEngine, config: Dict = None):
        super().__init__(event_engine)
        self.config = config or {}
        self.latency_ms = self.config.get("latency_ms", 100)
        
        self._active = False
        self._task: Optional[asyncio.Task] = None
        self._generator = MarketDataGenerator()
        
        # 模拟挂单簿: order_id -> OrderData
        self._active_orders: Dict[str, OrderData] = {}
        self._subscribed: List[str] = []
        
        self.logger = logging.getLogger("MockExchange")

    async def connect(self) -> None:
        self._active = True
        self._task = asyncio.create_task(self._run_simulation())
        self.logger.info(f"Mock Exchange Connected. Latency={self.latency_ms}ms")

    async def close(self) -> None:
        self._active = False
        if self._task:
            self._task.cancel()
        self.logger.info("Mock Exchange Closed")

    async def subscribe(self, symbols: List[str]) -> None:
        self._subscribed.extend(symbols)
        self.logger.info(f"Subscribed: {symbols}")

    async def send_order(self, req: OrderRequest) -> str:
        """
        模拟发单流程:
        1. 创建本地订单 (CREATED)
        2. 模拟网络延迟
        3. 变更为 SUBMITTED 并加入撮合队列
        """
        order_id = str(uuid.uuid4())
        
        order = OrderData(
            symbol=req.symbol,
            exchange=Exchange.MOCK,
            order_id=order_id,
            exchange_order_id=f"mock_oid_{random.randint(1000,9999)}",
            direction=req.direction,
            offset=req.offset,
            type=req.type,
            price=req.price,
            volume=req.volume,
            traded=0,
            status=OrderStatus.CREATED,
            timestamp=asyncio.get_event_loop().time()
        )
        
        # 立即记录 (Created)
        self._active_orders[order_id] = order
        # 推送 Created 状态 (可选，有些策略只关心 Submitted)
        # self.event_engine.put(Event(EventType.ORDER_STATUS, order))
        
        # 启动异步任务去模拟“发送到交易所”的过程
        asyncio.create_task(self._simulate_order_submit(order))
        
        return order_id

    async def cancel_order(self, order_id: str, symbol: str) -> None:
        asyncio.create_task(self._simulate_order_cancel(order_id))

    async def _simulate_order_submit(self, order: OrderData):
        """模拟网络延迟后提交成功"""
        delay = self.latency_ms / 1000.0
        await asyncio.sleep(delay)
        
        if order.order_id in self._active_orders:
            try:
                # 状态流转 Created -> Submitted
                OrderStateMachine.transition(order.status, OrderStatus.SUBMITTED)
                order.status = OrderStatus.SUBMITTED
                # 推送事件
                self.event_engine.put(Event(EventType.ORDER_STATUS, order))
                self.logger.debug(f"Order Submitted: {order.order_id}")
            except Exception as e:
                self.logger.error(f"Mock submit failed: {e}")

    async def _simulate_order_cancel(self, order_id: str):
        """模拟撤单"""
        delay = self.latency_ms / 1000.0
        await asyncio.sleep(delay)
        
        if order_id in self._active_orders:
            order = self._active_orders[order_id]
            try:
                OrderStateMachine.transition(order.status, OrderStatus.CANCELLED)
                order.status = OrderStatus.CANCELLED
                self.event_engine.put(Event(EventType.ORDER_STATUS, order))
                del self._active_orders[order_id] # 移除撮合队列
            except Exception:
                pass

    async def _run_simulation(self):
        """主循环: 生成行情 + 撮合"""
        while self._active:
            for symbol in self._subscribed:
                # 1. 生成 Tick
                tick = self._generator.get_tick(symbol)
                self.event_engine.put(Event(EventType.TICK, tick))
                
                # 2. 撮合 (简化版)
                self._match_orders(tick)
            
            # 500ms 一个 Tick
            await asyncio.sleep(0.5)

    def _match_orders(self, tick: TickData):
        """
        报价撮合逻辑
        """
        # 使用 list(items) 避免遍历时删除报错
        for order_id, order in list(self._active_orders.items()):
            if order.symbol != tick.symbol:
                continue
            
            if order.status != OrderStatus.SUBMITTED:
                continue

            matched = False
            # 市价单: 直接成交
            if order.type == OrderType.MARKET:
                matched = True
            # 限价单: 价格判定
            elif order.type == OrderType.LIMIT:
                if order.direction == Direction.LONG:
                    # 买单: 只要 卖一价 <= 委托价
                    if tick.ask_price_1 <= order.price:
                        matched = True
                elif order.direction == Direction.SHORT:
                    # 卖单: 只要 买一价 >= 委托价
                    if tick.bid_price_1 >= order.price:
                        matched = True
            
            if matched:
                self._simulate_fill(order, tick)

    def _simulate_fill(self, order: OrderData, tick: TickData):
        """执行成交"""
        try:
            OrderStateMachine.transition(order.status, OrderStatus.FILLED)
            order.status = OrderStatus.FILLED
            order.traded = order.volume
            # 简单假设成交价 = 委托价 (限价) 或 最新价 (市价)
            fill_price = order.price if order.type == OrderType.LIMIT else tick.last_price
            order.price = fill_price # Update to actual fill price for record
            
            # 推送订单更新
            self.event_engine.put(Event(EventType.ORDER_STATUS, order))
            
            # 推送成交明细 (Trade) - 可选
            # ...
            
            # 从活跃列表移除
            del self._active_orders[order.order_id]
            self.logger.info(f"Order Filled: {order.order_id} @ {fill_price}")
            
        except InvalidStateTransitionError:
            pass
