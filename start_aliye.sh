#!/bin/bash
set -e
cd "$(dirname "$0")"

echo "🏙️  ALİYE başlatılıyor..."

python3 -m venv venv 2>/dev/null || true
source venv/bin/activate

pip install -r requirements.txt -q

echo "📰  Haber toplayıcı arka planda başlatılıyor..."
python aliye_main.py &
MAIN_PID=$!
echo "   PID: $MAIN_PID"

echo "🖥️   Dashboard başlatılıyor → http://localhost:8504"
streamlit run aliye_dashboard.py \
    --server.port 8504 \
    --server.headless true \
    --theme.base dark

# Cleanup on exit
kill $MAIN_PID 2>/dev/null || true
