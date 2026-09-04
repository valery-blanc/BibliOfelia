# FEAT-088 — Moteur de recherche de devise

**Status:** DONE
**Date:** 2026-09-01

## Contexte

Retour de test de Val (2026-09-01) sur le réglage de caisse livré la veille :

> « Devise : plutôt qu'une liste déroulante, fais un moteur de recherche qui
> recherche parmi toutes les devises. Le moteur attend la 2ᵉ lettre. On pourra
> donc taper soit une partie ou tout le trigramme, soit une partie ou tout le
> nom du pays. N'oublie pas de gérer les langues. »

La première version n'offrait que **six devises codées en dur** (CHF, VES, EUR,
USD, ARS, MGA) — celles des instances connues. Une nouvelle bibliothèque dans
un septième pays aurait exigé une modification du code.

## Comportement

Le réglage Avancé → Paramètres → « Caisse — devise et échéances » remplace la
liste déroulante par un **champ de recherche**.

- La recherche part à la **2ᵉ lettre** (demande explicite de Val) : sur un
  trigramme, une seule lettre remonterait la moitié de la liste.
- Elle porte sur le **code** (`CHF`), le **nom de la devise** (« franc
  suisse », « bolívar ») et le **nom du pays** (« Suisse », « Venezuela »),
  en partie comme en entier.
- **Insensible aux accents et à la casse** : « perou » trouve le sol péruvien.
- Les résultats sont classés : correspondance exacte du code d'abord, puis
  début de chaîne, puis contenu. `ARS` ne se noie pas sous les devises dont un
  pays contient « ars ».
- À moins de deux caractères, le champ propose les **devises des instances
  existantes** plutôt que rien — il n'est jamais vide au premier clic.
- Chaque résultat affiche **code, nom et pays** : « CHF — franc suisse (Liechtenstein, Suisse) ».

### Langues

Les libellés sont rendus dans la langue de l'écran, dans les **quatre**
langues. Vérifié : `suisse` (fr), `switzerland` (en), `suiza` (es) et `soisa`
(mg) renvoient tous `CHF`.

### Sans JavaScript

Le champ est un `<input type="text">` ordinaire **qui part au serveur tel
quel** : le script n'ajoute que la liste de suggestions. Sans lui, on tape
`CHF` et le réglage fonctionne toujours.

C'est pourquoi il n'y a **pas** de champ caché doublant le champ visible :
l'attelage aurait paru plus riche, mais sans JavaScript le champ caché ne
serait jamais rempli et le réglage deviendrait impossible à changer. Choisir un
résultat écrit le **code** dans le champ — ce qu'on voit est exactement ce qui
sera enregistré.

Le serveur accepte aussi une saisie libre **non ambiguë** (« Suisse »,
« bolívar ») : une recherche tapée puis validée au clavier, sans passer par la
liste, ne doit pas être rejetée quand elle ne désigne qu'une devise. Une saisie
ambiguë (« franc ») est refusée avec un message qui le dit.

## Spécification technique

### Source des libellés — Babel plutôt qu'une table maison

`Babel==2.16.0` ajouté à `requirements.txt`. Les noms de devises et de pays
viennent du **CLDR embarqué dans la bibliothèque** : aucune requête réseau, la
contrainte hors-ligne est respectée.

L'alternative — une table maison passée par `gettext` — aurait ajouté
**153 devises × leurs pays × 4 langues** à nos `.po`, à traduire à la main et à
maintenir à chaque changement politique. Ici le gate i18n n'est pas impacté.

Trou connu et assumé : le CLDR malgache ne nomme pas toutes les devises (`VES`
s'y rend « VES »). On garde alors le code plutôt qu'une chaîne vide, et le nom
du pays reste traduit (« Venezoelà »).

### `apps/finance/currencies.py`

- `catalogue(language)` — devises **en circulation** (`tender=True`) avec leurs
  pays, libellées et triées. Mis en cache par langue (`lru_cache`) : la
  construction parcourt tous les territoires du CLDR, trop lent pour être
  refait à chaque frappe.
- **Filtre sur les devises vivantes** : les 306 codes ISO 4217 de Babel
  comprennent les monnaies mortes (franc français, mark), qu'il serait absurde
  de proposer. Il en reste 153.
- `search(query, language)` — exact, puis préfixe, puis contenu.
- `is_valid(code)` / `describe(code)` / `precision(code)`.

### Reste

- `GET /finance/currencies/?q=` → JSON. **SUPERADMIN uniquement**, comme
  l'écran qui l'héberge.
- `CurrencySearchWidget` + `CurrencyField` dans `apps/core/forms.py`.
- `static/js/currency-search.js` — sans dépendance (contrainte hors-ligne),
  anti-rebond 180 ms, navigation clavier (flèches, Entrée, Échap), et
  **réponses hors délai ignorées** : le serveur répond dans le désordre quand
  on tape vite.
- `templates/core/admin/_currency_search.html` + styles `.currency-*`.

### Piège rencontré — `FORM_RENDERER`

Le renderer de formulaires de Django utilise un **moteur de templates isolé**
qui ne voit pas `templates/` : le widget levait `TemplateDoesNotExist` et la
page de réglage rendait un 500. Corrigé par
`FORM_RENDERER = "django.forms.renderers.TemplatesSetting"`, qui exige
`django.forms` dans `INSTALLED_APPS` pour que les templates de widgets fournis
par Django restent trouvables.

## Impact sur l'existant

- `apps/finance/money.py` : `CURRENCIES` et `currency_choices()` supprimés ; la
  précision par défaut vient de `currencies.precision()`.
- `FORM_RENDERER` est un réglage **global** : tous les formulaires de l'app
  passent désormais par les templates de `django.forms`. Vérifié par la suite
  complète (872 tests, dont le rendu de tous les écrans à formulaire).
- Image Docker : +9 Mo environ (données CLDR).
