import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable, Coroutine, Dict, List, Union

# Define Handler Type: Can be a regular function or an async coroutine
HandlerType = Union[Callable[["Event"], Any], Callable[["Event"], Coroutine[Any, Any, Any]]]

class EventType:
    """
    系统事件总线 Topic 定义 (集中式管理)
    """
    TICK = "eTick"             # 行情更新 -> Payload: TickData
    ORDER_REQ = "eOrderReq"    # 发单请求 -> Payload: OrderRequest
    ORDER_STATUS = "eOrder"    # 订单状态与回报 -> Payload: OrderData
    TRADE = "eTrade"           # 成交回报 -> Payload: TradeData
    LOG = "eLog"               # 日志事件 -> Payload: LogData (Dict)
    ERROR = "eError"           # 异常事件 -> Payload: ErrorData (Dict)
    RECOVERY = "eRecovery"     # 恢复事件 -> Payload: None (Signal)

@dataclass
class Event:
    """
    标准事件对象 (通用信封)
    """
    type: str       # 事件类型 (Topic)
    data: Any = None # 事件载荷 (Payload)

class EventEngine:
    """
    核心事件引擎 (Blind Bus)
    负责将事件分发给注册的回调函数，不包含任何业务逻辑。
    """
    def __init__(self) -> None:
        self._queue: Optional[asyncio.Queue[Event]] = None
        self._handlers: Dict[str, List[HandlerType]] = defaultdict(list)
        self._active: bool = False
        self._task: Union[asyncio.Task[Any], None] = None
        self.logger = logging.getLogger("EventEngine")

    def start(self) -> None:
        """启动事件处理循环"""
        if self._active:
            return
            
        if self._queue is None:
            self._queue = asyncio.Queue()
            
        self._active = True
        self._task = asyncio.create_task(self._run())
        self.logger.info("EventEngine started")

    def stop(self) -> None:
        """停止事件处理循环"""
        self._active = False
        if self._task:
            self._task.cancel()
        self.logger.info("EventEngine stopped")

    def register(self, type: str, handler: HandlerType) -> None:
        """注册事件回调"""
        # 防止重复注册
        if handler not in self._handlers[type]:
            self._handlers[type].append(handler)
            self.logger.debug(f"Registered handler {handler} for {type}")

    def unregister(self, type: str, handler: HandlerType) -> None:
        """注销事件回调"""
        if type in self._handlers:
            if handler in self._handlers[type]:
                self._handlers[type].remove(handler)
                self.logger.debug(f"Unregistered handler {handler} for {type}")

    def put(self, event: Event) -> None:
        """
        向总线推送事件
        注意：这是非阻塞方法，可以从同步代码中调用 (thread-safe for asyncio queue?)
        Asyncio Queue is checking loop thread safety. Ideally call internal put_nowait.
        如果从其他线程调用，需要用 loop.call_soon_threadsafe，这里暂时假设单线程或协程环境。
        """
        if self._queue is not None:
            self._queue.put_nowait(event)

    async def _run(self) -> None:
        """事件处理主循环"""
        while self._active:
            try:
                # wait for event
                event = await self._queue.get()
                self._process(event)
            except asyncio.CancelledError:
                self.logger.info("EventEngine task cancelled")
                break
            except Exception as e:
                self.logger.error(f"EventEngine run error: {e}", exc_info=True)

    def _process(self, event: Event) -> None:
        """触发回调"""
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    # 如果是协程函数，创建一个 Task 去执行，不阻塞总线分发
                    if asyncio.iscoroutinefunction(handler):
                        asyncio.create_task(handler(event))
                    else:
                        # 同步函数直接执行
                        handler(event) # type: ignore
                except Exception as e:
                    self.logger.error(f"Handler error for {event.type}: {e}", exc_info=True)
