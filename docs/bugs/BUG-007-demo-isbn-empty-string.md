# BUG-007 — `install_demo()` 500 : ISBN vide collisionne sur contrainte UNIQUE

Statut : **FIXED** (2026-05-22)
Sprint : 4 (FEAT-015 — données de démo)
Découverte : test Val du wizard BibliOfelia sur la Pi (FEAT-020 / Task #18)
Spec impactée : `SPEC_BIBLIOFELIA.md` §11.4 (données de démo)

## Symptôme

À l'étape 8 du wizard de premier démarrage, si l'utilisateur coche
« Importer le jeu de démo », la finalisation échoue en `500 Internal Server
Error` :

```
django.db.utils.IntegrityError: UNIQUE constraint failed:
  catalog_bibliographicrecord.isbn_13
  File "/app/apps/setup/demo.py", line 82, in install_demo
    rec = BibliographicRecord.objects.create(...)
```

## Cause racine

`apps/setup/demo.py` ligne 87 :

```python
isbn_13="" if rng.random() < 0.3 else f"978{rng.randint(10**9, 10**10 - 1)}",
```

Le champ `BibliographicRecord.isbn_13` est défini `null=True` avec une
contrainte UNIQUE partielle `WHERE isbn_13 IS NOT NULL` (cf.
`apps/catalog/models.py:175`). Cette contrainte est conçue pour autoriser
plusieurs notices sans ISBN — à condition que l'absence soit modélisée par
`NULL`, pas par la chaîne vide `""`. Or SQLite traite `""` comme une valeur
ordinaire : la contrainte UNIQUE s'applique, et la 2ᵉ notice tirée avec
`""` (probabilité 30 % × 50 notices ≈ certaine, et reproductible avec
`Random(42)`) lève une `IntegrityError`.

## Fix

Remplacer `""` par `None` dans `demo.py`. La contrainte partielle laisse
alors passer plusieurs `NULL`, comme prévu par le modèle.

## Test

- Wizard BibliOfelia avec l'option démo cochée → arrive à l'écran de
  récapitulatif, recovery_key affichée.
- 50 notices créées dont environ 15 sans ISBN.
