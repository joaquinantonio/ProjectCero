#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a development environment (interactive)
# Usage: ./scripts/bootstrap.sh

ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$ROOT_DIR"

echo "Creating virtual environment .venv (if missing)"
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

echo "Activating virtualenv"
# shellcheck source=/dev/null
source .venv/bin/activate

echo "Installing dependencies"
pip install -r requirements.txt

if [ ! -f .env ]; then
  echo "Copying .env.example to .env"
  cp .env.example .env
  echo "Please edit .env to set DB credentials and DJANGO_SECRET_KEY before proceeding."
  echo "You can press enter to continue but migrations may fail if DB isn't configured."
  read -r -p "Edit .env now? (y/N) " edit_now
  if [ "$edit_now" = "y" ] || [ "$edit_now" = "Y" ]; then
    ${EDITOR:-vi} .env
  fi
fi

echo "Running migrations"
python manage.py migrate

echo "Create a superuser with: python manage.py createsuperuser"

echo "Done. Run the dev server with: python manage.py runserver"


