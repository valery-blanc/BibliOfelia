# BUG-019 — Enrichissement : titres manquants à cause du quota Google Books (429)

Statut : **FIXED** (en test Val) — 2026-06-05

## Symptôme

Après un import Excel d'ISBN (Avancé → Catalogage Excel → Importer) puis un
enrichissement des métadonnées, **beaucoup de notices restent sans titre ni
auteur**, avec le placeholder `ISBN:<isbn> - <jj.mm.aaaa hh.mn>`
(ex. `ISBN:9788419547781 - 05.06.2026 20.20`). Or ces livres avaient bien été
trouvés **par leur ISBN** lors de la vérification Excel (colonne
`TITLE_FOUND_BY_ISBN` remplie, source = Google Books).

## Reproduction / preuve (Box, 2026-06-05)

- Notice 266 : `isbn_13='9788419547781'`, titre = placeholder, 0 auteur.
- Réglage sources = les 4 activées ; job d'enrichissement **#9** lancé avec
  `sources=['openlibrary','google_books','bnf','bne']`, scope `all`, mode
  `fill_missing`.
- Résultat job #9 : total 208, **updated 112, skipped 96, errors 0**. La notice
  266 fait partie des 96 « skipped ».
- Test live : `google_books.lookup('9788419547781')` → **HTTP 429 Too Many
  Requests** (`https://www.googleapis.com/books/v1/volumes?q=isbn:…`).

## Cause racine

L'API Google Books (gratuite) est plafonnée (~100 requêtes/100 s en rafale,
~1000/jour). Entre la vérification Excel, l'import et l'enrichissement, le quota
a été consommé. Pendant le batch d'enrichissement (208 notices, 1 requête GB
chacune), Google Books a commencé à répondre **429**. Le code attrapait
`httpx.HTTPError` et renvoyait `None` **silencieusement** → pas de titre → notice
classée « skipped » → le placeholder restait.

La vérification, lancée plus tôt, était encore sous quota ; l'enrichissement,
lancé après, a tapé le mur. Deux défauts de robustesse :

1. **Aucune gestion du 429** : pas d'espacement des requêtes (throttle) ni de
   réessai (back-off) → on perd des notices dès qu'on approche le quota.
2. **429 = « rien trouvé »** silencieux → invisible pour l'utilisateur et non
   rejouable.

## Fix

`apps/catalog/sources/google_books.py` :
- **Throttle adaptatif** thread-safe (itér. 2, retour Val « c'est lent ») :
  **aucun bridage en régime normal** ; après un 429, espacement
  `_MIN_INTERVAL_SLOW = 1,2 s` pendant `_SLOW_WINDOW = 100 s`
  (`_note_rate_limited`), puis retour automatique à pleine vitesse. Évite de
  pénaliser le cas (fréquent) où le quota est disponible. Partagé verify +
  enrichissement.
- **Back-off sur 429** : `_get_json()` réessaie `_MAX_RETRIES_429 = 3` fois en
  respectant l'en-tête `Retry-After` (sinon délai exponentiel 2→4→8 s, plafonné
  à 30 s). Si le 429 persiste → lève `SourceRateLimited`.

`apps/catalog/enrichment.py` — **saut des notices complètes** (itér. 2) : en
mode FILL_MISSING, `_record_is_complete(record)` (titre réel ≠ placeholder ET
au moins un auteur) → la notice est `skipped` **sans** interroger les sources.
Les re-runs ne retapent que les notices restées incomplètes (ex. rate-limitées
au run précédent) → rapides et économes en quota. Compromis : couverture /
résumé / éditeur d'une notice déjà titrée+auteurée ne sont pas recomplétés en
FILL_MISSING (utiliser OVERWRITE pour une réinterrogation complète).

`apps/catalog/sources/__init__.py` : nouvelle exception `SourceRateLimited` pour
distinguer « quota atteint, réessayer plus tard » de « rien trouvé » (`None`).

`apps/catalog/enrichment.py` :
- `_safe_call` attrape `SourceRateLimited` → sentinel interne `_RATE_LIMITED`.
- `_try_sources(..., with_rate_limit=True)` renvoie `(responses, rate_limited)`
  (le sentinel n'échappe jamais : source rate-limitée = `None` dans le dict).
- `run_enrichment_job` : une notice **sans donnée ET rate-limitée** est comptée
  dans le nouveau champ `EnrichmentJob.rate_limited` (au lieu de `skipped`) avec
  une entrée dédiée dans le rapport. Un re-run ultérieur (quota disponible)
  la complétera.

`apps/catalog/excel_catalog.py` : `_pass1_by_isbn` et `_search_all` propagent un
drapeau `rate_limited` ; `run_verify_job` compte
`ExcelCatalogJob.rate_limited` et marque la colonne `SOURCE_BY_ISBN` à
`RATE_LIMITED` pour les lignes non résolues à cause du quota.

Migration `catalog/0010_enrichmentjob_rate_limited_and_more` (champ
`rate_limited` sur `EnrichmentJob` et `ExcelCatalogJob`).

**UI** : bandeau ambre « Quota Google Books atteint — relancez demain » sur
`enrichment_detail.html` et `excel_catalog/detail.html` quand `rate_limited > 0`,
+ stat dédiée + ligne de rapport « quota atteint — à relancer ».

## Limite résiduelle

Le throttle + back-off absorbent le quota **rafale** (libéré en quelques
secondes). Le quota **journalier** épuisé n'est pas récupérable dans le job : il
faut **relancer le lendemain** (réinitialisation quotidienne, minuit Pacific) —
d'où le bandeau. L'API Google Books étant gratuite, son plafond n'est pas
relevable simplement ; la bonne pratique reste de **consommer moins** et
d'**étaler** le catalogage sur plusieurs jours.

## Tests

`apps/catalog/tests/test_enrichment.py` : `test_try_sources_with_rate_limit_flag`,
`test_run_enrichment_job_counts_rate_limited`,
`test_google_books_backoff_then_raises_rate_limited` (itér. 1) ;
`test_run_enrichment_job_skips_complete_records_in_fill_missing`,
`test_run_enrichment_job_overwrite_does_not_skip_complete`,
`test_run_enrichment_job_does_not_skip_placeholder_title`,
`test_google_books_throttle_is_adaptive` (itér. 2). Suite complète : 373 passed.
