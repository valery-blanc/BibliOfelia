"""Le conteneur de prod doit initialiser autant que celui de dev. SPEC §4.4.

BUG-045 : `setup_roles` et `setup_schedules` tournaient dans
`scripts/dev-entrypoint.sh` mais **pas** dans `scripts/entrypoint.sh`. Rien ne
le signalait — les tests s'exécutent sur une base fabriquée par les migrations
et les fixtures, jamais par l'entrypoint. La divergence a donc vécu jusqu'à ce
qu'on la cherche.

Ces tests lisent les deux scripts comme du texte. C'est rudimentaire, et c'est
exactement le niveau qu'il fallait : le défaut n'était pas dans une logique,
il était dans une ligne absente.
"""
from __future__ import annotations

from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"

# Commandes d'initialisation qui doivent tourner des DEUX côtés. Une commande
# ajoutée à l'entrypoint de dev sans l'être à celui de prod est un bug qui ne se
# verra que sur une Box neuve, en site distant, des mois plus tard.
COMMANDES_REQUISES = ("migrate", "seed_defaults", "setup_roles", "setup_schedules")


@pytest.fixture(scope="module")
def prod() -> str:
    return (SCRIPTS / "entrypoint.sh").read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def dev() -> str:
    return (SCRIPTS / "dev-entrypoint.sh").read_text(encoding="utf-8")


@pytest.mark.parametrize("commande", COMMANDES_REQUISES)
def test_entrypoint_prod_execute_la_commande(prod, commande):
    assert f"manage.py {commande}" in prod, (
        f"`{commande}` manque à l'entrypoint de PROD : sur une Box neuve, "
        f"cette étape d'initialisation n'aura jamais lieu"
    )


@pytest.mark.parametrize("commande", COMMANDES_REQUISES)
def test_entrypoint_dev_execute_la_commande(dev, commande):
    assert f"manage.py {commande}" in dev


def test_les_scripts_sont_en_lf(prod, dev):
    """BUG-040 : un `\\r` dans le shebang fait chercher au noyau un interpréteur
    nommé « /bin/sh\\r », et le conteneur redémarre en boucle sur un
    « No such file or directory » qui désigne un fichier bien présent."""
    for nom in ("entrypoint.sh", "dev-entrypoint.sh"):
        brut = (SCRIPTS / nom).read_bytes()
        assert b"\r\n" not in brut, f"{nom} contient des CRLF"


def test_les_commandes_d_init_tolerent_l_echec(prod):
    """Une commande d'initialisation qui échoue ne doit pas empêcher la Box de
    démarrer : mieux vaut une Box qui tourne avec un réglage manquant qu'une Box
    injoignable sur un site sans maintenance."""
    for commande in ("seed_defaults", "setup_roles", "setup_schedules"):
        ligne = next(
            l for l in prod.splitlines() if f"manage.py {commande}" in l
        )
        assert "|| true" in ligne, f"`{commande}` peut bloquer le démarrage"
