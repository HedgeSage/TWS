# 核心模块: 交易策略体系 (Strategy Architecture)

## 1. 概述
本模块定义了从市场数据输入到交易指令输出的完整决策流。采用 **Alpha-Portfolio-Execution** 三层分层架构，实现逻辑解耦。

## 2. 架构分层

```mermaid
graph TD
    Data[Tick Data] --> Alpha
    Alpha[Alpha Layer\n(Signal Generation)] -->|Signal (-1 to 1)| Portfolio
    Portfolio[Portfolio Layer\n(Risk & Allocation)] -->|Target Position| Execution
    Execution[Execution Layer\n(Order Management)] -->|Orders| Exchange
```

### 2.1 Alpha 层 (信号)
- **职责**: 纯数学计算，无状态，无副作用。
- **输入**: 市场数据 (Tick/Bar)。
- **输出**: 信号值 (通常为 -1.0 ~ 1.0)。
- **代码**: `quant_system/core/signal.py` (`BaseSignal`).

### 2.2 Portfolio 层 (组合/策略)
- **职责**: 策略的大脑。消费信号，结合账户资金、风险偏好，决定“现在应该持有多少仓位”。
- **逻辑**: `Current Pos` vs `Target Pos`。
- **代码**: `quant_system/strategy/*.py` (如 `DualMAStrategy`).

### 2.3 Execution 层 (执行)
- **职责**: 策略的手脚。负责把“目标仓位”变成“实际仓位”。
- **核心逻辑**: **Target Position Driven (目标仓位驱动)**。
    - 如果 `Target > Current`: 买入 (Long/Cover)。
    - 如果 `Target < Current`: 卖出 (Sell/Short)。
- **功能**: 处理滑点、拆单、挂单撤单、交易所 API 交互。
- **代码**: `quant_system/strategy/base.py` (`BaseStrategy`).

## 3. 关键实现细节

### 3.1 目标仓位驱动 (Set Target Position)
策略开发者只需调用 `await self.set_target_position(new_target)`。
底层会自动计算差额：
- 需买入: `volume = new_target - current_pos`
- 需卖出: `volume = current_pos - new_target`

### 3.2 动态动态平衡 (Dynamic Rebalance)
- 在 `DynamicRebalanceStrategy` 中展示了如何利用此架构实现网格/再平衡策略。
- 无论市场如何波动，策略只需关注“我希望持有多少”，执行层负责“如何达到”。

## 4. 注意事项
- **双向持仓模式**: 目前系统设计强制假设 **Hedge Mode** (双向持仓)，即 Long 和 Short 仓位独立存在。
- **并发安全**: 策略是异步运行的 (`asyncio`)，需注意不要在 `await` 期间让共享状态发生意外改变（虽然单线程模型回避了大部分锁问题）。
