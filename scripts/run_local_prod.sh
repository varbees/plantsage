#!/usr/bin/env bash
set -euo pipefail

export PORT="${PORT:-8080}"
python -m uvicorn api.main:app --host 0.0.0.0 --port "${PORT}"
