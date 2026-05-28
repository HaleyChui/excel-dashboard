#!/bin/bash
# 啟動戰情表生成器
# Usage: bash start.sh

set -e

export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20 2>/dev/null || true

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "📦 安裝後端依賴..."
cd "$ROOT_DIR/backend"
pip install -r requirements.txt -q 2>/dev/null || true

echo "📦 安裝前端依賴 + 建置..."
cd "$ROOT_DIR/frontend"
npm install --silent 2>/dev/null
npx vite build 2>&1 | tail -3

echo "🚀 啟動 Flask（http://localhost:5000）..."
cd "$ROOT_DIR/backend"
python app.py