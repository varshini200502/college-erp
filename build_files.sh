#!/bin/bash
set -e

echo "===> College ERP: Starting Vercel Staging Build..."

# If Vercel's python virtual environment exists, activate it
if [ -d "/vercel/path0/.vercel/python/.venv" ]; then
    echo "Activating Vercel Python virtual environment..."
    source /vercel/path0/.vercel/python/.venv/bin/activate
fi

# Install python dependencies with PEP 668 fallback for uv-managed environments
python3 -m pip install -r requirements.txt --break-system-packages 2>/dev/null || python3 -m pip install -r requirements.txt || true

# Collect static assets for Vercel CDN deployment
python3 manage.py collectstatic --noinput --clear

echo "===> College ERP: Vercel Staging Build Completed Successfully."
