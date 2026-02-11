#!/bin/bash

# SPY Credit Spread Dashboard - Backend Startup Script

cd "$(dirname "$0")"

# 親ディレクトリをPYTHONPATHに追加
export PYTHONPATH="$(dirname $(pwd)):$PYTHONPATH"

echo "Starting FastAPI Dashboard..."
echo "PYTHONPATH: $PYTHONPATH"
echo ""

# uvicornで起動
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
