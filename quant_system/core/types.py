from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# --- Enums ---

class Direction(str, Enum):
    """交易方向"""
    LONG = "LONG"   # 多
    SHORT = "SHORT" # 空

class Offset(str, Enum):
    """开平方向 (Hedge Mode 必须)"""
    OPEN = "OPEN"   # 开仓
    CLOSE = "CLOSE" # 平仓
    NONE = "NONE"   # 现货/单向持仓可能用到

class OrderType(str, Enum):
    """订单类型"""
    LIMIT = "LIMIT"   # 限价
    MARKET = "MARKET" # 市价

class OrderStatus(str, Enum):
    """订单状态"""
    CREATED = "CREATED"           # 本地已创建
    SUBMITTED = "SUBMITTED"       # 已发送至交易所
    PARTIALLY_FILLED = "PARTIALLY_FILLED" # 部分成交
    FILLED = "FILLED"             # 全部成交
    CANCELLED = "CANCELLED"       # 已撤单
    REJECTED = "REJECTED"         # 拒单

class Exchange(str, Enum):
    """交易所枚举"""
    OKX = "OKX"
    BINANCE = "BINANCE"
    MOCK = "MOCK"

class ProductType(str, Enum):
    """产品类型 (统一扁平分类)"""
    PERP = "PERP"       # 永续合约
    FUTURE = "FUTURE"   # 交割期货
    SPOT = "SPOT"       # 现货
    OPTION = "OPTION"   # 期权

# --- Data Classes ---

@dataclass
class Instrument:
    """单一扁平化合约定义 (Entity 1 Core)"""
    symbol: str             # 系统唯一代码 (如 "BTC-USDT-SWAP")
    exchange: Exchange      # 交易所
    product_type: ProductType # 产品类型
    
    contract_size: float    # 合约乘数 (1张合约对应多少标的)
    price_tick: float       # 最小价格变动
    
    # 可选字段
    expiry_date: Optional[datetime] = None  # 过期日
    option_strike: Optional[float] = None   # 行权价 (仅期权)
    underlying: str = ""                    # 标的物代码

@dataclass
class TickData:
    """标准行情数据"""
    symbol: str
    exchange: Exchange
    timestamp: float        # Unix timestamp (seconds)
    last_price: float
    volume: float
    bid_price_1: float
    ask_price_1: float
    funding_rate: float = 0.0 # 资金费率 (Perp Feature)

    @property
    def datetime(self) -> datetime:
        return datetime.fromtimestamp(self.timestamp)

@dataclass
class OrderRequest:
    """发单请求"""
    symbol: str
    exchange: Exchange
    direction: Direction
    type: OrderType
    volume: float
    price: float = 0.0
    offset: Offset = Offset.NONE # 默认为NONE, 但Perp必须指定OPEN/CLOSE
    client_order_id: str = ""

@dataclass
class OrderData:
    """订单数据 (系统内部流通的标准对象)"""
    symbol: str
    exchange: Exchange
    order_id: str           # Client Order ID
    exchange_order_id: str  # Exchange ID (Initial empty)
    
    direction: Direction
    offset: Offset
    type: OrderType
    price: float
    volume: float
    traded: float           # 已成交量
    status: OrderStatus
    
    timestamp: float        # Update timestamp

    def is_active(self) -> bool:
        """是否为活跃状态 (未终结)"""
        return self.status in [
            OrderStatus.CREATED, 
            OrderStatus.SUBMITTED, 
            OrderStatus.PARTIALLY_FILLED
        ]

@dataclass
class TradeData:
    """成交明细"""
    symbol: str
    exchange: Exchange
    order_id: str
    trade_id: str
    direction: Direction
    offset: Offset
    price: float
    volume: float
    timestamp: float
