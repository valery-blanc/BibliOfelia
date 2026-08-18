# BUG-022 — Sources BnF et BNE : notices vides (parsing SRU)

**Status:** FIXED
**Date:** 2026-08-03

## Symptôme

Tout livre catalogué par scan sur `grand-saconnex.bibliofelia.org` arrivait au
catalogue avec un **titre placeholder** `ISBN:9782017171720 - 03.08.2026 19.23`,
sans auteur ni éditeur — alors que la BnF possède bien la notice. Même effet à
l'enrichissement (aucun champ jamais rempli par BnF/BNE) et sur la passe 2 du
catalogage Excel (candidats systématiquement rejetés, score de similarité nul).

Aucune erreur, aucun log : les sources répondaient HTTP 200 et étaient
simplement considérées comme « n'ayant rien trouvé ».

## Reproduction

Sur n'importe quelle instance, avant le fix :

```python
from apps.catalog.sources import bnf
bnf.lookup("9782017171720")
# → {'title': '', 'authors_text': '', 'publisher': '', 'publication_year': None, …}
# alors que la BnF renvoie <srw:numberOfRecords>1</srw:numberOfRecords>
```

Idem `bne.lookup("9788420412146")` (Don Quichotte, présent à la BNE).

## Cause racine

Les deux sources servent le Dublin Core **imbriqué dans un wrapper** à
l'intérieur de `<srw:recordData>` :

```xml
<srw:recordData>
  <oai_dc:dc>            <!-- BnF ; BNE et Swisscovery : <srw_dc:dc> -->
    <dc:title>La cathédrale de la peur / Irene Adler</dc:title>
    …
```

Or le helper de parsing cherchait en **enfant direct** :

```python
record_data.findall(f"dc:{tag}", _NS)   # ← ne descend pas dans oai_dc:dc
```

→ liste vide pour tous les champs. `lookup_isbn_multi` exige un titre non vide
pour retenir une source, donc les réponses étaient jetées silencieusement, et
`merge_record` (fusion champ par champ) n'avait rien à fusionner.

Le bug affectait les **trois** points d'entrée de chaque source : `lookup`
(ISBN), `lookup_issn` (FEAT-052, périodiques) et `search` (FEAT-050, passe 2
titre + auteur). Conséquence indirecte : sur les instances neuves d'Avignon,
Google Books étant lui aussi hors service (BUG-023), il ne restait qu'OpenLibrary
— d'où 6 notices sur 6 sans titre.

## Fix appliqué

1. `apps/catalog/sources/bnf.py` — `_texts()` cherche en descendant
   (`.//dc:{tag}`), avec le commentaire expliquant l'imbrication.
2. `apps/catalog/sources/_alma_sru.py` (**nouveau**) — le parsing SRU Alma est
   factorisé : BNE et Swisscovery (FEAT-060) tournent tous deux sur Alma et
   répondent à l'identique, donc une seule implémentation, corrigée une fois.
   `bne.py` n'est plus qu'une déclaration d'endpoint.
3. Nettoyage des zones auteur MARC exportées en DC au passage : préfixe de
   liaison `880-01`, identifiant d'autorité `(IDREF)026705370`, code de rôle
   final `aut` — sinon l'auteur enregistré aurait été
   « 880-01 Barilier, Étienne 1947-.... (IDREF)026705370 aut ».

## Vérification

`apps/catalog/tests/test_sources_sru.py` — 11 cas, sur des **captures réelles**
(tronquées) des réponses BnF / BNE / Swisscovery / K10plus, y compris la
structure imbriquée qui causait le bug. Suite complète : 419 tests verts.

Sur l'instance grand-saconnex après déploiement, `lookup_isbn_multi` sur les
6 ISBN du 2026-08-03 : 3 titres retrouvés (contre 0 avant) — les 3 autres
(`9782889790173`, `9782889790081`, `9782342388794`) sont réellement absents de
toutes les sources (petit éditeur suisse récent, auto-édition).

## Section spec impactée

`SPEC_BIBLIOFELIA.md` §6.11 (enrichissement multi-sources) et §6.1 (catalogage
par scan : lookup au scan).
