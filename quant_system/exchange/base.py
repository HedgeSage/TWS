from abc import ABC, abstractmethod
from typing import List, Optional

from quant_system.core.event import EventEngine
from quant_system.core.types import OrderRequest, OrderData

class BaseExchange(ABC):
    """
    交易所抽象基类 (Interface)
    所有真实或模拟交易所都必须实现此接口。
    """
    def __init__(self, event_engine: EventEngine):
        self.event_engine = event_engine

    @abstractmethod
    async def connect(self) -> None:
        """连接交易所 (Websocket/REST)"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """断开连接"""
        pass

    @abstractmethod
    async def subscribe(self, symbols: List[str]) -> None:
        """订阅行情"""
        pass

    @abstractmethod
    async def send_order(self, req: OrderRequest) -> str:
        """
        发送订单
        :return: system_order_id (local unique id)
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> None:
        """撤销订单"""
        pass
