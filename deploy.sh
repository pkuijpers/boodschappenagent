#!/usr/bin/env bash
set -euo pipefail

PI_HOST="${PI_HOST:-192.168.2.117}"
PI_USER="${PI_USER:-pieter}"
REMOTE_DIR="${REMOTE_DIR:-/home/${PI_USER}/albert}"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Deploying to ${PI_USER}@${PI_HOST}:${REMOTE_DIR} ..."

# Backup remote data-bestanden naar lokale /backup (zonder recipes en reference)
echo "Backup maken van remote data ..."
rsync -avz \
  --exclude='recipes/' \
  --exclude='reference/' \
  "${PI_USER}@${PI_HOST}:${REMOTE_DIR}/data/" \
  "${LOCAL_DIR}/backup/"

# Sync broncode, recipes en reference (altijd overschrijven)
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
  --include='data/recipes/***' \
  --include='data/reference/***' \
  --include='pyproject.toml' \
  --include='uv.lock' \
  --include='README.md' \
  --exclude='*' \
  "${LOCAL_DIR}/" \
  "${PI_USER}@${PI_HOST}:${REMOTE_DIR}/"

# Sync overige data-bestanden; remote wint als die nieuwer is
rsync -avz --update \
  --exclude='recipes/' \
  --exclude='reference/' \
  "${LOCAL_DIR}/data/" \
  "${PI_USER}@${PI_HOST}:${REMOTE_DIR}/data/"

# Restart de remote app
ssh "${PI_USER}@${PI_HOST}" "sudo systemctl restart albert"

echo ""
echo "Klaar. Installeer dependencies op de Pi met:"
echo "  ssh ${PI_USER}@${PI_HOST} 'cd ${REMOTE_DIR} && uv sync --no-dev'"
echo ""
echo "Start de server met:"
echo "  ssh ${PI_USER}@${PI_HOST} 'cd ${REMOTE_DIR} && uv run uvicorn boodschappenagent.web.app:create_app --factory --host 0.0.0.0 --port 8000'"
echo ""
echo "=== Logs van remote server ==="
ssh "${PI_USER}@${PI_HOST}" "sudo journalctl -u albert -n 50 --no-pager"
