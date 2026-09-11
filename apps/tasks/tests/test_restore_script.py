"""Tests du script `scripts/restore.sh`. SPEC §8.3.

Deuxième moitié de BUG-046 : le script faisait un `gunzip` **inconditionnel**
alors que `run_backup` écrit des sauvegardes NON compressées. Comme la
redirection shell tronque la cible avant que gunzip ne s'exécute, pointer le
script sur la sauvegarde la plus courante du système laissait la base vivante
**vide**.

Le script est exécuté pour de vrai, sur de vrais fichiers. Ces tests sont donc
ignorés là où `bash` et `sqlite3` ne sont pas disponibles — c'est le cas du
poste Windows de développement, pas celui du conteneur où tourne la suite.
"""
from __future__ import annotations

import gzip
import shutil
import sqlite3
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "restore.sh"

pytestmark = pytest.mark.skipif(
    not (shutil.which("bash") and shutil.which("sqlite3")),
    reason="nécessite bash et sqlite3 (conteneur Linux)",
)


def _creer_base(path: Path, valeur: str) -> None:
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


def _lancer(source: Path, data_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), str(source)],
        env={"PATH": "/usr/bin:/bin:/usr/local/bin", "BACKUP_DATA_PATH": str(data_dir)},
        capture_output=True,
        text=True,
    )


@pytest.fixture
def data_dir(tmp_path) -> Path:
    d = tmp_path / "data"
    d.mkdir()
    _creer_base(d / "bibliofelia.sqlite3", "avant")
    return d


class TestRestoreScript:
    def test_archive_non_compressee(self, tmp_path, data_dir):
        """Le cœur du bug : c'est le format que produit `run_backup`, donc de
        loin le plus courant — et c'est celui qui échouait."""
        source = tmp_path / "bibliofelia-20260910T120000Z.sqlite3"
        _creer_base(source, "restauree")

        r = _lancer(source, data_dir)

        assert r.returncode == 0, r.stderr
        assert _lire_marqueur(data_dir / "bibliofelia.sqlite3") == "restauree"

    def test_archive_compressee(self, tmp_path, data_dir):
        brut = tmp_path / "brut.sqlite3"
        _creer_base(brut, "depuis-gz")
        source = tmp_path / "sauvegarde.sqlite3.gz"
        with open(brut, "rb") as fh_in, gzip.open(source, "wb") as fh_out:
            fh_out.write(fh_in.read())

        r = _lancer(source, data_dir)

        assert r.returncode == 0, r.stderr
        assert _lire_marqueur(data_dir / "bibliofelia.sqlite3") == "depuis-gz"

    def test_les_journaux_wal_sont_supprimes(self, tmp_path, data_dir):
        (data_dir / "bibliofelia.sqlite3-wal").write_bytes(b"journal perime")
        (data_dir / "bibliofelia.sqlite3-shm").write_bytes(b"index perime")
        source = tmp_path / "sauvegarde.sqlite3"
        _creer_base(source, "restauree")

        r = _lancer(source, data_dir)

        assert r.returncode == 0, r.stderr
        assert not (data_dir / "bibliofelia.sqlite3-wal").exists()
        assert not (data_dir / "bibliofelia.sqlite3-shm").exists()

    def test_archive_corrompue_laisse_la_base_intacte(self, tmp_path, data_dir):
        """La régression la plus coûteuse : la redirection `>` tronquait la base
        vivante AVANT que la décompression n'échoue."""
        source = tmp_path / "corrompue.sqlite3"
        source.write_bytes(b"ceci n'est pas une base SQLite")

        r = _lancer(source, data_dir)

        assert r.returncode != 0
        assert _lire_marqueur(data_dir / "bibliofelia.sqlite3") == "avant"

    def test_copie_de_securite_creee(self, tmp_path, data_dir):
        source = tmp_path / "sauvegarde.sqlite3"
        _creer_base(source, "restauree")

        _lancer(source, data_dir)

        copies = list(data_dir.glob("bibliofelia.sqlite3.before-restore-*"))
        assert len(copies) == 1
        assert _lire_marqueur(copies[0]) == "avant"

    def test_source_absente(self, tmp_path, data_dir):
        r = _lancer(tmp_path / "inexistante.sqlite3", data_dir)
        assert r.returncode != 0
        assert _lire_marqueur(data_dir / "bibliofelia.sqlite3") == "avant"
