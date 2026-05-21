#!/bin/bash
# Sauvegarde BibliOfelia : sqlite3 .backup + rsync media + rotation.
set -euo pipefail

TS=$(date -u +%Y%m%dT%H%M%SZ)
DATA="${BACKUP_DATA_PATH:-/app/data}"
MEDIA="${BACKUP_MEDIA_PATH:-/app/media}"
DEST="${BACKUP_DEST_PATH:-/backup}"

mkdir -p "${DEST}/db/hourly" "${DEST}/db/daily" "${DEST}/db/weekly" "${DEST}/db/monthly" "${DEST}/media"

DB="${DATA}/bibliofelia.sqlite3"
if [ ! -f "${DB}" ]; then
    echo "[backup] BD introuvable (${DB}), skip"
    exit 0
fi

OUT="${DEST}/db/hourly/bibliofelia-${TS}.sqlite3"
echo "[backup] dump ${DB} -> ${OUT}"
sqlite3 "${DB}" ".backup '${OUT}'"

echo "[backup] vérification intégrité..."
INTEGRITY=$(sqlite3 "${OUT}" "PRAGMA integrity_check;")
if [ "${INTEGRITY}" != "ok" ]; then
    echo "[backup] ERREUR intégrité: ${INTEGRITY}"
    rm -f "${OUT}"
    exit 2
fi

gzip -f "${OUT}"

# Promotions
HOUR=$(date -u +%H)
DOW=$(date -u +%u)   # 1..7
DOM=$(date -u +%d)

if [ "${HOUR}" = "02" ]; then
    cp "${OUT}.gz" "${DEST}/db/daily/"
fi
if [ "${HOUR}" = "02" ] && [ "${DOW}" = "1" ]; then
    cp "${OUT}.gz" "${DEST}/db/weekly/"
fi
if [ "${HOUR}" = "02" ] && [ "${DOM}" = "01" ]; then
    cp "${OUT}.gz" "${DEST}/db/monthly/"
fi

# Rotation
find "${DEST}/db/hourly"  -name "*.sqlite3.gz" -mtime +1   -delete
find "${DEST}/db/daily"   -name "*.sqlite3.gz" -mtime +7   -delete
find "${DEST}/db/weekly"  -name "*.sqlite3.gz" -mtime +35  -delete
find "${DEST}/db/monthly" -name "*.sqlite3.gz" -mtime +400 -delete

# Media (quotidien)
if [ "${HOUR}" = "02" ] && [ -d "${MEDIA}" ]; then
    echo "[backup] rsync media..."
    rsync -a --delete "${MEDIA}/" "${DEST}/media/"
fi

# Cloud (si activé)
if [ "${CLOUD_BACKUP_ENABLED:-false}" = "true" ] && [ -n "${RCLONE_REMOTE:-}" ]; then
    if [ "${HOUR}" = "03" ]; then
        echo "[backup] sync vers ${RCLONE_REMOTE}..."
        rclone sync "${DEST}" "${RCLONE_REMOTE}" --max-age 35d || echo "[backup] sync cloud échoué, retry plus tard"
    fi
fi

echo "[backup] ${TS} OK"
