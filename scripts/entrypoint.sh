#!/bin/sh
# Entrypoint prod : migrations + seed minimal + lancement gunicorn.
set -eu

echo "[bibliofelia] vérification base SQLite..."
python -c "from django.db import connection; connection.ensure_connection()" \
    || { echo "DB indisponible, abort"; exit 1; }

echo "[bibliofelia] migrations..."
python manage.py migrate --noinput

echo "[bibliofelia] seed initial si nécessaire..."
python manage.py seed_defaults || true

echo "[bibliofelia] compilation traductions..."
python manage.py compilemessages 2>/dev/null || true

echo "[bibliofelia] collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "[bibliofelia] démarrage : $*"
exec "$@"
