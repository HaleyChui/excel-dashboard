#!/bin/bash
# ───────────────────────────────────────────────
#  開發模式啟動腳本
#  執行：bash dev.sh
#
#  環境變數：
#    LLM_BACKEND=mock       → mock 回應（無 LLM 呼叫）
#    LLM_BACKEND=openrouter → OpenRouter API 直連（預設，最快）
#    LLM_BACKEND=hermes     → 串接 Hermes CLI（較慢但用你的 hermes 配置）
# ───────────────────────────────────────────────

set -e
export NVM_DIR="$HOME/.nvm"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
nvm use 20 2>/dev/null || true

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
LLM_BACKEND="${LLM_BACKEND:-openrouter}"

# ── 載入 Hermes env（讓 Flask 拿到 API keys） ──
if [ -f "$HOME/.hermes/.env" ]; then
  set -a
  source "$HOME/.hermes/.env"
  set +a
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " 📊 戰情表生成器 · 開發模式"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo " LLM 後端：$LLM_BACKEND"
echo ""

# ── 1. 後端 Flask ──
echo "🚀 啟動 Flask（http://localhost:5000）..."
cd "$ROOT_DIR/backend"
LLM_BACKEND="$LLM_BACKEND" .venv/bin/python app.py &
FLASK_PID=$!

# ── 2. 前端 Vite Dev Server（HMR） ──
echo "🚀 啟動 Vite Dev Server（http://localhost:5173）..."
cd "$ROOT_DIR/frontend"
npx vite --host 0.0.0.0 &
VITE_PID=$!

echo ""
echo "  ✓ Flask:  http://localhost:5000"
echo "  ✓ Vite:   http://localhost:5173  (HMR enabled)"
echo "  ✕ 停止：  Ctrl+C"
echo ""

# ── 3. 捕獲 Ctrl+C 同時關兩個 ──
trap "echo ''; echo '🛑 正在關閉服務...'; kill $FLASK_PID $VITE_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait