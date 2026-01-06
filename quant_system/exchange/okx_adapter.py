import asyncio
import logging
import ccxt.pro as ccxt
from typing import Dict, List, Optional

from quant_system.core.event import EventEngine, Event, EventType
from quant_system.core.types import OrderRequest, OrderData, TickData, Exchange, Direction, OrderType
from quant_system.exchange.base import BaseExchange

class OkxExchangeAdapter(BaseExchange):
    """
    OKX 交易所适配器 (基于 CCXT Pro)
    """
    def __init__(self, event_engine: EventEngine, config: Dict):
        super().__init__(event_engine)
        self.config = config
        self.logger = logging.getLogger("OkxAdapter")
        
        # 初始化 CCXT 实例
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

    async def check_login(self) -> bool:
        """
        验证 API Key 是否有效 (通过拉取一次历史订单)
        """
        try:
            # 拉取最近 1 条历史订单 (OKX 不支持通用的 fetch_orders)
            orders = await self.api.fetch_closed_orders(limit=1)
            self.logger.info(f"Login Check Passed. History Orders: {len(orders)}")
            if orders:
                last_o = orders[0]
                self.logger.info(f"Last Order: {last_o['symbol']} {last_o['side']} {last_o['status']}")
            return True
        except Exception as e:
            self.logger.error(f"Login Check Failed: {e}")
            return False

    async def subscribe(self, symbols: List[str]) -> None:
        """
        订阅行情 (Loop)
        """
        if not self._active:
            self.logger.warning("Adapter not connected, cannot subscribe")
            return

        self.logger.info(f"Start watching tickers for: {symbols}")
        # 1. Ticker Loop
        self._ws_task = asyncio.create_task(self._watch_loop(symbols))
        
        # 2. Private Order Loop (如果配置了 Key)
        if self.config.get('api_key'):
             self.logger.info("Start watching private orders...")
             asyncio.create_task(self._watch_orders_loop())

    async def send_order(self, req: OrderRequest) -> str:
        """
        发送订单
        """
        if not self._active:
            self.logger.warning("Adapter not connected")
            return ""

        # 映射方向
        side = 'buy' if req.direction == Direction.LONG else 'sell'
        
        # 映射类型 (目前仅支持 LIMIT)
        order_type = 'limit'
        
        # 映射 posSide (OKX 永续合约双向持仓模式下必填)
        # LONG -> posSide='long', SHORT -> posSide='short'
        pos_side = 'long' if req.direction == Direction.LONG else 'short'
        
        try:
            self.logger.info(f"Sending Order: {req.symbol} {side} {req.price}@{req.volume} posSide={pos_side}")
            
            # 调用 CCXT create_order
            # 注意: OKX Swap 的 amount 单位是合约张数
            order = await self.api.create_order(
                symbol=req.symbol,
                type=order_type,
                side=side,
                amount=req.volume,
                price=req.price,
                params={'posSide': pos_side} 
            )
            
            self.logger.info(f"Order Placed. ID: {order['id']}")
            return str(order['id'])
            
        except Exception as e:
            self.logger.error(f"Send Order Failed: {e}")
            return ""

    async def cancel_order(self, order_id: str, symbol: str) -> None:
        """
        撤销订单
        """
        try:
            self.logger.info(f"Cancelling Order: {order_id} ({symbol})")
            await self.api.cancel_order(order_id, symbol)
            self.logger.info("Cancel Sent")
        except Exception as e:
            self.logger.error(f"Cancel Order Failed: {e}")

    async def _watch_loop(self, symbols: List[str]):
        """
        主监听循环 (Tickers)
        """
        while self._active:
            try:
                # 这一步会挂起，直到收到交易所推送
                symbol = symbols[0]
                ccxt_ticker = await self.api.watch_ticker(symbol)
                
                # 阶段 6.2: 解析并推送 TickData
                tick = TickData(
                    symbol=symbol,
                    exchange=Exchange.OKX,
                    timestamp=ccxt_ticker['timestamp'] / 1000.0,
                    last_price=float(ccxt_ticker['last']),
                    volume=float(ccxt_ticker['baseVolume']),
                    bid_price_1=float(ccxt_ticker['bid']),
                    ask_price_1=float(ccxt_ticker['ask']),
                    funding_rate=0.0 
                )
                
                # self.logger.debug(f"Tick: {tick.symbol} {tick.last_price}")
                self.event_engine.put(Event(EventType.TICK, tick))
                
            except Exception as e:
                self.logger.error(f"Watch Loop Error: {e}")
                await asyncio.sleep(5)

    async def _watch_orders_loop(self):
        """
        监听私有订单回报
        """
        while self._active:
            try:
                order_data = await self.api.watch_orders()
                
                # 暂时只做 Log
                if isinstance(order_data, list):
                    for o in order_data:
                        self.logger.info(f"[Order Update] {o['symbol']} {o['status']} {o['filled']}/{o['amount']}")
                else:
                    self.logger.info(f"[Order Update] {order_data}")
                    
            except Exception as e:
                self.logger.error(f"Order Watch Error: {e}")
                await asyncio.sleep(5)
