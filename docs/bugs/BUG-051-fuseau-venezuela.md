# BUG-051 — San Juan et Canaima n'affichent pas la même heure

**Statut :** FIXED
**Symptôme :** l'horloge de San Juan et celle de Canaima divergent. Les deux
bibliothèques sont au Venezuela, qui n'a qu'un fuseau, celui de Caracas
(`America/Caracas`, UTC−4 toute l'année).

## Constat (2026-10-26, 17:12 UTC)

| Instance | Horloge mesurée | Réglage |
|---|---|---|
| San Juan | 14:12, `−03` | `TZ=America/Argentina/San_Juan` dans `~/docker/bibliofelia-instances/sanjuan/.env`. Aucun `Setting.timezone` en base. |
| Canaima | 17:12 UTC | pas de `TZ` dans `/opt/edubox/.env`, donc `${TZ:-UTC}` dans le compose. Le Pi lui-même est en `Europe/Zurich` (la Box est en Suisse au moment de la mesure). |
| Grand-Saconnex | 18:12 CET | `Europe/Zurich`. Inchangé : la bibliothèque est en Suisse. |

`America/Argentina/San_Juan` est la province argentine de San Juan (UTC−3),
pas la bibliothèque vénézuélienne.

## Correctif

- San Juan : `TZ=America/Caracas`, conteneurs recréés.
- Canaima : `TZ=America/Caracas` dans `/opt/edubox/.env`, conteneurs BibliOfelia
  recréés. Le fuseau du système du Pi n'est pas modifié : il suit l'endroit où
  la Box se trouve physiquement. L'horloge de la bibliothèque, elle, est celle
  de Caracas.
- Grand-Saconnex reste `Europe/Zurich`.
- Calibre sur la Box garde `America/Lima` : ce n'est pas l'horloge BibliOfelia.

## Spec

SPEC §6.6 (fuseau horaire).
