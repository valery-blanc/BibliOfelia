"""Tests de sauvegarde et restauration. SPEC §8.

Couvrent BUG-046 : la restauration laissait en place les journaux WAL de la base
remplacée, que SQLite rejouait ensuite **par-dessus** la base restaurée.

Ces tests manipulent de vrais fichiers SQLite en mode WAL plutôt que des mocks :
c'est précisément le comportement du moteur — et non celui de notre code — qui
faisait le dégât, et un mock l'aurait masqué.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from apps.tasks.backup import _drop_wal_sidecars, restore_from_file


def _creer_base(path: Path, valeur: str) -> None:
    """Crée une base en mode WAL contenant une ligne repérable."""
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("CREATE TABLE marqueur (valeur TEXT);")
    conn.execute("INSERT INTO marqueur VALUES (?);", (valeur,))
    conn.commit()
    conn.close()


def _lire_marqueur(path: Path) -> str:
    conn = sqlite3.connect(str(path))
    try:
        return conn.execute("SELECT valeur FROM marqueur;").fetchone()[0]
    finally:
        conn.close()


def _ecrire_sans_checkpoint(path: Path, valeur: str) -> sqlite3.Connection:
    """Écrit une transaction qui reste dans le journal WAL.

    La connexion est **rendue ouverte** : la fermer déclencherait un checkpoint
    qui fusionnerait le journal dans le fichier principal, et il n'y aurait plus
    rien à démontrer.
    """
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA wal_autocheckpoint=0;")
    conn.execute("UPDATE marqueur SET valeur = ?;", (valeur,))
    conn.commit()
    return conn


class TestDropWalSidecars:
    def test_supprime_les_deux_journaux(self, tmp_path):
        db = tmp_path / "base.sqlite3"
        db.write_bytes(b"")
        wal = tmp_path / "base.sqlite3-wal"
        shm = tmp_path / "base.sqlite3-shm"
        wal.write_bytes(b"journal")
        shm.write_bytes(b"index")

        _drop_wal_sidecars(db)

        assert not wal.exists()
        assert not shm.exists()
        assert db.exists(), "le fichier principal ne doit pas être touché"

    def test_ne_leve_pas_si_absents(self, tmp_path):
        db = tmp_path / "base.sqlite3"
        db.write_bytes(b"")
        _drop_wal_sidecars(db)  # ne doit pas lever

    def test_ne_confond_pas_avec_un_suffixe(self, tmp_path):
        """`with_suffix` aurait transformé `base.sqlite3` en `base-wal` ; le nom
        correct est `base.sqlite3-wal`."""
        db = tmp_path / "base.sqlite3"
        db.write_bytes(b"")
        piege = tmp_path / "base-wal"
        piege.write_bytes(b"a garder")

        _drop_wal_sidecars(db)

        assert piege.exists()


@pytest.mark.django_db
class TestRunBackup:
    """L'archive produite doit être un fichier **autonome**.

    Constaté sur la Box le 2026-09-10 : chaque sauvegarde laissait à côté d'elle
    un journal `-wal` de 140 Ko. `with sqlite3.connect(...)` valide la
    transaction mais **ne ferme pas** la connexion — un piège de l'API, pas de
    notre code. Or `_rotate` promeut l'archive vers daily/weekly/monthly par un
    `copy2` du seul fichier principal : les copies promues pouvaient être
    amputées de ce que contenait le journal.
    """

    @pytest.fixture
    def sauvegarde(self, tmp_path, settings):
        from apps.tasks.backup import run_backup

        source = tmp_path / "bibliofelia.sqlite3"
        _creer_base(source, "donnees")
        settings.DATABASE_PATH = str(source)
        settings.BACKUP_USB_PATH = str(tmp_path / "backup")
        return run_backup

    def test_l_archive_n_a_pas_de_journal_a_cote(self, sauvegarde):
        resultat = sauvegarde()

        assert resultat.status == "ok", resultat.error
        archive = Path(resultat.db_path)
        assert archive.exists()
        assert not archive.with_name(archive.name + "-wal").exists()
        assert not archive.with_name(archive.name + "-shm").exists()

    def test_l_archive_seule_contient_toutes_les_donnees(self, sauvegarde):
        """La preuve qui compte : l'archive est copiée **seule** ailleurs, puis
        relue. C'est ce que fait `_rotate`, et c'est ce que fera l'opérateur qui
        emporte le fichier sur une clé."""
        resultat = sauvegarde()
        archive = Path(resultat.db_path)

        ailleurs = archive.parent.parent / "emportee.sqlite3"
        ailleurs.write_bytes(archive.read_bytes())

        assert _lire_marqueur(ailleurs) == "donnees"

    def test_promotion_journaliere_coherente(self, sauvegarde):
        resultat = sauvegarde(force_daily=True)

        assert "daily" in resultat.rotated
        assert _lire_marqueur(Path(resultat.rotated["daily"])) == "donnees"


@pytest.mark.django_db
class TestRestoreFromFile:
    def test_restaure_le_contenu_de_l_archive(self, tmp_path, settings):
        cible = tmp_path / "bibliofelia.sqlite3"
        archive = tmp_path / "archive.sqlite3"
        _creer_base(cible, "avant")
        _creer_base(archive, "archive")
        settings.DATABASE_PATH = str(cible)

        restore_from_file(str(archive))

        assert _lire_marqueur(cible) == "archive"

    def test_le_journal_de_l_ancienne_base_ne_ressuscite_pas(self, tmp_path, settings):
        """Le cœur de BUG-046.

        Une transaction encore dans le journal WAL au moment de la restauration
        — le cas normal d'une base vivante — réapparaissait après coup : SQLite
        rejouait le journal orphelin par-dessus la base restaurée. C'est
        exactement l'enregistrement que l'on cherchait à annuler qui revenait.
        """
        cible = tmp_path / "bibliofelia.sqlite3"
        archive = tmp_path / "archive.sqlite3"
        _creer_base(cible, "avant")
        _creer_base(archive, "archive")
        settings.DATABASE_PATH = str(cible)

        # Une écriture qui reste dans le -wal, connexion laissée ouverte.
        conn = _ecrire_sans_checkpoint(cible, "a-annuler")
        try:
            assert (tmp_path / "bibliofelia.sqlite3-wal").exists(), (
                "le test lui-même est invalide s'il n'y a pas de journal"
            )

            restore_from_file(str(archive))

            assert not (tmp_path / "bibliofelia.sqlite3-wal").exists()
            assert not (tmp_path / "bibliofelia.sqlite3-shm").exists()
            assert _lire_marqueur(cible) == "archive", (
                "le journal de l'ancienne base a été rejoué sur la base restaurée"
            )
        finally:
            conn.close()

    def test_copie_de_securite_coherente(self, tmp_path, settings):
        """La copie prise avant écrasement doit contenir les transactions encore
        dans le journal — un `cp` du seul fichier principal les perdrait, et le
        filet de sécurité serait incomplet au moment précis où il sert."""
        cible = tmp_path / "bibliofelia.sqlite3"
        archive = tmp_path / "archive.sqlite3"
        _creer_base(cible, "avant")
        _creer_base(archive, "archive")
        settings.DATABASE_PATH = str(cible)

        conn = _ecrire_sans_checkpoint(cible, "dans-le-journal")
        try:
            restore_from_file(str(archive))
        finally:
            conn.close()

        sauvegardes = list(tmp_path.glob("bibliofelia.pre-restore.*"))
        assert len(sauvegardes) == 1
        assert _lire_marqueur(sauvegardes[0]) == "dans-le-journal"

    def test_archive_corrompue_ne_detruit_pas_la_base(self, tmp_path, settings):
        cible = tmp_path / "bibliofelia.sqlite3"
        _creer_base(cible, "precieux")
        settings.DATABASE_PATH = str(cible)

        archive = tmp_path / "corrompue.sqlite3"
        archive.write_bytes(b"ceci n'est pas une base SQLite")

        with pytest.raises(Exception):
            restore_from_file(str(archive))

        assert _lire_marqueur(cible) == "precieux"

    def test_archive_absente(self, tmp_path, settings):
        settings.DATABASE_PATH = str(tmp_path / "bibliofelia.sqlite3")
        with pytest.raises(FileNotFoundError):
            restore_from_file(str(tmp_path / "inexistante.sqlite3"))

    def test_restaure_depuis_un_gz(self, tmp_path, settings):
        import gzip

        cible = tmp_path / "bibliofelia.sqlite3"
        source = tmp_path / "source.sqlite3"
        _creer_base(cible, "avant")
        _creer_base(source, "depuis-gz")
        settings.DATABASE_PATH = str(cible)

        archive = tmp_path / "archive.sqlite3.gz"
        with open(source, "rb") as brut, gzip.open(archive, "wb") as comprime:
            comprime.write(brut.read())

        restore_from_file(str(archive))

        assert _lire_marqueur(cible) == "depuis-gz"
