# FEAT-065 — Langues parlées de l'usager

**Status:** DONE
**Date:** 2026-08-19

## Contexte

Le public d'une bibliothèque Ofelia est multilingue. Savoir quelles langues
parle un usager permet de l'orienter vers le bon fonds et de l'accueillir dans
sa langue. À ne pas confondre avec `preferred_language`, qui ne dit qu'une
chose : dans quelle langue lui écrire (relances, courriels).

## Comportement

Nouveau champ **« Langues parlées »** dans la fiche usager. Plusieurs langues
par personne.

Saisie par cases à cocher dans un encadré, sur la liste suivante (ordre
d'affichage exact, tel que demandé) :

Français, Anglais, Portugais, Espagnol, Italien, Allemand, Arabe, Albanais,
Turc, Russe, Serbo-croate, Tamoul, Chinois, Polonais, Persan, Farsi, Grec,
Somali, Roumain, Ukrainien, Japonais, Malgache.

Sous l'encadré, un champ libre **« Autres langues »** : texte non vérifié,
plusieurs langues séparées par des virgules.

La fiche usager affiche les langues cochées (dans la langue de l'interface)
suivies des langues libres. Les libellés des 22 langues sont traduits en
EN/ES/MG ; le champ libre est restitué tel quel.

## Spec technique

- `Member.spoken_languages` — `JSONField(default=list, blank=True)`, liste de
  codes stables (`fr`, `en`, `pt`, `es`, `it`, `de`, `ar`, `sq`, `tr`, `ru`,
  `sh`, `ta`, `zh`, `pl`, `fa-persan`, `fa`, `el`, `so`, `ro`, `uk`, `ja`,
  `mg`). Les codes sont figés en base, seuls les libellés sont traduits.
  Persan et Farsi sont deux entrées distinctes parce que la liste demandée les
  distingue ; ils portent donc deux codes distincts.
- `Member.spoken_languages_other` — `CharField(max_length=200, blank=True)`.
- `apps/members/languages.py` — `SPOKEN_LANGUAGES` (liste ordonnée de
  `(code, libellé traduisible)`), `labels_for(codes)` pour l'affichage,
  réutilisé par FEAT-066 (langues des enfants).
- Widget `LanguageChecklistWidget` (`CheckboxSelectMultiple` stylé en encadré),
  partagé entre l'usager et ses enfants.
- Codes inconnus déjà en base (import, saisie API) : conservés en base,
  affichés bruts. On ne perd jamais une donnée qu'on ne sait pas nommer.

## Impact sur l'existant

- `apps/members/models.py` (+ migration), `forms.py`, nouveau `languages.py`.
- Templates `members/member_form.html`, `members/member_detail.html`.

## Implémentation

- `Member.spoken_languages` (JSON) + `Member.spoken_languages_other` —
  migration `members/0004`.
- `apps/members/languages.py` : `SPOKEN_LANGUAGES` (22 entrées, codes figés),
  `labels_for` (ordre de la liste, code inconnu restitué tel quel), `display`.
- `LanguageChecklistWidget` + `SpokenLanguagesField` (`apps/members/forms.py`),
  partagés avec les enfants (FEAT-066) ; CSS `div.lang-grid` dans
  `static/css/ofelia.css` (grille responsive dans un encadré).
- `Member.spoken_languages_display` alimente la fiche usager.
- Tests : 9 cas dans `apps/members/tests/test_languages_and_children.py`.

### Réserve signalée à Val

« Persan » et « Farsi » sont deux noms de la même langue. La liste demandée les
distingue, on a donc gardé deux entrées (`fa` et `fa-farsi`). Cocher l'une ou
l'autre revient au même en pratique ; à fusionner si Val le souhaite.
