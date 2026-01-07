#!/bin/bash
# TWS Quant System - Update Script
# Usage: ./update.sh

# Stop Service
echo "Stopping TWS Service..."
sudo systemctl stop tws

# 1. Update Config (Git Pull)
echo "Pulling latest config from Git..."
git pull origin main

# 2. Update Code (Pip Install)
# Option A: From PyPI (if you publish)
# pip install --upgrade tws-quant

# Option B: From Local Source (Hybrid Mode)
echo "Installing latest code..."
pip install .

# 3. Restart Service (Disabled for Safety)
# Restart your specific strategy manually:
# sudo systemctl restart tws@your_config_name
echo "Update Complete! Please restart your strategy process manually."
