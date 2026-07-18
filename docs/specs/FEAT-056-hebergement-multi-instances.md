# FEAT-056 — Hébergement multi-instances + domaine bibliofelia.org

**Status:** DÉPLOYÉ — test fonctionnel Val en attente (phases 1-5 en place et vérifiées HTTP/TLS)
**Date:** 2026-07-18

## Réalisé (2026-07-18)

Tout est additif sur Avignon (aucun conteneur/site existant modifié ; régression OK :
noema/carradio/enpleinproust/cv/ofelia.zitoon = 200. Les 504 supabase/swisskap = service
Tulear éteint, pré-existant, sans rapport).

- **Phase 1** — `~/docker/traefik/dynamic/canaima.bibliofelia.org.yml` → Pi:80 ; Pi `.env`
  `BIBLIOFELIA_CSRF_TRUSTED_ORIGINS` += `https://canaima.bibliofelia.org`, conteneur recréé.
  `https://canaima.bibliofelia.org/bibliofelia/` = 200, cert OK. `ofelia.zitoon.com` conservé.
- **Phase 2** — `bibliofelia.org-redirect.yml` : apex+www → 301 → ofeliainternational.org/what-we-do/.
- **Phase 3** — `~/docker/bibliofelia-docs/` (image nginx statique MkDocs). `docs.bibliofelia.org` = 200.
  Doc **locale embarquée sur la Box inchangée** (le miroir en ligne est en plus).
- **Phase 4** — `~/docker/bibliofelia-instances/{sanjuan,grand-saconnex}/` : image
  `ofelia/bibliofelia:avignon` (buildée 1×), stacks web(gunicorn)+worker(qcluster)+nginx(static/media),
  volumes isolés, SECRET_KEY unique, sert à la racine `/`. Les 2 = 200 → wizard `/setup/` (fresh).
- **Phase 5** — `~/docker/mailserver/` docker-mailserver v15.1.0 + Rspamd (greylisting + scoring +
  DKIM/DMARC/SPF, spam→Junk ; ClamAV off). Ports `192.168.0.222:{25,465,587,993}`. TLS via acme.json
  Traefik. Boîtes `no-reply@`, `info@`, `admin@` (mdp dans `~/docker/mailserver/CREDENTIALS.txt`).
  Test interne : submission 587 AUTH+STARTTLS → livraison locale → **DKIM-signé** (d=bibliofelia.org
  s=mail), Rspamd score 0.00. **Réception externe + délivrabilité dépendent des actions Val ci-dessous.**

## Actions Val en attente (externes)

1. **DNS Infomaniak — DKIM** : ajouter TXT `mail._domainkey` = `v=DKIM1; k=rsa; p=MIIBIjANBgkq…AB`
   (valeur complète fournie ; fichier `rspamd/dkim/rsa-2048-mail-bibliofelia.org.public.dns.txt`).
2. **Port-forwarding box internet** → 192.168.0.222 : **25 entrant** (recevoir), **993** (IMAP externe) ;
   587/465 si client mail externe. Sans 25 entrant : pas de réception externe.
3. **rDNS/PTR** de 31.164.198.65 → `mail.bibliofelia.org` (FAI) — « après les tâches en cours ».

## Context

Val a acheté le domaine **bibliofelia.org** (Infomaniak). On passe d'une seule
box à un hébergement multi-sites :

- 2 **nouvelles instances** BibliOfelia hébergées sur **Avignon** (`192.168.0.222`)
  pour 2 bibliothèques : `sanjuan.bibliofelia.org` et `grand-saconnex.bibliofelia.org`.
- La **documentation** utilisateur sur `docs.bibliofelia.org` (Avignon).
- La **Ofelia Box** (Raspberry Pi, projet keebee `C:\WORK\keebee`, hostname `Canaima`)
  change d'adresse : `ofelia.zitoon.com` → **`canaima.bibliofelia.org`** ; tout doit
  continuer à fonctionner à la nouvelle adresse.
- Un **serveur SMTP** sur Avignon pour `no-reply@`, `info@`, `admin@ bibliofelia.org`
  (emails de confirmation notamment).
- **Redirection 301** de `bibliofelia.org` + `www.bibliofelia.org` vers
  `https://ofeliainternational.org/what-we-do/` (SEO-safe, sans abîmer le référencement
  d'ofeliainternational.org).

## Architecture réseau (existant, confirmé)

- Une seule IP publique **`31.164.198.65`** (partagée avec zitoon.com). Ports 80/443
  forwardés vers **Traefik v2.11** sur Avignon (réseau Docker externe `web`).
- Traefik : 2 providers — **docker** (labels, ex. NOEMA) + **file** (`~/docker/traefik/dynamic/*.yml`,
  `watch: true`). TLS Let's Encrypt via `httpChallenge` (resolver `letsencrypt`).
- Ajouter une route = **déposer un fichier YAML** dans `dynamic/` (aucun conteneur existant
  touché → zéro risque pour NOEMA / sites zitoon). Backends conteneurs = labels docker.
- `ofelia.zitoon.com.yml` route déjà `Host(ofelia.zitoon.com)` → `http://192.168.0.147:80` (Pi).

## Contraintes

- **Ne rien casser sur Avignon** (NOEMA, carradio, enpleinproust, cv, supabase,
  swisskap-dev, pihole, GQQFM…). Travail purement additif.
- IP non vraiment statique mais change rarement → A record en dur pour l'instant
  (DDNS plus tard). Voir mémoire `project_bibliofelia_org_infra`.

## Découpage en phases

- **Phase 1 — canaima.bibliofelia.org** (migration Pi) : fichier Traefik `canaima` → Pi:80 ;
  Pi = ajouter `https://canaima.bibliofelia.org` à `BIBLIOFELIA_CSRF_TRUSTED_ORIGINS` +
  restart. (nginx Pi a déjà `canaima` dans `server_name` + catch-all `_` ; `ALLOWED_HOSTS=*`.)
  `ofelia.zitoon.com` reste actif en parallèle (transition).
- **Phase 2 — redirect apex/www** : fichier Traefik avec middleware `redirectregex` (301
  permanent) → `https://ofeliainternational.org/what-we-do/`.
- **Phase 3 — docs.bibliofelia.org** : build MkDocs Material statique (guide utilisateur
  4 langues) servi par un conteneur nginx sur `web` + labels Traefik.
- **Phase 4 — instances sanjuan + grand-saconnex** : image BibliOfelia buildée sur Avignon,
  2 stacks compose isolés (SQLite WAL par instance, worker django-q2, volume propre), labels Traefik.
- **Phase 5 — SMTP** : serveur mail Avignon (no-reply/info/admin), génère la clé **DKIM**
  → ajout du TXT `default._domainkey` chez Infomaniak ; **rDNS/PTR** à voir avec le FAI (Val).

## Impact

- Avignon : nouveaux fichiers `~/docker/traefik/dynamic/*.yml` ; nouveaux dossiers
  `~/docker/bibliofelia-<instance>/`, `~/docker/bibliofelia-docs/`, serveur mail.
- Pi (keebee) : `.env` `BIBLIOFELIA_CSRF_TRUSTED_ORIGINS`.
- DNS Infomaniak : zone livrée (fichier `dns_bibliofelia.org.txt`) ; DKIM à ajouter en Phase 5.
