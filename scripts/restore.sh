#!/bin/bash
# Restauration BibliOfelia depuis sauvegarde locale.
# Usage : ./restore.sh <fichier.sqlite3.gz>
set -euo pipefail

SRC="${1:-}"
DEST="${BACKUP_DATA_PATH:-/app/data}/bibliofelia.sqlite3"

if [ -z "${SRC}" ] || [ ! -f "${SRC}" ]; then
    echo "Usage : $0 <chemin/vers/sauvegarde.sqlite3.gz>"
    exit 1
fi

echo "[restore] BD cible : ${DEST}"
echo "[restore] backup avant écrasement..."
if [ -f "${DEST}" ]; then
    cp "${DEST}" "${DEST}.before-restore-$(date -u +%Y%m%dT%H%M%SZ)"
fi

echo "[restore] décompression et copie..."
gunzip -c "${SRC}" > "${DEST}"

echo "[restore] vérification intégrité..."
INTEGRITY=$(sqlite3 "${DEST}" "PRAGMA integrity_check;")
if [ "${INTEGRITY}" != "ok" ]; then
    echo "[restore] ERREUR intégrité après restauration : ${INTEGRITY}"
    exit 2
fi

echo "[restore] OK — restart bibliofelia-web pour prendre en compte."
