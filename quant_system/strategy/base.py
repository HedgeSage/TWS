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
        
        self.pos: float = 0.0  # 当前净仓位 (Net Position)
        self.target_pos: float = 0.0 # 目标仓位
        
        self.logger.info(f"Strategy Initialized for {symbols}")

    async def start(self):
        """
        启动策略
        """
        self.engine.register(EventType.TICK, self._on_tick_wrapper)
        self.engine.register(EventType.ORDER_STATUS, self._on_order_status_wrapper)
        # 注册恢复事件
        self.engine.register(EventType.RECOVERY, self._on_recovery_wrapper)
        
        await self.exchange.subscribe(self.symbols)
        self.on_start()

    async def stop(self):
        """停止策略"""
        self.engine.unregister(EventType.TICK, self._on_tick_wrapper)
        self.engine.unregister(EventType.ORDER_STATUS, self._on_order_status_wrapper)
        self.engine.unregister(EventType.RECOVERY, self._on_recovery_wrapper)
        self.on_stop()

    # --- 用户接口 ---
    
    @abstractmethod
    def on_tick(self, tick: TickData):
        pass

    def on_order_status(self, order: OrderData):
        pass
    
    async def on_recovery(self):
        """
        [New in 7.4] 灾难恢复钩子
        在系统完成自动对账(持仓/挂单)后触发。
        """
        pass
    
    def on_start(self):
        pass
    
    def on_stop(self):
        pass

    # --- 恢复逻辑 (Reconciliation) ---

    async def _on_recovery_wrapper(self, event: Event):
        """处理恢复事件"""
        self.logger.warning("Recovery Event Received! Starting Reconciliation...")
        
        # 1. 对账持仓
        await self._reconcile_position()
        
        # 2. 对账挂单
        await self._reconcile_open_orders()
        
        # 3. 用户钩子
        await self.on_recovery()
        self.logger.info("Reconciliation Complete.")

    async def _reconcile_position(self):
        """强制同步持仓"""
        active_positions = await self.exchange.query_position()
        # 筛选本策略关心的
        net_pos = 0.0
        for p in active_positions:
            if p.symbol in self.symbols:
                # 简单累加 (Hedge Mode: Long - Short)
                # PositionData has direction, volume
                if p.direction == Direction.LONG:
                    net_pos += p.volume
                elif p.direction == Direction.SHORT:
                    net_pos -= p.volume
                    
        old_pos = self.pos
        self.pos = net_pos # 强制覆盖
        if abs(old_pos - net_pos) > 0.0001:
            self.logger.warning(f"Position Reconciled: Local {old_pos} -> Remote {net_pos}")

    async def _reconcile_open_orders(self):
        """强制同步挂单"""
        open_orders = await self.exchange.query_open_orders()
        
        # 重建 active_orders
        # 注意: 这里会丢失部分历史订单的本地缓存(prev_traded)，但为了正确性必须重置
        
        current_ids = set()
        for o in open_orders:
            if o.symbol in self.symbols:
                self.active_orders[o.order_id] = o
                self.orders[o.order_id] = o # 更新缓存
                current_ids.add(o.order_id)
        
        # 清理不在列表中的
        to_remove = []
        for oid in self.active_orders:
            if oid not in current_ids:
                to_remove.append(oid)
        
        for oid in to_remove:
            del self.active_orders[oid]
            # 标记为未知关闭? 暂时不动 active_orders 以外的 self.orders
            
        self.logger.info(f"Open Orders Reconciled. Active: {len(self.active_orders)}")

    async def set_target_position(self, target: float, symbol: str, price: float):
        """
        核心方法: 设置目标仓位
        由执行逻辑判断如果不一致，发单去追
        """
        self.target_pos = target
        diff = target - self.pos
        
        if abs(diff) < 0.0001: # 忽略微小误差
            return

        # 简单的自动执行逻辑 (One Step)
        # 复杂情况(如反手)需要分两步，这里依赖 tick 驱动下一次
        
        direction = Direction.LONG
        offset = Offset.NONE
        volume = abs(diff)
        
        # 决策逻辑 (假设单币种策略)
        if self.pos >= 0:
            if target > self.pos:
                # 加仓多
                direction = Direction.LONG
                offset = Offset.OPEN
            elif target < self.pos:
                # 减仓多 or 反手
                direction = Direction.SHORT
                offset = Offset.CLOSE # 先平多
                if target < 0:
                    volume = self.pos # 仅平掉现有，剩下的反手交给下一次 Check
        
        elif self.pos < 0:
            if target < self.pos:
                # 加仓空
                direction = Direction.SHORT
                offset = Offset.OPEN
            elif target > self.pos:
                # 减仓空 or 反手
                direction = Direction.LONG
                offset = Offset.CLOSE # 先平空
                if target > 0:
                    volume = abs(self.pos)
        
        # 执行
        self.logger.info(f"Rebalance: Pos {self.pos} -> Target {target}. Action: {direction} {offset} {volume}@{price}")
        await self._send_order(symbol, direction, offset, price, volume)

    # --- 交易便捷指令 ---

    async def buy(self, symbol: str, price: float, volume: float) -> str:
        return await self._send_order(symbol, Direction.LONG, Offset.OPEN, price, volume)

    async def sell(self, symbol: str, price: float, volume: float) -> str:
        return await self._send_order(symbol, Direction.SHORT, Offset.CLOSE, price, volume)

    async def short(self, symbol: str, price: float, volume: float) -> str:
        return await self._send_order(symbol, Direction.SHORT, Offset.OPEN, price, volume)

    async def cover(self, symbol: str, price: float, volume: float) -> str:
        return await self._send_order(symbol, Direction.LONG, Offset.CLOSE, price, volume)

    # --- 内部逻辑 ---

    async def _send_order(self, symbol, direction, offset, price, volume) -> str:
        req = OrderRequest(
            symbol=symbol,
            exchange=Exchange.OKX, 
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
        
        # 计算成交差额更新仓位
        prev_order = self.orders.get(order.order_id)
        prev_traded = prev_order.traded if prev_order else 0.0
        new_traded = order.traded
        delta = new_traded - prev_traded
        
        if delta > 0:
            self._update_pos(order.direction, order.offset, delta)
            
        self.orders[order.order_id] = order
        
        if order.is_active():
            self.active_orders[order.order_id] = order
        elif order.order_id in self.active_orders:
            del self.active_orders[order.order_id]
            
        self.on_order_status(order)

    def _update_pos(self, direction: Direction, offset: Offset, volume: float):
        """根据成交更新净仓位"""
        if direction == Direction.LONG:
            if offset == Offset.OPEN:
                self.pos += volume
            else: # CLOSE (Sell Long to Close)
                 # 实际上 Close Long 是 Direction.SHORT + Offset.CLOSE? 
                 # 不，用户习惯: buy/sell pair. sell 是平多.
                 # 检查 BaseStrategy.sell implementation: Direction.SHORT, Offset.CLOSE.
                 pass
        
        # 修正: 统一按 Direction/Offset 逻辑
        # Long/Open -> +
        # Short/Close -> + (买入平空)
        # Short/Open -> -
        # Long/Close -> - (卖出平多)
        
        change = 0.0
        if direction == Direction.LONG:
            if offset == Offset.OPEN:
                change = volume
            elif offset == Offset.CLOSE:
                change = volume # Cover Short -> Pos increases (e.g. -1 to 0)
        elif direction == Direction.SHORT:
            if offset == Offset.OPEN:
                change = -volume
            elif offset == Offset.CLOSE:
                change = -volume # Sell Long -> Pos decreases (e.g. 1 to 0)
                
        self.pos += change
        self.logger.info(f"Position Update: {change} -> Current: {self.pos}")
