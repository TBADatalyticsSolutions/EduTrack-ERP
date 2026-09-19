#!/usr/bin/env bash
set -o errexit
set -o nounset
set -o pipefail

echo "==> Installing Python dependencies"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo "==> Running Django deployment checks"
python manage.py check --deploy

echo "==> Verifying migration files"
python manage.py makemigrations --check --dry-run

echo "==> Applying database migrations"
python manage.py migrate --noinput

echo "==> Collecting static files"
python manage.py collectstatic --noinput

echo "==> Build completed successfully"
