# FEAT-083 — Coordonnées complètes de l'usager

**Status:** DONE
**Date:** 2026-08-31

## Contexte

Demande Val (`temp.txt`, 2026-08-31), en tête du chantier « gestion financière ».
La fiche usager ne porte aujourd'hui qu'un téléphone et une **adresse en texte
libre** (`Member.address`, `TextField`). Ni email, ni adresse structurée.

Ce n'est pas un confort : FEAT-084 doit **envoyer les factures par email** et
**imprimer une facture A4** qui porte l'adresse du destinataire. Sans email, la
moitié du bouclement (FEAT-086) n'a rien à envoyer ; sans adresse découpée, une
facture ne peut pas être mise en page.

## Comportement

La fiche usager gagne un bloc « Coordonnées » :

| Champ | Obligatoire | Remarque |
|---|---|---|
| Email | non | validé (`EmailField`) ; c'est lui qui reçoit les factures |
| Téléphone | non | champ existant `contact_phone`, déplacé dans le bloc |
| Rue et n° | non | `address_street` |
| Complément d'adresse | non | `address_extra` |
| Code postal | non | `address_postal_code` |
| Localité | non | `address_city` |
| État / province | non | `address_state` — explicitement optionnel (demande Val) |
| Pays | non | `address_country`, pré-rempli par le pays de la bibliothèque |

**Écart assumé au cahier des charges** : `temp.txt` demande « code postal, état
(optionnel), pays » sans citer la **localité**. Un code postal sans ville ne
permet pas d'adresser une enveloppe ; le champ est ajouté.

**Commentaire libre (500 caractères)** : la fiche possède déjà un champ libre
`notes`, sans limite. Plutôt que d'installer deux zones de texte libre
quasi identiques sur le même écran, `notes` est **réutilisé** : relibellé
« Commentaire », plafonné à 500 caractères et marqué facultatif. Aucune donnée
existante n'est perdue (les notes plus longues restent lisibles ; seule une
**nouvelle** saisie est plafonnée).

L'adresse s'affiche sur la fiche en un bloc multi-lignes ; l'email est un lien
`mailto:`. Un usager sans email est signalé sur sa fiche **dès qu'il a une
facture ouverte** (FEAT-084) : c'est le seul moment où l'absence coûte quelque
chose.

## Spécification technique

- `apps/members/models.py` : sept nouveaux champs sur `Member`, tous
  `blank=True`. Propriétés `address_lines` (liste de lignes non vides, pour le
  gabarit et le PDF de facture) et `postal_address` (même chose en une chaîne).
- Migration `members/00XX_member_contact.py` : ajout des champs **puis**
  recopie de l'ancien `address` — première ligne dans `address_street`, le
  reste dans `address_extra` (tronqués à la longueur du champ) — **puis**
  suppression de `address`. `RunPython` avec son inverse, pour que la migration
  soit réversible sur une instance de production.
- `apps/members/forms.py` : champs ajoutés à `MemberForm`,
  `notes` en `Textarea(rows=3)` avec `max_length=500` et compteur.
- `templates/members/member_form.html` et `member_detail.html` : bloc
  « Coordonnées ».

## Impact sur l'existant

- `Member.address` **disparaît**. Seuls le formulaire et le gabarit de la fiche
  le lisaient (vérifié par `grep`) — aucun rapport, export Excel ni API ne le
  référence.
- L'export Excel du catalogue ne touche pas les usagers : pas d'impact.
