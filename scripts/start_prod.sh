#!/bin/bash
# 生产环境启动（多 worker，无 reload）
# 在服务器项目根目录执行: ./scripts/start_prod.sh

cd "$(dirname "$0")/.."
WORKERS=${WORKERS:-2}
PORT=${PORT:-8000}
echo "Starting production server: $WORKERS workers, port $PORT"
exec python -m uvicorn src.main:app --host 0.0.0.0 --port "$PORT" --workers "$WORKERS"
