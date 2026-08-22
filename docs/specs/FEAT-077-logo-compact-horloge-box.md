# FEAT-077 — Logo compact + horloge de la Box sur l'accueil

- **Statut** : DONE
- **Sprint** : 29
- **Demandé par** : Val (2026-08-22)
- **Sections spec impactées** : §10.1 (navigation), §10.2 (accueil)

## Contexte

Deux demandes d'interface :

1. **Le logo de la barre du haut prenait trop de place.** `ofelia-logo.png` fait
   2560 × 688 px : à 28 px de haut, il occupait ~104 px de large, au détriment du
   nom de la bibliothèque sur les petits écrans.
2. **La Box perd son horloge quand on la coupe.** Le Raspberry Pi n'a pas de
   pile RTC : hors ligne, à chaque extinction, il repart sur une heure fausse.
   Rien dans l'interface ne le montrait — les dates de prêt, les retards et les
   sauvegardes en dépendent pourtant toutes.

## Comportement

### Logo compact

La barre du haut affiche `ofelia-logo-small.png` (726 × 688 px, l'emblème seul
sans le lettrage), soit **~30 px de large à 28 px de haut au lieu de ~104 px**.
`ofelia-logo.png` reste en place : il sert aux étiquettes et au filigrane des
cartes membres, où le format large est voulu.

### Date et heure de la Box

Sur l'accueil, à droite du « Bonjour, <nom> », alignée sur le bloc de
salutation :

```
Bonjour, admin.                                              14:03
Voici ce qui se passe à la bibliothèque…      vendredi 22 août 2026
```

L'heure est en gros, en bordeaux, suivie de l'**abréviation du fuseau** en
petit et en gris ; la date en dessous, dans le gris des sous-titres. Sur mobile,
le bloc passe à la ligne (`flex-wrap`).

L'abréviation vient de la base IANA quand elle existe (`CEST`, `IST`, `EAT`).
La base a retiré les sigles littéraux de la plupart des zones d'Amérique du Sud
— `America/Caracas` renvoie `-04` et non `VET`, `America/Argentina/San_Juan`
renvoie `-03` et non `ART`. Un décalage numérique n'apprend rien à un
bibliothécaire : on affiche alors **le nom de la ville**, qui est le repère
qu'il a lui-même choisi dans les Paramètres (`Caracas`, `San Juan`).

Le bloc heure est découpé en deux `span` : `.hero-clock-hm` (rafraîchi par le
script) et `.hero-clock-tz` (le sigle). Sans cette séparation, le premier
rafraîchissement effaçait le sigle — bug constaté par Val le 2026-08-22 et
verrouillé par `test_refresh_script_never_overwrites_the_timezone`.

**C'est l'heure de la Box, jamais celle du poste.** Le gabarit rend
l'horodatage serveur dans `data-clock`, et le script ne se sert de l'horloge du
navigateur que pour mesurer le **temps écoulé depuis le chargement** — il
rafraîchit l'affichage toutes les 15 s à partir de la base serveur. Un poste
bien à l'heure ne peut donc pas masquer une Box déréglée, ce qui est tout
l'objet de l'affichage. La date, elle, reste celle du rendu (elle ne bascule pas
à minuit sur une page laissée ouverte — cas sans conséquence en bibliothèque).

### Fuseau horaire

`TIME_ZONE` était figé à `"UTC"`. Une bibliothèque à Madagascar aurait vu 3 h de
moins que sa pendule et aurait cru sa Box déréglée **en permanence** — l'inverse
de l'effet recherché. Deux niveaux, du plus général au plus spécifique :

**1. `TZ`, variable d'environnement de l'instance** — donne le défaut, avec
`UTC` si absente (comportement inchangé pour l'existant) :

```yaml
environment:
  TZ: ${TZ:-UTC}     # valeur dans le .env de l'instance
```

`TZ` est la variable POSIX standard : la poser règle du même coup l'horloge du
conteneur et celle de Django. C'est ce qui fait que **la Box prend le fuseau du
Raspberry Pi** (`timedatectl` → `/opt/edubox/.env`) sans qu'on ait rien à saisir
dans l'interface.

**2. Réglage `Avancé → Paramètres → Fuseau horaire`** — surcharge le précédent,
sans redéploiement. Liste déroulante de tous les fuseaux IANA
(`zoneinfo.available_timezones()`), première entrée « Fuseau du système
(<TZ>) » qui laisse la main à la machine. `TimezoneMiddleware` l'active à chaque
requête.

Chaque entrée porte **l'abréviation et le décalage**, sans quoi le nom IANA seul
ne se choisit pas — on ne devine pas qu'une bibliothèque de **Canaima** veut
`America/Caracas` (constat Val, 2026-08-22) :

```
Europe/Zurich — CEST (UTC+2)
Asia/Kolkata — IST (UTC+5:30)
America/Caracas (UTC-4)
```

La base IANA a **retiré les sigles littéraux** de la plupart des zones
d'Amérique du Sud : `America/Caracas` renvoie `-04` et non `VET`,
`America/Argentina/San_Juan` renvoie `-03` et non `ART`. Ce ne sont pas des
sigles manquants, ce sont les abréviations officielles actuelles. Quand le sigle
est numérique, on n'affiche que le décalage plutôt qu'un « -04 (UTC-4) » qui
répète deux fois la même chose. Rétablir `VET`/`ART` supposerait une table
maintenue à la main pour 486 fuseaux : non retenu.

**Coût** : `available_timezones()` scanne l'arborescence tzdata. Mesuré dans le
conteneur (Fez comme Pi) : **~220 ms au premier rendu de l'écran, ~40 ms
ensuite** — inutile de mettre en cache. (Sur Windows le même appel prend 4 s,
mais le dev local n'est pas utilisé.)

Valeurs en service au 2026-08-22 :

| Instance | `TZ` | Réglage Paramètres |
|---|---|---|
| Box (Canaima) | `Europe/Zurich` (fuseau du Pi) | vide |
| sanjuan | `America/Argentina/San_Juan` | vide |
| grand-saconnex | `Europe/Zurich` | vide |

**Robustesse** : un fuseau invalide en base est ignoré avec un `logger.warning`,
et la table `Setting` absente (avant la première migration) est traitée comme
« pas de réglage ». Une valeur aberrante ne doit pas empêcher la bibliothèque de
prêter des livres.

## Spec technique

- `static/img/ofelia-logo-small.png` (nouveau) ; `templates/base.html` pointe
  dessus.
- `templates/core/dashboard.html` : le hero devient deux blocs
  (`.hero-text` + `.hero-clock`), plus le script de rafraîchissement.
- `static/css/ofelia.css` : `.hero` en `flex` avec `justify-content:
  space-between` et `flex-wrap`, `.hero-clock` / `-time` / `-date`
  (`tabular-nums` pour que les chiffres ne dansent pas d'une minute à l'autre).
- `config/settings/base.py` : `TIME_ZONE = env("TZ")`, défaut `UTC` ;
  `TimezoneMiddleware` ajouté en fin de `MIDDLEWARE`.
- `apps/core/middleware.py` : `TimezoneMiddleware` — active le réglage,
  `timezone.deactivate()` s'il est vide, ignore un fuseau inconnu.
- `apps/core/timeutils.py` (nouveau) : `abbreviation()`, `utc_offset()`,
  `city()`, `zone_label()` — partagés par l'accueil et les Paramètres, pour que
  le sigle soit calculé une seule fois et de la même façon aux deux endroits.
- `apps/core/views.py` : `dashboard` passe `clock_abbr` au gabarit. On n'utilise
  **pas** `{% now "T" %}`, qui rendrait « -04 ».
- `apps/core/forms.py` : `TimezoneForm` (clé `Setting.timezone`), validation par
  `zoneinfo.ZoneInfo`, libellés délégués à `timeutils.zone_label()`.
- `apps/core/admin_views.py` : section `timezone` dans le registre `FORMS`.
- `.env.example` : bloc `TZ` documenté.
- Hors dépôt : `TZ` ajoutée dans les `.env` et `docker-compose.yml` des instances
  (Fez) et dans `/opt/edubox/.env` + `/opt/edubox/docker-compose.yml` (Box).
  ⚠️ Ce dernier appartient au projet **keebee** : les deux lignes
  `TZ: ${TZ:-UTC}` doivent être reportées dans `C:\WORK\keebee\docker-compose.yml`,
  sinon le prochain déploiement keebee les efface.

## Tests

`apps/core/tests/test_dashboard_clock.py` :

- l'horodatage publié est celui du serveur (à 30 s près) ;
- le script ne contient **pas** de `new Date()` sans argument — c'est ce qui
  réintroduirait l'horloge du poste et viderait la fonctionnalité de son sens ;
- l'accueil affiche bien une heure, une date et l'abréviation du fuseau ;
- une zone sans sigle littéral affiche sa ville (`Caracas`, `San Juan`) et
  jamais `-04` ;
- le script de rafraîchissement ne vise que `.hero-clock-hm`, jamais le bloc
  entier — sans quoi le sigle disparaît au bout de 15 s ;
- `TIME_ZONE` se lit dans l'environnement, défaut `UTC` ;
- le réglage des Paramètres surcharge le fuseau système (San Juan vs Zurich) ;
- un réglage vide retombe sur le fuseau système ;
- un fuseau inconnu en base ne casse pas l'accueil (200, pas 500) ;
- `TimezoneForm` refuse un fuseau inconnu à la saisie et enregistre depuis
  l'écran des Paramètres ;
- les libellés portent sigle et décalage, sans répéter un sigle numérique, et la
  liste reste exhaustive (`>= available_timezones()`).

## Impact sur l'existant

- Aucune migration. Aucun changement de comportement pour les instances qui ne
  posent pas `TZ` (elles restent en UTC).
- `ofelia-logo.png` n'est pas supprimé (impressions).
- Si un fuseau est posé (`TZ` ou réglage), **toutes** les dates de l'application
  le suivent (prêts, retards, sauvegardes) — c'est l'effet voulu, mais il vaut
  mieux le poser avant la mise en service d'une bibliothèque qu'après.
- Une requête de plus sur `Setting` par requête HTTP (lecture par clé primaire
  sur SQLite) : négligeable devant le reste du rendu.
