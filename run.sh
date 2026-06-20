#!/usr/bin/env bash
set -e
python -m pip install -r requirements.txt
python -m app.seed
echo "ClearLane on http://localhost:8000  (/ = overview, /console = live console)"
uvicorn app.main:app --host 0.0.0.0 --port 8000
