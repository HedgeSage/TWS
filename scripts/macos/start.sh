#!/bin/bash

# start.sh - MacOS 一键打包运行
# Usage: ./scripts/macos/start.sh <account_name>

set -e

ACCOUNT=$1

if [ -z "$ACCOUNT" ]; then
    echo "Usage: $0 <account_name> (e.g. ./scripts/macos/start_macos.sh sub06)"
    exit 1
fi

PROJECT_ROOT=$(pwd)
PYTHON_EXEC=$(which python3)

echo ">>> [Start] Account: $ACCOUNT"

# 1. Build & Install
echo ">>> (1/4) Packaging..."
rm -rf dist/
$PYTHON_EXEC -m build > /dev/null

echo ">>> (2/4) Installing..."
pip install dist/*.whl --force-reinstall > /dev/null

# 2. Config & Launch
PLIST_SRC="scripts/macos/com.tws.strategy.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/com.tws.strategy.$ACCOUNT.plist"

echo ">>> (3/4) Configuring Service..."
# 确保日志目录存在
mkdir -p logs

# 替换模板变量并写入 LaunchAgents (使用 sed 动态替换)
# 这里我们假设 plist 是个模板，直接替换 {{ACCOUNT}}, {{PROJECT_ROOT}}, {{PYTHON_EXEC}}
cp "$PLIST_SRC" "$PLIST_DEST"
sed -i '' "s|{{ACCOUNT}}|$ACCOUNT|g" "$PLIST_DEST"
sed -i '' "s|{{PROJECT_ROOT}}|$PROJECT_ROOT|g" "$PLIST_DEST"
sed -i '' "s|{{PYTHON_EXEC}}|$PYTHON_EXEC|g" "$PLIST_DEST"

echo ">>> (4/4) Launching..."
# 尝试卸载旧的（屏蔽错误）
launchctl unload "$PLIST_DEST" 2>/dev/null || true
# 加载新的
launchctl load "$PLIST_DEST"

# 简单检查
sleep 1
if launchctl list | grep "com.tws.strategy.$ACCOUNT" > /dev/null; then
    echo "✅ Success! Service started."
    echo "   Logs: tail -f logs/tws.$ACCOUNT.out"
else
    echo "❌ Failed to start. Check logs/tws.$ACCOUNT.err"
fi
