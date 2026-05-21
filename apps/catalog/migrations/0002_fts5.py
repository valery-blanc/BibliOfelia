"""Crée la table virtuelle FTS5 + triggers de synchronisation. SPEC §5.3.

Indexe (title, subtitle, summary, authors_concat) pour la recherche plein-texte.
L'agrégation des auteurs se fait dans les triggers via un sous-SELECT
group_concat sur la table M2M `catalog_bibliographicrecord_authors`.
"""
from __future__ import annotations

from django.db import migrations


CREATE_FTS5 = """
CREATE VIRTUAL TABLE IF NOT EXISTS catalog_record_fts USING fts5(
    title,
    subtitle,
    summary,
    authors_concat,
    record_id UNINDEXED,
    tokenize = "unicode61 remove_diacritics 2"
);
"""

CREATE_TRIGGERS = [
    """
    CREATE TRIGGER IF NOT EXISTS catalog_record_fts_ai
    AFTER INSERT ON catalog_bibliographicrecord BEGIN
        INSERT INTO catalog_record_fts(title, subtitle, summary, authors_concat, record_id)
        VALUES (
            new.title,
            new.subtitle,
            new.summary,
            (
                SELECT COALESCE(group_concat(a.full_name, ' '), '')
                FROM catalog_author a
                JOIN catalog_bibliographicrecord_authors ra ON ra.author_id = a.id
                WHERE ra.bibliographicrecord_id = new.id
            ),
            new.id
        );
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS catalog_record_fts_ad
    AFTER DELETE ON catalog_bibliographicrecord BEGIN
        DELETE FROM catalog_record_fts WHERE record_id = old.id;
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS catalog_record_fts_au
    AFTER UPDATE ON catalog_bibliographicrecord BEGIN
        DELETE FROM catalog_record_fts WHERE record_id = old.id;
        INSERT INTO catalog_record_fts(title, subtitle, summary, authors_concat, record_id)
        VALUES (
            new.title,
            new.subtitle,
            new.summary,
            (
                SELECT COALESCE(group_concat(a.full_name, ' '), '')
                FROM catalog_author a
                JOIN catalog_bibliographicrecord_authors ra ON ra.author_id = a.id
                WHERE ra.bibliographicrecord_id = new.id
            ),
            new.id
        );
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS catalog_record_fts_m2m_ai
    AFTER INSERT ON catalog_bibliographicrecord_authors BEGIN
        DELETE FROM catalog_record_fts WHERE record_id = new.bibliographicrecord_id;
        INSERT INTO catalog_record_fts(title, subtitle, summary, authors_concat, record_id)
        SELECT
            r.title,
            r.subtitle,
            r.summary,
            (
                SELECT COALESCE(group_concat(a.full_name, ' '), '')
                FROM catalog_author a
                JOIN catalog_bibliographicrecord_authors ra ON ra.author_id = a.id
                WHERE ra.bibliographicrecord_id = r.id
            ),
            r.id
        FROM catalog_bibliographicrecord r
        WHERE r.id = new.bibliographicrecord_id;
    END;
    """,
    """
    CREATE TRIGGER IF NOT EXISTS catalog_record_fts_m2m_ad
    AFTER DELETE ON catalog_bibliographicrecord_authors BEGIN
        DELETE FROM catalog_record_fts WHERE record_id = old.bibliographicrecord_id;
        INSERT INTO catalog_record_fts(title, subtitle, summary, authors_concat, record_id)
        SELECT
            r.title,
            r.subtitle,
            r.summary,
            (
                SELECT COALESCE(group_concat(a.full_name, ' '), '')
                FROM catalog_author a
                JOIN catalog_bibliographicrecord_authors ra ON ra.author_id = a.id
                WHERE ra.bibliographicrecord_id = r.id
            ),
            r.id
        FROM catalog_bibliographicrecord r
        WHERE r.id = old.bibliographicrecord_id;
    END;
    """,
]


DROP_FTS5 = [
    "DROP TRIGGER IF EXISTS catalog_record_fts_m2m_ad;",
    "DROP TRIGGER IF EXISTS catalog_record_fts_m2m_ai;",
    "DROP TRIGGER IF EXISTS catalog_record_fts_au;",
    "DROP TRIGGER IF EXISTS catalog_record_fts_ad;",
    "DROP TRIGGER IF EXISTS catalog_record_fts_ai;",
    "DROP TABLE IF EXISTS catalog_record_fts;",
]


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=[CREATE_FTS5, *CREATE_TRIGGERS],
            reverse_sql=DROP_FTS5,
        ),
    ]
