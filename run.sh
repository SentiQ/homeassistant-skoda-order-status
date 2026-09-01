#!/bin/sh
set -eu
cd /config/skoda-order-status
mkdir -p logs
exec .venv/bin/python scripts/poll_order_status.py >> logs/poll.log 2>&1
