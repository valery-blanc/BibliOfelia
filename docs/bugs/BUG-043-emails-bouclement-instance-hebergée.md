# BUG-043 — Le bouclement parle de la Box sur une instance hébergée

**Status:** FIXED
**Date:** 2026-09-03

## Symptôme

Signalé par Val (2026-09-03) sur Grand-Saconnex. L'étape 3 du bouclement
(`/fr/closing/`) parle de la Box, affiche **Hors ligne**, et le bouton dit
« Mettre en file d'attente ». Après clic : *« 3 emails attendent encore dans
la file »*. « Voir la file » → bouton Envoyer → redirection vers la caisse
avec *« 3 email(s) laissé(s) en file : la Box n'est pas en ligne. »*

Grand-Saconnex n'est pas la Box. Val : « on est forcément en ligne, le bouton
devrait envoyer immédiatement. Pas de notion de Box. »

## Cause racine

`is_online()` = « le relais SMTP répond ». Sur Grand-Saconnex,
`email_config` est **vide** (`enabled=False`, pas d'hôte) → `is_online()`
est faux. Toute l'UI en déduisait « la Box est hors ligne », y compris
`flush_outbox()` qui **refusait d'envoyer**.

Deux confusions collées :

1. **Où on est** (`Setting["is_box"]`) et **si le SMTP répond** n'étaient
   pas distingués.
2. La file d'attente hors-ligne n'a de sens **que sur la Box** (Canaima),
   qui peut perdre Internet. Une instance hébergée est en ligne par
   construction.

Le bouton de la file POST vers `outbox_flush`, qui redirige **toujours**
vers la caisse — d'où la page d'arrivée.

## Comportement voulu (Val)

| | Instance hébergée | Box (Canaima) |
|---|---|---|
| En ligne | Envoyer tout de suite. Aucune mention de « Box ». | Envoyer tout de suite. |
| Pas d'Internet / SMTP injoignable | N/A (elle est en ligne). Si le SMTP n'est **pas configuré**, le dire clairement (Avancé → Paramètres → Email). | File d'attente. Liste affichée pour prévenir **par téléphone**. Envoi dès que la Box est de nouveau en ligne. |

## Correctif

- `can_send_email()` : instance hébergée + SMTP configuré → on tente l'envoi,
  même si `is_online()` était faux pour d'autres raisons. Box → `is_online()`.
- Copy UI : « Box » / « Hors ligne » / « Mettre en file » **seulement** si
  `is_box`. Sinon « Envoyer maintenant », et si le SMTP manque : le dire.
- `outbox_flush` redirige vers la file (ou vers l'écran d'origine via `next`).
- Hors ligne sur la Box : mention **téléphone** pour prévenir les usagers.
