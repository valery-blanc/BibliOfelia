"""Sauvegardes locales + cloud. SPEC §8.

`run_backup()` produit une copie cohérente de la BD SQLite et l'enregistre
dans `Setting["last_backup"]` pour que le dashboard puisse alerter (§6.6).
La rotation 24h / 7j / 4w / 12m est gérée par les sous-dossiers
`hourly/daily/weekly/monthly` (cf. `scripts/backup.sh` qui fait la même
chose côté container backup quand il est déployé).

`run_backup` est appelé par :
- la commande `manage.py run_backup`
- la tâche django-q2 horaire (enregistrée par `apps.tasks.scheduling`)
- le bouton « Sauvegarder maintenant » dans /admin/settings/backup/.
"""
from __future__ import annotations

import logging
import os
import shutil
import sqlite3
import subprocess
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path

from django.conf import settings

logger = logging.getLogger(__name__)


@dataclass
class BackupResult:
    at: datetime
    status: str  # "ok" | "error" | "skipped"
    db_path: str = ""
    size_bytes: int = 0
    media_synced: bool = False
    cloud_pushed: bool = False
    error: str = ""
    rotated: dict = field(default_factory=dict)


def run_backup(force_daily: bool = False, force_cloud: bool = False) -> BackupResult:
    """Effectue une sauvegarde. Retourne `BackupResult` et met à jour
    `Setting["last_backup"]`. Ne lève jamais d'exception — toute erreur est
    capturée et reflétée dans `status="error"`.
    """
    from apps.core.models import Setting

    now = datetime.now(timezone.utc)
    result = BackupResult(at=now, status="ok")

    cfg = Setting.get("backup_config", {}) or {}
    dest_path = Path(cfg.get("usb_path") or settings.BACKUP_USB_PATH)
    src_db = Path(settings.DATABASE_PATH)

    if not src_db.exists():
        result.status = "error"
        result.error = f"BD introuvable: {src_db}"
        _persist(result)
        return result

    try:
        dest_path.mkdir(parents=True, exist_ok=True)
        hourly = dest_path / "db" / "hourly"
        hourly.mkdir(parents=True, exist_ok=True)
        ts = now.strftime("%Y%m%dT%H%M%SZ")
        out = hourly / f"bibliofelia-{ts}.sqlite3"

        # 1. Copie cohérente via sqlite3 .backup
        with sqlite3.connect(str(src_db)) as src, sqlite3.connect(str(out)) as dst:
            src.backup(dst)
        # 2. Vérif intégrité
        with sqlite3.connect(str(out)) as check:
            cur = check.execute("PRAGMA integrity_check;")
            row = cur.fetchone()
            integrity = (row[0] if row else "") or ""
            if integrity != "ok":
                out.unlink(missing_ok=True)
                raise RuntimeError(f"integrity_check: {integrity!r}")

        result.db_path = str(out)
        result.size_bytes = out.stat().st_size

        # 3. Promotions (daily / weekly / monthly)
        result.rotated = _rotate(dest_path, out, now, force_daily=force_daily)

        # 4. rsync media (quotidien)
        if (now.hour == 2 or force_daily) and settings.MEDIA_ROOT and Path(settings.MEDIA_ROOT).exists():
            media_dest = dest_path / "media"
            media_dest.mkdir(parents=True, exist_ok=True)
            try:
                _rsync_media(Path(settings.MEDIA_ROOT), media_dest)
                result.media_synced = True
            except Exception as exc:
                logger.warning("rsync media KO : %s", exc)

        # 5. Cloud (opt-in)
        if cfg.get("cloud_enabled") and (now.hour == 3 or force_cloud):
            remote = cfg.get("cloud_remote", "")
            if remote:
                try:
                    _push_cloud(dest_path, remote)
                    result.cloud_pushed = True
                except Exception as exc:
                    logger.warning("Cloud sync KO : %s", exc)

    except Exception as exc:
        result.status = "error"
        result.error = str(exc)
        logger.exception("Backup failed")

    _persist(result)
    return result


def _persist(result: BackupResult) -> None:
    from apps.core.models import Setting

    Setting.set("last_backup", {
        "at": result.at.isoformat(),
        "status": result.status,
        "db_path": result.db_path,
        "size_bytes": result.size_bytes,
        "media_synced": result.media_synced,
        "cloud_pushed": result.cloud_pushed,
        "error": result.error,
    }, "Trace de la dernière sauvegarde")


def _rotate(dest: Path, src: Path, now: datetime, force_daily: bool = False) -> dict:
    """Copie l'archive vers daily/weekly/monthly selon l'heure/jour et
    supprime les fichiers obsolètes (24h / 7j / 35j / 400j)."""
    promoted: dict = {}
    daily = dest / "db" / "daily"
    weekly = dest / "db" / "weekly"
    monthly = dest / "db" / "monthly"
    for d in (daily, weekly, monthly):
        d.mkdir(parents=True, exist_ok=True)

    if force_daily or now.hour == 2:
        target = daily / src.name
        shutil.copy2(src, target)
        promoted["daily"] = str(target)
        if force_daily or now.isoweekday() == 1:
            target = weekly / src.name
            shutil.copy2(src, target)
            promoted["weekly"] = str(target)
        if force_daily or now.day == 1:
            target = monthly / src.name
            shutil.copy2(src, target)
            promoted["monthly"] = str(target)

    _prune(dest / "db" / "hourly", days=1)
    _prune(daily, days=7)
    _prune(weekly, days=35)
    _prune(monthly, days=400)
    return promoted


def _prune(folder: Path, days: int) -> None:
    cutoff = datetime.now().timestamp() - days * 86400
    if not folder.exists():
        return
    for entry in folder.iterdir():
        if entry.is_file() and entry.stat().st_mtime < cutoff:
            entry.unlink(missing_ok=True)


def _rsync_media(src: Path, dest: Path) -> None:
    """rsync si dispo (Linux), sinon copytree (Windows dev)."""
    if shutil.which("rsync"):
        subprocess.run(
            ["rsync", "-a", "--delete", str(src) + "/", str(dest) + "/"],
            check=True,
            capture_output=True,
        )
        return
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(src, dest)


def _push_cloud(dest: Path, remote: str) -> None:
    """rclone sync local → remote. Requiert `rclone` configuré dans
    l'environnement (passphrase de chiffrement gérée par rclone crypt côté
    config — pas dans BibliOfelia)."""
    rclone = shutil.which("rclone")
    if not rclone:
        raise RuntimeError("rclone non installé")
    subprocess.run(
        [rclone, "sync", str(dest), remote, "--max-age", "35d"],
        check=True,
        capture_output=True,
    )


# ----------------------------------------------------------------------
# Restauration
# ----------------------------------------------------------------------
def restore_from_file(archive_path: str) -> None:
    """Restaure la BD depuis un fichier `.sqlite3` (ou `.sqlite3.gz`).

    Stoppe Django de manière coopérative : recommandation d'usage hors web
    actif (CLI ou wizard). Aucune protection concurrence : à l'admin de couper
    le service.
    """
    import gzip

    target = Path(settings.DATABASE_PATH)
    src = Path(archive_path)
    if not src.exists():
        raise FileNotFoundError(archive_path)

    tmp = target.with_suffix(".restoring")
    if str(src).endswith(".gz"):
        with gzip.open(src, "rb") as fh_in, open(tmp, "wb") as fh_out:
            shutil.copyfileobj(fh_in, fh_out)
    else:
        shutil.copy2(src, tmp)

    # Vérification intégrité avant remplacement
    with sqlite3.connect(str(tmp)) as check:
        cur = check.execute("PRAGMA integrity_check;")
        row = cur.fetchone()
        if not row or row[0] != "ok":
            tmp.unlink(missing_ok=True)
            raise RuntimeError(f"integrity_check sur l'archive: {row[0] if row else 'KO'}")

    # Backup de la BD courante avant écrasement
    if target.exists():
        backup_now = target.with_suffix(f".pre-restore.{int(datetime.now().timestamp())}")
        shutil.copy2(target, backup_now)
    os.replace(tmp, target)
