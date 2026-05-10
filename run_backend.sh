#!/bin/bash
# Backend startup script
cd "$(dirname "$0")"
export PYTHONPATH="${PWD}:${PYTHONPATH}"
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
