# FEAT-057 — Guide utilisateur accessible depuis les instances hébergées

**Status:** DONE
**Date:** 2026-08-03

## Context

Le bouton « ? » de la topbar pointe sur `<préfixe app>/docs/`
(`apps/core/context_processors.py:docs_url`). Sur la Box, l'app est servie sous
`/bibliofelia/` et nginx keebee sert le guide MkDocs embarqué → OK. Sur les deux
instances créées à FEAT-056 (Avignon), l'app est servie **à la racine**, donc le
bouton visait `/docs/` — que le nginx d'instance ne connaissait pas : **404**.

Constaté par Val le 2026-08-03 sur `grand-saconnex.bibliofelia.org`.

## Behavior

Sur les trois déploiements, le bouton « ? » ouvre le guide utilisateur dans un
nouvel onglet :

| Instance | URL du guide | Servi par |
|---|---|---|
| canaima (Box, Pi) | `/bibliofelia/docs/` | nginx keebee, guide embarqué (hors-ligne) |
| grand-saconnex | `/docs/` | nginx d'instance → conteneur `bibliofelia-docs` |
| sanjuan | `/docs/` | idem |

`/docs` sans slash final redirige en 301 vers `/docs/`.

## Technical spec

`deploy/avignon/instance-nginx.conf` (copie versionnée du fichier partagé
`~/docker/bibliofelia-instances/nginx.conf`, monté en lecture seule dans
`bo-<instance>-nginx`) :

```nginx
location = /docs { return 301 /docs/; }
location /docs/ {
    resolver 127.0.0.11 valid=30s;          # DNS Docker, résolu à chaque requête
    set $docs_upstream bibliofelia-docs;    # → un restart du conteneur docs ne casse rien
    rewrite ^/docs/(.*)$ /$1 break;
    proxy_pass http://$docs_upstream:80;
    proxy_set_header Host $host;
    proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
}
```

On réutilise le conteneur MkDocs déjà en place pour `docs.bibliofelia.org`
(FEAT-056 phase 3) : les deux nginx d'instance et le conteneur docs partagent le
réseau Docker `web`. Aucune duplication de build, aucun volume supplémentaire.

Le `resolver` + variable est délibéré : sans lui, nginx résout l'IP du conteneur
docs **au démarrage** et sert des 502 après tout redéploiement du guide.

Le même traitement a été appliqué à `location /` (`set $app_upstream web`) après
un incident pendant ce déploiement : nginx avait été rechargé **avant** la
recréation du conteneur `web`, dont l'IP a changé → **502 sur toute
l'instance** jusqu'au redémarrage de nginx. Une instance tenue à distance, sans
maintenance sur site, ne doit pas dépendre de l'ordre de redémarrage des
conteneurs.

Les pages du guide utilisent des chemins **relatifs** pour leurs assets
(`assets/stylesheets/main.<hash>.min.css`) → rien à réécrire.

## Impact on existing code

- `deploy/avignon/instance-nginx.conf` — nouveau (fichier d'infra versionné).
- Aucun changement applicatif : `docs_url` était déjà correct, c'est le serveur
  web qui ne répondait pas.
- La Box n'est pas touchée (guide local embarqué inchangé, contrainte hors-ligne).

## Limite connue (arbitrée avec Val, laissée en l'état)

Le guide contient ~200 liens « vers l'app » écrits en dur en
`/bibliofelia/<lang>/…` (convention posée à FEAT-050/Sprint 20). Ils fonctionnent
sur canaima mais **tombent en 404 sur les instances Avignon**, où l'app est à la
racine. Décision Val 2026-08-03 : on laisse tel quel pour l'instant ; le
correctif envisagé serait un script du thème MkDocs déduisant le préfixe de
l'app depuis l'URL de la page.
