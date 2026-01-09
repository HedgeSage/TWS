# 核心模块: 持续集成与部署 (CI/CD & Deployment)

## 1. 概述
本模块描述了从代码提交到生产环境运行的自动化流水线。核心原则是 **"不可变制品"** 与 **"配置分离"**。

## 2. 部署工作流

### 2.1 自动化构建 (GitHub Actions)
- **触发**: Push to `main` branch.
- **流程**:
    1.  Checkout Code.
    2.  Set up Python 3.10.
    3.  `python -m build` 生成 Wheel 包 (`.whl`)。
    4.  Upload Artifacts.
- **配置文件**: `.github/workflows/build.yml`.

### 2.2 混合更新模式 (Hybrid Deployment)
生产环境采用“双通道”更新：
1.  **代码更新**: 安装最新的 `.whl` 包（通过脚本或 Pip）。
2.  **配置更新**: 使用 `git pull` 拉取最新的配置文件。

## 3. 生产环境管理

### 3.1 目录结构
```text
/home/ubuntu/tws
├── config.json          # 核心配置文件 (多账号)
├── scripts/
│   ├── update.sh        # 一键更新脚本
│   └── tws@.service     # Systemd 模板
└── quant_system/        # (可选) 源码，用于本地调试或git pull模式
```

### 3.2 部署平台指南

#### A. Linux 云服务器 (Systemd)
适用于 7x24 小时无人值守运行。

- **服务模板**: `scripts/tws@.service` (支持自动重启配置)
- **部署步骤**:
  1. 复制模板: `sudo cp scripts/tws@.service /etc/systemd/system/`
  2. 重载配置: `sudo systemctl daemon-reload`
  3. 启动实例: `sudo systemctl start tws@<account_id>` (如 `tws@account1`)
  4. 查看状态: `sudo systemctl status tws@<account_id>`
- **日志路径**: `journalctl -u tws@<account_id> -f`

#### B. MacOS 本地主机 (Launchd)
适用于本地 Mac Mini 长期运行测试，已集成 **防休眠** 与 **一键部署**。

- **核心脚本**:
    - `scripts/macos/start.sh <account>`: 一键执行 `Build` -> `Install` -> `Config` -> `Start`。
    - `scripts/macos/stop.sh <account>`: 一键停止服务。
    - `scripts/macos/com.tws.strategy.plist`: Launchd 配置文件模板。

- **部署流程**:
  ```bash
  # 1. 启动服务 (例如账户 sub06)
  ./scripts/macos/start.sh sub06
  
  # 2. 停止服务
  ./scripts/macos/stop.sh sub06
  ```

- **重要说明**:
    1. **权限问题 (PermissionError)**:
       如果遇到 `Operation not permitted: 'config.json'`，是因为 macOS 对 `Documents/Downloads` 等文件夹有隐私保护。
       **解决**: 建议将项目移动到用户主目录 (`~/TWS`) 下运行，或在“系统设置 -> 隐私与安全性 -> 完全磁盘访问权限”中添加终端/Python。
    2. **防休眠**:
       启动脚本会自动调用 `caffeinate -s`，**无需**修改系统电源设置，且仅在策略运行时生效。

- **日志路径**:
    - **标准输出/错误**: `logs/tws.<account>.out` / `.err` (通常为空或仅包含启动报错)
    - **应用日志**: `logs/TWS_YYYYMMDD_HHMMSS.log` (完整的策略运行日志)

### 3.3 内存优化
针对低配云服务器 (1C2G) 进行了深度优化：
- **按需加载**: `OkxExchangeAdapter` 支持 `market_type="SWAP"` 参数。
- **效果**: 仅加载永续合约元数据 (约 270 个)，跳过现货和期权 (约 2000+ 个)，内存占用降低 **88%**。

## 4. 安全实践
- **密钥管理**: 推荐使用环境变量或 1Password Service Account，严禁将 API Key 硬编码在代码库中。
- **权限控制**: GitHub Deploy Keys 设置为 **Read-Only**。
- **网络安全**: 交易所 API Key 绑定服务器 **固定 IP**，且关闭提币权限。

## 5. 常见问题排查与优化 (Troubleshooting & Optimization)

### 5.1 策略调试记录
在实盘部署过程中已修复以下核心问题，后续开发请注意规避：

1.  **EventLoop 冲突 (RuntimeError)**
    -   **现象**: 服务启动后立刻静默退出，无日志。
    -   **原因**: `EventEngine` 在 `__init__` 中过早初始化 `asyncio.Queue`，导致队列绑定到了错误的事件循环上。
    -   **解决**: 将队列初始化延迟到 `start()` 方法中，确保其绑定到当前运行的 Loop。

2.  **CCXT 市场模糊 (Ambiguity Error)**
    -   **现象**: 报错 `okx safeMarket() requires a fourth argument...`。
    -   **原因**: 为节省内存配置了 `market_type="SWAP"`，导致 CCXT 缺少其他市场元数据，无法正确解析部分混合推送数据。
    -   **解决**: 暂时在 `config.json` 中移除 `market_type` 限制，加载全量市场 (`Cache Size: 1500+`)。

### 5.2 日志系统说明
为适应长期运行需求，日志系统已做如下调优：
-   **文件命名**: `logs/TWS_YYYYMMDD_HHMMSS.log` (每次启动生成独立文件)。
-   **静默模式**: 移除 `StreamHandler`，控制台不再输出由应用产生的日志，仅显示 `launchd` 的系统级报错。
-   **等级过滤**: 行情 ticker 数据被降级为 DEBUG，生产环境默认 INFO 级别下不会记录，以节省磁盘空间。

### 5.3 已知限制
-   **MacOS 权限 (TCC)**: 在 `~/Documents` 目录下运行 Python 脚本可能会遇到 `PermissionError: config.json`。
    -   *推荐方案*: 将项目迁移至 `~/TWS` (用户主目录)。
    -   *替代方案*: 在“系统设置 -> 隐私与安全性 -> 完全磁盘访问权限”中手动添加 Python 解释器。
