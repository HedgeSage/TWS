from typing import Dict, Set
from quant_system.core.types import OrderStatus

class InvalidStateTransitionError(Exception):
    """非法状态流转异常"""
    pass

class OrderStateMachine:
    """
    订单状态机 (Order Lifecycle Manager)
    
    原则:
    1. 单向流动: 一般不可逆 (除了部分成交可能继续成交)。
    2. 终态锁定: 一旦进入 FILLED/CANCELLED/REJECTED，不可再变。
    """
    
    # 允许的状态流转表
    _transitions: Dict[OrderStatus, Set[OrderStatus]] = {
        # 起始状态
        OrderStatus.CREATED: {
            OrderStatus.SUBMITTED,      # 正常提交
            OrderStatus.REJECTED,       # 风控/预检拒绝
            OrderStatus.CANCELLED       # 还没发出去就撤单
        },
        
        # 已提交 -> 等待回报
        OrderStatus.SUBMITTED: {
            OrderStatus.PARTIALLY_FILLED, # 部分成交
            OrderStatus.FILLED,           # 全部成交
            OrderStatus.CANCELLED,        # 成功撤单
            OrderStatus.REJECTED          # 交易所拒单
        },
        
        # 部分成交 -> 可以继续成交或结束
        OrderStatus.PARTIALLY_FILLED: {
            OrderStatus.PARTIALLY_FILLED, # 继续部分成交 (数量增加)
            OrderStatus.FILLED,           # 剩余全部成交
            OrderStatus.CANCELLED,        # 剩余部分撤销
            # 注意: 部分成交后一般不会变回 SUBMITTED
        },
        
        # 终态 (Terminal States) -> 不允许流转到任何状态
        OrderStatus.FILLED: set(),
        OrderStatus.CANCELLED: set(),
        OrderStatus.REJECTED: set(),
    }

    @classmethod
    def check_transition(cls, current: OrderStatus, new_state: OrderStatus) -> bool:
        """
        检查状态流转是否合法 (纯查询，不抛异常)
        """
        if current == new_state:
            # 允许同状态更新 (例如部分成交数量变化，或者重复收到回报)
            return True
        return new_state in cls._transitions.get(current, set())

    @classmethod
    def transition(cls, current: OrderStatus, new_state: OrderStatus) -> OrderStatus:
        """
        执行状态流转检查
        :return: new_state if valid
        :raise: InvalidStateTransitionError
        """
        if cls.check_transition(current, new_state):
            return new_state
        
        raise InvalidStateTransitionError(
            f"Invalid order state transition: {current} -> {new_state}"
        )
