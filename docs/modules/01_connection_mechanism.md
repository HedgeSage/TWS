# 核心模块: 连线与恢复机制 (Connection & Recovery)

## 1. 概述
本模块负责维护与交易所 (OKX) 的 WebSocket 长连接，处理网络波动，并确保断线重连后的数据一致性。

## 2. 设计思路
- **抽象层**: `BaseExchange` 定义标准接口。
- **实现层**: `OkxExchangeAdapter` (基于 `ccxt.pro`)。
- **生命周期**: `Connect -> Active -> Error/Disconnect -> Reconnect -> Recovery -> Active`。

## 3. 核心机制

### 3.1 自动重连 (Automatic Reconnection)
- **实现位置**: `OkxExchangeAdapter._watch_loop`
- **策略**: 指数退避 (Exponential Backoff)。
    - 初始等待: 1s
    - 最大等待: 60s
    - 每次失败: `sleep_time = min(sleep_time * 2, 60)`
- **异常捕获**: 捕获所有 `NetworkError` 和 `ExchangeError`，防止进程崩溃。

### 3.2 状态对账 (State Reconciliation)
- **触发时机**: 重连成功后，系统分发 `EventType.RECOVERY` 事件。
- **执行流程**:
    1.  **查询全量持仓**: 调用 REST API `fetch_positions`。
    2.  **覆盖内存状态**: `strategy.pos` 被强制更新为交易所返回的真实持仓。
    3.  **查询全量挂单**: 调用 REST API `fetch_open_orders`。
    4.  **重置订单缓存**: `strategy.active_orders` 被重置，清理掉本地存在但交易所已不存在的“僵尸单”。

### 3.3 灾难恢复钩子 (User Hook)
- **方法**: `BaseStrategy.on_recovery(self)`
- **用途**: 策略开发者在此实现自定义逻辑。
- **示例**:
    ```python
    async def on_recovery(self):
        self.logger.warning("Recovered from crash! Cancelling all open orders...")
        await self.cancel_all()
    ```

## 4. 极端场景处理
- **场景**: 断网期间有成交。
    - **处理**: 对账机制会发现本地持仓与远程不一致，直接使用远程持仓覆盖本地，修正误差。
- **场景**: 交易所 API 报错 (500/502)。
    - **处理**: `_watch_loop` 会捕获异常并重试，不会导致程序退出。
