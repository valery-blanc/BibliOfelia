#!/usr/bin/env bash
# Sprint 15 Task 6 — Deploiement du guide utilisateur (site statique MkDocs)
# vers la Ofelia Box.
#
# Usage : ./docs/user-guide/scripts/deploy_pi.sh
#
# Prerequis :
#   - .venv-doc operationnel avec MkDocs et plugins (cf. requirements-doc.txt)
#   - cle SSH ~/.ssh/id_ed25519_pi
#   - location nginx /bibliofelia/docs/ deja declaree dans
#     C:\WORK\keebee\nginx\conf.d\ofelia-locations.inc
set -euo pipefail

PI_USER="ofelia"
PI_HOST="192.168.0.147"
PI_TARGET="/var/lib/bibliofelia-docs"
LOCAL_SITE="$(dirname "$0")/../site"
SSH_KEY="$HOME/.ssh/id_ed25519_pi"

cd "$(dirname "$0")/.."

echo "==> Build du site (4 langues)..."
../../.venv-doc/Scripts/python.exe -m mkdocs build --strict || {
    echo "ERREUR : build mkdocs --strict a echoue. Corrigez avant de deployer."
    exit 1
}

echo "==> Verification connectivite Pi..."
ssh -i "$SSH_KEY" -o ConnectTimeout=5 "$PI_USER@$PI_HOST" "echo connect_ok" >/dev/null

echo "==> Creation du dossier cible sur la Pi (si absent)..."
ssh -i "$SSH_KEY" "$PI_USER@$PI_HOST" "sudo mkdir -p $PI_TARGET && sudo chown $PI_USER:$PI_USER $PI_TARGET"

echo "==> rsync du site vers $PI_USER@$PI_HOST:$PI_TARGET ..."
rsync -avz --delete -e "ssh -i $SSH_KEY" \
    "./site/" \
    "$PI_USER@$PI_HOST:$PI_TARGET/"

echo "==> Reload nginx..."
ssh -i "$SSH_KEY" "$PI_USER@$PI_HOST" "sudo docker exec edubox-nginx nginx -t && sudo docker exec edubox-nginx nginx -s reload"

echo
echo "OK — guide deploye. URLs accessibles :"
echo "  - http://ofelia.local/bibliofelia/docs/        (FR)"
echo "  - http://ofelia.local/bibliofelia/docs/en/     (EN)"
echo "  - http://ofelia.local/bibliofelia/docs/es/     (ES)"
echo "  - http://ofelia.local/bibliofelia/docs/mg/     (MG)"
