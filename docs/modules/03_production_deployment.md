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

### 3.2 Systemd 多实例管理
使用 **Systemd Template Units** 实现单台服务器运行多个独立策略进程。

- **模板文件**: `scripts/tws@.service`
- **启动命令**: `sudo systemctl start tws@<account_id>`
- **原理**: Systemd 将 `@` 后的字符串作为 `%i` 参数传给启动命令：
  `python -m quant_system.main --config config.json --account <account_id>`

### 3.3 内存优化
针对低配云服务器 (1C2G) 进行了深度优化：
- **按需加载**: `OkxExchangeAdapter` 支持 `market_type="SWAP"` 参数。
- **效果**: 仅加载永续合约元数据 (约 270 个)，跳过现货和期权 (约 2000+ 个)，内存占用降低 **88%**。

## 4. 安全实践
- **密钥管理**: 推荐使用环境变量或 1Password Service Account，严禁将 API Key 硬编码在代码库中。
- **权限控制**: GitHub Deploy Keys 设置为 **Read-Only**。
- **网络安全**: 交易所 API Key 绑定服务器 **固定 IP**，且关闭提币权限。
