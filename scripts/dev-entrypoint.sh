#!/bin/sh
# Entrypoint dev : makemigrations + migrate + seed + runserver.
# En dev on bind-mount le code, donc les migrations se créent côté host.
set -eu

echo "[dev] makemigrations..."
python manage.py makemigrations --noinput || true

echo "[dev] migrate..."
python manage.py migrate --noinput

echo "[dev] seed_defaults..."
python manage.py seed_defaults || true

echo "[dev] démarrage : $*"
exec "$@"
