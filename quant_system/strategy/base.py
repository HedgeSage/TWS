import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional

from quant_system.core.event import EventEngine, Event, EventType
from quant_system.core.types import (
    TickData, OrderData, OrderRequest, TradeData,
    Exchange, Direction, Offset, OrderType, OrderStatus
)
from quant_system.exchange.base import BaseExchange

class BaseStrategy(ABC):
    """
    策略抽象基类 (User API)
    原则: 提供极简的接口，隐藏底层 EventQueue 和 Exchange 细节
    """
    
    def __init__(self, engine: EventEngine, exchange: BaseExchange, symbols: List[str]):
        self.engine = engine
        self.exchange = exchange
        self.symbols = symbols
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # 内部状态
        self.orders: Dict[str, OrderData] = {} # order_id -> Order
        self.active_orders: Dict[str, OrderData] = {}
        
        self.logger.info(f"Strategy Initialized for {symbols}")

    async def start(self):
        """
        启动策略
        1. 注册核心回调
        2. 订阅行情
        """
        self.engine.register(EventType.TICK, self._on_tick_wrapper)
        self.engine.register(EventType.ORDER_STATUS, self._on_order_status_wrapper)
        
        await self.exchange.subscribe(self.symbols)
        self.on_start()

    async def stop(self):
        """停止策略"""
        self.engine.unregister(EventType.TICK, self._on_tick_wrapper)
        self.engine.unregister(EventType.ORDER_STATUS, self._on_order_status_wrapper)
        self.on_stop()

    # --- 用户需要实现的回调 ---
    
    @abstractmethod
    def on_tick(self, tick: TickData):
        """收到行情推送"""
        pass

    def on_order_status(self, order: OrderData):
        """收到订单状态更新 (默认仅打印，用户可覆盖)"""
        pass
    
    def on_start(self):
        pass
    
    def on_stop(self):
        pass

    # --- 交易便捷指令 (Trading API) ---

    async def buy(self, symbol: str, price: float, volume: float) -> str:
        """买入开仓 (Open Long)"""
        return await self._send_order(
            symbol, Direction.LONG, Offset.OPEN, price, volume
        )

    async def sell(self, symbol: str, price: float, volume: float) -> str:
        """卖出平仓 (Close Long)"""
        return await self._send_order(
            symbol, Direction.SHORT, Offset.CLOSE, price, volume
        )

    async def short(self, symbol: str, price: float, volume: float) -> str:
        """卖出开仓 (Open Short)"""
        return await self._send_order(
            symbol, Direction.SHORT, Offset.OPEN, price, volume
        )

    async def cover(self, symbol: str, price: float, volume: float) -> str:
        """买入平仓 (Close Short)"""
        return await self._send_order(
            symbol, Direction.LONG, Offset.CLOSE, price, volume
        )

    # --- 内部逻辑 ---

    async def _send_order(self, symbol, direction, offset, price, volume) -> str:
        req = OrderRequest(
            symbol=symbol,
            exchange=Exchange.MOCK, # TODO: Should be adaptable
            direction=direction,
            offset=offset,
            type=OrderType.LIMIT,
            price=price,
            volume=volume
        )
        order_id = await self.exchange.send_order(req)
        return order_id

    def _on_tick_wrapper(self, event: Event):
        tick: TickData = event.data
        if tick.symbol in self.symbols:
            self.on_tick(tick)

    def _on_order_status_wrapper(self, event: Event):
        order: OrderData = event.data
        self.orders[order.order_id] = order
        
        if order.is_active():
            self.active_orders[order.order_id] = order
        elif order.order_id in self.active_orders:
            del self.active_orders[order.order_id]
            
        self.on_order_status(order)
