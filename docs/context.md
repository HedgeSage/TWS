# TWS Project Context Router

**Current Context**: Phase 9 - Preparation for Final Walkthrough.
**Last Updated**: 2026-01-07

此文档是 AI 助手的**核心上下文入口**。每次开启新会话时，请首先阅读本文档。

---

## 📚 1. 全局文档索引 (Global Documentation)

- **[架构设计 (Architecture)](./architecture.md)**: 
  包含系统核心架构图、数据结构定义 (`TickData`, `OrderData`)、事件总线设计等。
  *Source of Truth for System Design.*

- **[开发规范 (Standards)](./architecture.md#阶段-3-项目结构与环境规划-structure--environment)**: 
  (位于架构文档第3节) 包含目录结构、编码规范、依赖管理。

---

## 🚀 2. 核心模块文档 (Module Documentation)

记录了已完成的核心模块的设计思路与实现细节。

- **[01 连线与恢复机制](./modules/01_connection_mechanism.md)**
  - WebSocket 断连重连 (Exponential Backoff)
  - 状态对账 (State Reconciliation)
  
- **[02 交易策略体系](./modules/02_strategy_system.md)**
  - Alpha / Portfolio / Execution 三层架构
  - 目标仓位驱动 (Target Position Driven)
  
- **[03 持续集成与部署](./modules/03_production_deployment.md)**
  - CI/CD 流水线 (GitHub Actions)
  - Systemd 多实例管理 (`tws@.service`)
  - 混合部署模式

---

## 🗺️ 3. 项目进度 (Project Roadmap)

| 阶段 | 任务模块 | 状态 | 备注 |
| :--- | :--- | :--- | :--- |
| **Phase 1-3** | **基础设施** | ✅ Done | 架构、事件引擎、OXK连接器 |
| **Phase 4** | **执行层** | ✅ Done | BaseStrategy, Target Position |
| **Phase 5** | **信号系统** | ✅ Done | BaseSignal, Signal Layering |
| **Phase 6** | **稳定性** | ✅ Done | Recovery Hook, Reconciliation |
| **Phase 7** | **策略实现** | ✅ Done | DualMA, DynamicRebalance |
| **Phase 8** | **实盘部署** | ✅ Done | Config Refactor, Packaging, Systemd |
| **Phase 9** | **实战演练** | ⏳ Pending | Mock Run, Key Mgmt, Final Checks |

---

## 📝 4. 当前会话指引 (For the AI Agent)

**Current Priority**: 推进 Phase 9 实战演练。

**注意事项**:
1.  **Context Loading**: 在回答问题前，请根据问题涉及的模块，读取 `modules/` 下对应的详细文档。
2.  **Artifacts**: 请勿在 `.gemini/` 下创建新的 `task.md`。即使需要更新进度，也请直接修改本文件的 **Section 3 (Project Roadmap)**。
3.  **Style**: 保持文档的模块化，新的核心功能实现后，请在 `modules/` 下创建新文件并在本索引中注册。
