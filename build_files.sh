#!/bin/bash
set -e

echo "===> College ERP: Starting Vercel Staging Build..."

# Install python dependencies
python3 -m pip install -r requirements.txt

# Collect static assets for Vercel CDN deployment
python3 manage.py collectstatic --noinput --clear

echo "===> College ERP: Vercel Staging Build Completed Successfully."
