import pytest
from datetime import datetime
from quant_system.core.types import (
    Instrument, ProductType, Exchange, 
    OrderData, OrderStatus, Direction, Offset, OrderType
)

def test_instrument_creation():
    """验证 Instrument 扁平化模型"""
    # 1. 创建永续合约
    perp = Instrument(
        symbol="BTC-USDT-SWAP",
        exchange=Exchange.OKX,
        product_type=ProductType.PERP,
        contract_size=1.0,
        price_tick=0.1
    )
    assert perp.expiry_date is None
    assert perp.product_type == ProductType.PERP

    # 2. 创建期权合约 (验证可选字段)
    option = Instrument(
        symbol="BTC-250320-50000-C",
        exchange=Exchange.OKX,
        product_type=ProductType.OPTION,
        contract_size=1.0,
        price_tick=5.0,
        expiry_date=datetime(2025, 3, 20),
        option_strike=50000.0
    )
    assert option.option_strike == 50000.0
    assert option.product_type == ProductType.OPTION

def test_order_active_status():
    """验证订单状态判断逻辑"""
    base_order = OrderData(
        symbol="BTC", exchange=Exchange.MOCK,
        order_id="1", exchange_order_id="",
        direction=Direction.LONG, offset=Offset.OPEN, type=OrderType.LIMIT,
        price=100, volume=1, traded=0,
        status=OrderStatus.CREATED, timestamp=0
    )
    
    assert base_order.is_active() == True
    
    base_order.status = OrderStatus.SUBMITTED
    assert base_order.is_active() == True
    
    base_order.status = OrderStatus.FILLED
    assert base_order.is_active() == False
    
    base_order.status = OrderStatus.CANCELLED
    assert base_order.is_active() == False
