#!/bin/bash

# stop.sh - MacOS 停止服务脚本
# Usage: ./scripts/macos/stop.sh <account_name>

ACCOUNT=$1

if [ -z "$ACCOUNT" ]; then
    echo "Usage: $0 <account_name>"
    exit 1
fi

PLIST_DEST="$HOME/Library/LaunchAgents/com.tws.strategy.$ACCOUNT.plist"

echo ">>> [Stop] Stopping service for account: $ACCOUNT"

if launchctl list | grep "com.tws.strategy.$ACCOUNT" > /dev/null; then
    launchctl unload "$PLIST_DEST"
    echo ">>> ✅ Service Stopped."
else
    echo ">>> ⚠️  Service not running."
fi
