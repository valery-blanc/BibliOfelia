# BUG-040 — CRLF dans les shebangs : BibliOfelia en boucle de redémarrage

**Statut** : `FIXED` (commit `2832c15`, 2026-08-26)
**Découvert** : 2026-08-26, en remontant la Ofelia Box sur une carte SD neuve
**Section spec impactée** : §11.1 (image Docker), §11.5 (mise à jour logicielle)

## Symptôme

Après restauration de la Box sur carte neuve, le conteneur `edubox-bibliofelia`
redémarre en boucle avec le **code de sortie 127** :

```
[FATAL tini] exec /app/scripts/entrypoint.sh failed: No such file or directory
```

...alors que le fichier **existe** et qu'il est **exécutable**. Une heure perdue
sur ce message avant d'en comprendre la cible.

## Cause racine

Le message ne parle pas du script mais de **l'interpréteur de son shebang**. Le
fichier commençait par `#!/bin/sh\r` : le noyau Linux cherche alors un binaire
littéralement nommé `/bin/sh\r`, qui n'existe pas.

L'origine est côté dépôt, pas côté Box :

- le poste de développement est sous **Windows avec `core.autocrlf = true`** ;
- le dépôt BibliOfelia n'avait **aucun `.gitattributes`** ;
- `git archive` — utilisé pour exporter les sources vers la Box — **applique les
  filtres de conversion de fin de ligne**.

Résultat : **680 fichiers exportés en CRLF**, dont **5 scripts à shebang**.

## Reproduction

```bash
head -1 scripts/entrypoint.sh | od -c     # ...  \r  \n  → CRLF
```

## Fix

Ajout d'un **`.gitattributes`** à la racine imposant `text eol=lf` (et `binary`
pour les formats qui ne doivent jamais être convertis). Les sources exportées
partent désormais en LF quel que soit le réglage `autocrlf` du poste.

## À retenir

⚠️ **« No such file or directory » sur un script qui existe = presque toujours un
CRLF dans le shebang.** Vérifier avec `head -1 <script> | od -c` avant de
chercher ailleurs. Le message désigne l'interpréteur, jamais le script.

## Portée

Ce bug est **propre au dépôt BibliOfelia**. Le défaut jumeau découvert la même
nuit — **BUG-039**, la restauration qui réinstallait du code périmé — concerne
`RESTAURER-OFELIA.sh` et vit donc dans le dépôt **ofeliabox**, pas ici.
