#!/bin/sh
# Apply schema migrations before the app starts. Doing this here rather than at
# import time means multiple uvicorn workers cannot race each other over DDL.
set -e

echo "Running database migrations…"
alembic upgrade head

exec "$@"
