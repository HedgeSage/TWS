# 量化交易系统 (Quant Trading System)

基于 Python 的高扩展性量化交易系统，采用 **事件总线 (Event Bus) + 状态机 (State Machine)** 架构。

## 核心特性
- **事件驱动**: Pure Pub/Sub architecture.
- **状态管理**: Strict Order State Machine.
- **Mock 优先**: Built-in Mock Exchange for logic verification.
- **环境隔离**: Production/Dev dependency isolation.

## 快速开始
```bash
pip install -e ".[dev]"
```
