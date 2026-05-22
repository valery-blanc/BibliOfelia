# BUG-009 — CSRF_TRUSTED_ORIGINS manquant — login externe impossible

**Statut** : FIXED — commit `b80f960` (2026-05-23)
**Sévérité** : Bloquant (login impossible depuis domaine externe)
**Section SPEC impactée** : §11.2 Docker Compose, §9.1 Authentification

---

## Symptôme

Login BibliOfelia impossible depuis `https://ofelia.zitoon.com/bibliofelia/` :
Django retourne 403 CSRF Forbidden sur le POST du formulaire de connexion.
En accès direct par IP locale (`http://192.168.0.147/bibliofelia/`), le login fonctionne.

## Cause racine

Django 4.0+ exige que l'origin de la requête POST soit dans `ALLOWED_HOSTS` **ou** dans `CSRF_TRUSTED_ORIGINS`. Quand l'application est servie derrière un reverse-proxy externe (ZeroTier, domaine custom), l'header `Origin` contient le domaine externe. Si `CSRF_TRUSTED_ORIGINS` est vide ou absent, Django rejette la requête.

La variable `CSRF_TRUSTED_ORIGINS` n'était pas définie dans le `docker-compose.yml` de production.

## Fix

Ajout dans `docker-compose.yml` (service `bibliofelia`) :

```yaml
CSRF_TRUSTED_ORIGINS: ${BIBLIOFELIA_CSRF_TRUSTED_ORIGINS:-}
```

La valeur est configurée dans `/opt/edubox/.env` sur la Pi selon le domaine d'accès :

```
BIBLIOFELIA_CSRF_TRUSTED_ORIGINS=https://ofelia.zitoon.com
```

Si vide, Django n'accepte que les origines locales (comportement sûr par défaut).

## Test de validation

- Login depuis `https://ofelia.zitoon.com/bibliofelia/fr/accounts/login/` → HTTP 302 OK.
- Login depuis `http://192.168.0.147/bibliofelia/fr/accounts/login/` → HTTP 302 OK.
