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

# Les deux commandes suivantes tournaient en dev (dev-entrypoint.sh) mais PAS en
# prod. Sur une Box neuve, cela voulait dire : aucun Group Django (les
# bibliothécaires s'authentifient sans aucune permission) et aucune
# planification django-q2 — donc AUCUNE sauvegarde horaire (§8), sur la cible
# précisément conçue pour tourner sans maintenance. Les deux sont idempotentes.
echo "[bibliofelia] rôles et permissions..."
python manage.py setup_roles || true

echo "[bibliofelia] planifications django-q2 (sauvegarde horaire, expirations)..."
python manage.py setup_schedules || true

echo "[bibliofelia] compilation traductions..."
python manage.py compilemessages 2>/dev/null || true

echo "[bibliofelia] collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "[bibliofelia] démarrage : $*"
exec "$@"
