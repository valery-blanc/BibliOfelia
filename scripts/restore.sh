#!/bin/bash
# Restauration BibliOfelia depuis sauvegarde locale.
# Usage : ./restore.sh <fichier.sqlite3[.gz]>
set -euo pipefail

SRC="${1:-}"
DEST="${BACKUP_DATA_PATH:-/app/data}/bibliofelia.sqlite3"
TMP="${DEST}.restoring"

if [ -z "${SRC}" ] || [ ! -f "${SRC}" ]; then
    echo "Usage : $0 <chemin/vers/sauvegarde.sqlite3[.gz]>"
    exit 1
fi

echo "[restore] BD cible : ${DEST}"

# Le format est DÉTECTÉ, jamais supposé : `apps/tasks/backup.py::run_backup`
# (tâche horaire, bouton « Sauvegarder maintenant », `manage.py run_backup`)
# écrit des .sqlite3 NON compressés dans /backup/db/hourly/ ; seul
# `scripts/backup.sh` gzippe. Un `gunzip -c` inconditionnel échouait donc sur la
# sauvegarde la plus courante — et comme la redirection tronque la cible AVANT
# que gunzip ne s'exécute, elle laissait la base vivante vide.
echo "[restore] extraction vers un fichier temporaire..."
rm -f "${TMP}"
if gzip -t "${SRC}" 2>/dev/null; then
    gunzip -c "${SRC}" > "${TMP}"
else
    cp "${SRC}" "${TMP}"
fi

echo "[restore] vérification intégrité de l'archive..."
INTEGRITY=$(sqlite3 "${TMP}" "PRAGMA integrity_check;")
if [ "${INTEGRITY}" != "ok" ]; then
    echo "[restore] ERREUR intégrité de l'archive : ${INTEGRITY}"
    echo "[restore] la base actuelle n'a pas été touchée."
    rm -f "${TMP}"
    exit 2
fi

echo "[restore] copie de sécurité de la base actuelle..."
if [ -f "${DEST}" ]; then
    SAFETY="${DEST}.before-restore-$(date -u +%Y%m%dT%H%M%SZ)"
    # `.backup` et non `cp` : en mode WAL le fichier principal seul ne contient
    # pas les transactions restées dans le journal.
    sqlite3 "${DEST}" ".backup '${SAFETY}'"
    echo "[restore] copie de sécurité : ${SAFETY}"
fi

mv -f "${TMP}" "${DEST}"
# Sans ça, SQLite rejoue le journal de l'ANCIENNE base par-dessus la nouvelle.
rm -f "${DEST}-wal" "${DEST}-shm"

echo "[restore] OK — redémarrer bibliofelia (web ET worker) pour prendre en compte."
