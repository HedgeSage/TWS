import asyncio
import logging
import ccxt.pro as ccxt  # 引入异步版 CCXT
from typing import Dict, List, Optional

from quant_system.core.event import EventEngine, Event, EventType
from quant_system.core.types import OrderRequest, OrderData
from quant_system.exchange.base import BaseExchange

class OkxExchangeAdapter(BaseExchange):
    """
    OKX 交易所适配器 (基于 CCXT Pro)
    阶段 6.1: 仅连接与日志打印，不涉及复杂解析
    """
    def __init__(self, event_engine: EventEngine, config: Dict):
        super().__init__(event_engine)
        self.config = config
        self.logger = logging.getLogger("OkxAdapter")
        
        # 初始化 CCXT 实例
        # 注意: 这里使用 options 里的 defaultType='swap' 默认交易永续合约
        self.api = ccxt.okx({
            'apiKey': config.get('api_key'),
            'secret': config.get('secret_key'),
            'password': config.get('passphrase'),
            'options': {'defaultType': 'swap'},  # 默认为永续合约
        })
        
        self._active = False
        self._ws_task: Optional[asyncio.Task] = None

    async def connect(self) -> None:
        """建立连接并启动监听循环"""
        self._active = True
        # CCXT 需要先加载市场数据才能解析 symbol
        self.logger.info("Loading markets from OKX...")
        await self.api.load_markets()
        self.logger.info("Markets loaded. OKX Adapter Initialized (CCXT Pro)")

    async def close(self) -> None:
        self._active = False
        if self._ws_task:
            self._ws_task.cancel()
        await self.api.close()
        self.logger.info("OKX Adapter Closed")

    async def subscribe(self, symbols: List[str]) -> None:
        """
        订阅行情 (Loop)
        阶段 6.1: 启动一个死循环，不断 watch_ticker 并打印日志
        """
        if not self._active:
            self.logger.warning("Adapter not connected, cannot subscribe")
            return

        self.logger.info(f"Start watching tickers for: {symbols}")
        # 启动后台任务去 Loop 接收数据
        self._ws_task = asyncio.create_task(self._watch_loop(symbols))

    async def send_order(self, req: OrderRequest) -> str:
        # 阶段 6.1 暂不实现下单，仅留空
        self.logger.warning("OKX Send Order Not Implemented in Phase 6.1")
        return "mock_oid_phase_6_1"

    async def cancel_order(self, order_id: str, symbol: str) -> None:
        pass

    async def _watch_loop(self, symbols: List[str]):
        """
        主监听循环
        CCXT Pro 的模式是: while True: await exchange.watch_ticker(symbol)
        """
        while self._active:
            try:
                # 注意: watch_ticker 一次通常只返回一个 symbol 的更新，或者我们可以用 watch_tickers (plural)
                # 这里为了简单验证测试，我们只监听第一个 symbol
                symbol = symbols[0]
                
                # 这一步会挂起，直到收到交易所推送
                ticker = await self.api.watch_ticker(symbol)
                
                # 阶段 6.1: 只打印 Raw Data
                self.logger.info(f"[WS Payload] {symbol} Price={ticker['last']} Vol={ticker['baseVolume']}")
                
                # (后续阶段 6.2 在这里做 TickData 转换并 put 到 EventEngine)
                
            except Exception as e:
                self.logger.error(f"Watch Loop Error: {e}")
                await asyncio.sleep(5) # 简单出错等待
