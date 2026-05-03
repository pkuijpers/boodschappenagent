#!/usr/bin/env bash
set -euo pipefail

PI_HOST="${PI_HOST:-192.168.2.117}"
PI_USER="${PI_USER:-pieter}"
REMOTE_DIR="${REMOTE_DIR:-/home/${PI_USER}/albert}"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Deploying to ${PI_USER}@${PI_HOST}:${REMOTE_DIR} ..."

rsync -avz --delete \
  --exclude='.git/' \
  --exclude='tests/' \
  --exclude='logs/' \
  --exclude='docs/' \
  --exclude='poc-ah-lijstje/' \
  --exclude='CLAUDE.md' \
  --exclude='digitize.sh' \
  --exclude='**/__pycache__/' \
  --exclude='**/*.pyc' \
  --exclude='.ruff_cache/' \
  --exclude='.pytest_cache/' \
  --exclude='*.egg-info/' \
  --exclude='.venv/' \
  --include='src/***' \
  --include='data/' \
  --include='data/ah_tokens.json' \
  --include='data/recipes/***' \
  --include='data/reference/***' \
  --include='pyproject.toml' \
  --include='uv.lock' \
  --include='README.md' \
  --exclude='*' \
  "${LOCAL_DIR}/" \
  "${PI_USER}@${PI_HOST}:${REMOTE_DIR}/"

echo ""
echo "Klaar. Installeer dependencies op de Pi met:"
echo "  ssh ${PI_USER}@${PI_HOST} 'cd ${REMOTE_DIR} && uv sync --no-dev'"
echo ""
echo "Start de server met:"
echo "  ssh ${PI_USER}@${PI_HOST} 'cd ${REMOTE_DIR} && uv run uvicorn boodschappenagent.web.app:create_app --factory --host 0.0.0.0 --port 8000'"
