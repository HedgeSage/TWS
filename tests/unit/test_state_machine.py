import pytest
from quant_system.core.state import OrderStateMachine, InvalidStateTransitionError
from quant_system.core.types import OrderStatus

def test_valid_transitions():
    """测试合法的状态流转路径"""
    # 1. 最完美的路径: Created -> Submitted -> Filled
    assert OrderStateMachine.transition(OrderStatus.CREATED, OrderStatus.SUBMITTED) == OrderStatus.SUBMITTED
    assert OrderStateMachine.transition(OrderStatus.SUBMITTED, OrderStatus.FILLED) == OrderStatus.FILLED
    
    # 2. 撤单路径: Created -> Submitted -> Cancelled
    assert OrderStateMachine.transition(OrderStatus.SUBMITTED, OrderStatus.CANCELLED) == OrderStatus.CANCELLED

    # 3. 拒单路径
    assert OrderStateMachine.transition(OrderStatus.CREATED, OrderStatus.REJECTED) == OrderStatus.REJECTED

def test_partial_fill_flow():
    """测试部分成交的复杂路径"""
    current = OrderStatus.SUBMITTED
    
    # 第一次部分成交
    current = OrderStateMachine.transition(current, OrderStatus.PARTIALLY_FILLED)
    assert current == OrderStatus.PARTIALLY_FILLED
    
    # 第二次部分成交 (同状态流转)
    current = OrderStateMachine.transition(current, OrderStatus.PARTIALLY_FILLED)
    assert current == OrderStatus.PARTIALLY_FILLED
    
    # 剩余全部成交
    current = OrderStateMachine.transition(current, OrderStatus.FILLED)
    assert current == OrderStatus.FILLED

def test_invalid_transitions():
    """测试非法流转"""
    # 1. 终态不可变
    with pytest.raises(InvalidStateTransitionError):
        OrderStateMachine.transition(OrderStatus.FILLED, OrderStatus.SUBMITTED)
        
    with pytest.raises(InvalidStateTransitionError):
        OrderStateMachine.transition(OrderStatus.CANCELLED, OrderStatus.FILLED)
        
    # 2. 不可跳跃 (Created 不能直接变 Filled, 必须先 Submitted)
    # 虽然物理上可能极快，但逻辑上我们要求先有 Submitted 事件
    with pytest.raises(InvalidStateTransitionError):
        OrderStateMachine.transition(OrderStatus.CREATED, OrderStatus.FILLED)
