# BUG-013 — Sélecteur de langue cassé en prod (FORCE_SCRIPT_NAME)

**Status :** FIXED
**Date :** 2026-05-24
**Sprint :** 9 (hotfix)
**Spec section :** SPEC §6.9 (i18n)

---

## Symptôme

En production (derrière nginx avec `FORCE_SCRIPT_NAME=/bibliofelia`), le
sélecteur de langue dans la topbar ne changeait pas la langue : la page se
rechargeait dans la même langue. Tapez `/es/` directement dans l'URL
fonctionnait (passait par le middleware locale).

## Cause racine

Le formulaire dans `templates/base.html` envoyait :

```html
<input type="hidden" name="next" value="{{ request.path }}">
```

`request.path` retourne le path **avec** le préfixe `SCRIPT_NAME`
(`/bibliofelia/fr/loans/lend/`).

Côté Django, la vue `set_language` appelle ensuite
`translate_url(next, lang_code)`. Cette fonction fait `resolve(next.path)`,
ne reconnaît pas le préfixe `/bibliofelia/` (pas dans les URL patterns),
attrape `Resolver404`, et **retourne l'URL inchangée**. Conséquence :
redirect vers `/bibliofelia/fr/...` → toujours FR.

## Diagnostic en shell Django (Pi) :

```
translate_url('/fr/loans/lend/', 'en') = '/bibliofelia/en/loans/lend/'  # OK
translate_url('/bibliofelia/fr/loans/lend/', 'en') = '/bibliofelia/fr/loans/lend/'  # KO
```

## Fix

Utiliser `{{ request.path_info }}` au lieu de `{{ request.path }}` —
`path_info` est le chemin **sans** `SCRIPT_NAME`, donc reconnu par
`resolve()` :

```html
<input type="hidden" name="next" value="{{ request.path_info }}">
```

Modifié dans :
- `templates/base.html`
- `templates/accounts/login.html`

## Validation

Test curl à travers nginx (sur la Pi) :
```
POST /bibliofelia/i18n/setlang/ language=en next=/fr/accounts/login/
→ 302 Location: /bibliofelia/en/accounts/login/   # OK
```

## Bug satellite : commentaire Django multi-ligne

Le commentaire `{# ... #}` ajouté à côté du fix s'étalait sur 2 lignes →
Django ne supporte **pas** le multi-ligne pour `{# #}` (doc :
[ref/templates/builtins#comment](https://docs.djangoproject.com/en/5.1/ref/templates/builtins/#comment)). Conséquence : la 2e ligne du commentaire
s'affichait comme texte brut dans la topbar.

Fix : commentaire ramené sur une seule ligne, ou bien utiliser
`{% comment %}...{% endcomment %}` pour du multi-ligne.
