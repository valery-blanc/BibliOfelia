# FEAT-060 — Sources européennes additionnelles (Swisscovery, K10plus)

**Status:** DONE
**Date:** 2026-08-03

## Context

Question Val 2026-08-03 : « J'ai des livres en italien, allemand, portugais :
est-ce qu'on peut trouver l'équivalent de la BnF pour les principales langues
européennes ? »

Le registre comptait 4 sources : OpenLibrary (couverture anglophone), Google
Books, BnF (FR), BNE (ES). Les livres suisses, allemands et italiens tombaient
donc souvent à côté — cas concret : `9782882415417` (Barilier, *Muses*, Éditions
Zoé) introuvable dans les 4.

## Candidats évalués (endpoints testés en direct le 2026-08-03)

| Source | Protocole | Clé | Verdict |
|---|---|---|---|
| **Swisscovery / SLSP** | SRU Alma DC, `alma.isbn` / `alma.issn` | non | ✅ retenu — trouve *Muses* que personne d'autre n'a. Réseau des bibliothèques suisses, fr/de/it |
| **K10plus** | SRU, `pica.isb` / `pica.tit` | non | ✅ retenu — catalogue collectif DE/AT/CH |
| DNB (Allemagne) | SRU | **oui** (`accessToken`) | écarté : demande d'accès requise, K10plus couvre le même besoin |
| SBN / ICCU (Italie) | — | — | écarté : pas d'endpoint SRU public (`opac.sbn.it/sru` renvoie l'OPAC HTML) |
| PORBASE / BNP (Portugal) | — | — | écarté : SRU en 404 (`/sru` et `view/sru/351BNP_INST`) |

Pour l'**italien** et le **portugais**, le meilleur levier reste donc Google
Books (avec sa clé, cf. BUG-023) — vérifié : `9788804799849` → « La figlia della
dea della luna ».

## Behavior

Deux sources s'ajoutent partout où le registre est consommé, sans nouvelle
interface :

- **scan de catalogage** (`lookup_isbn_multi`) — interrogées en parallèle avec
  les autres, ordre de préférence
  `openlibrary → google_books → bnf → bne → swisscovery → k10plus` ;
- **périodiques ISSN** (`lookup_issn_multi`) — Swisscovery seulement (Alma
  indexe l'ISSN ; côté K10plus `pica.iss` ne répond pas) ;
- **catalogage Excel passe 2** (`SEARCHES`, recherche titre + auteur) ;
- **enrichissement** — 2 cases à cocher supplémentaires (FEAT-059).

## Technical spec

- `apps/catalog/sources/_alma_sru.py` (nouveau) — client SRU Alma générique
  (`AlmaSruSource`), partagé par BNE et Swisscovery : mêmes URL, même schéma DC,
  même bruit MARC à nettoyer. Créé en réparant BUG-022 plutôt que de dupliquer
  un parsing déjà cassé une fois.
- `apps/catalog/sources/swisscovery.py` — endpoint
  `https://swisscovery.slsp.ch/view/sru/41SLSP_NETWORK`.
- `apps/catalog/sources/k10plus.py` — endpoint `https://sru.k10plus.de/opac-de-627`.
  Particularité : ni `dc:creator` ni `dc:publisher`, tout est en
  `dc:contributor` suffixé du rôle — `(Verlag)` → éditeur, le reste → auteurs.
  `dc:description` y est la mention de responsabilité, pas un résumé : non
  remontée comme `summary`.
- `apps/catalog/sources/__init__.py` — inscriptions dans `SOURCES`, `SEARCHES`,
  `ISSN_SOURCES` (Swisscovery seulement), `SOURCE_LABELS`.
- `apps/catalog/openlibrary.py` — `_MULTI_SOURCE_ORDER` et `_ISSN_SOURCE_ORDER`.

Aucune migration. Coût par scan : 2 requêtes HTTP de plus, mais lancées dans le
même `ThreadPoolExecutor` — la latence reste celle de la source la plus lente.

## Impact on existing code

- Une source muette ou en panne est déjà neutre (`None`, jamais d'exception).
- Tests : `apps/catalog/tests/test_sources_sru.py` (Swisscovery : nettoyage du
  bruit MARC ; K10plus : routage des contributeurs par rôle ; registres).
