#!/usr/bin/env python3
"""Traductions Sprint 31 — FR → EN/ES/MG.

Couvre FEAT-083 (coordonnées complètes de l'usager), FEAT-084 (caisse,
cotisations, amendes et factures), FEAT-085 (activités et animations),
FEAT-086 (bouclement de la journée) et BUG-041 (renouvellement de carte).

Vocabulaire fixé pour ce sprint, aligné sur l'existant (`Usager` → *Member* /
*Usuario* / *Mpampiasa`) :

| FR | EN | ES | MG |
|---|---|---|---|
| facture | invoice | factura | faktiora |
| caisse | till | caja | kitapom-bola |
| cotisation | membership fee | cuota | saram-pikambanana |
| amende | fine | multa | lamandy |
| animation | event | actividad | hetsika |
| activité | activity | actividad interna | asa |
| bouclement | day closing | cierre del día | famaranana ny andro |
| échéance | due date | vencimiento | daty farany |
| solde | balance | saldo | ambim-bola |
| encaisser | record a payment | registrar el pago | mandray vola |

`animation` et `activité` tombent tous deux sur *actividad* en espagnol : les
libellés espagnols lèvent l'ambiguïté par le contexte (« Actividades del
personal » vs « Actividades públicas ») partout où les deux se côtoient.

Le mécanisme (`apply_lang`, blocs `msgid_plural`, nettoyage du drapeau `fuzzy`)
est repris de `scripts/translations_sprint30.py`.

À rejouer APRÈS `makemessages` (qui réinsère les msgid) :
    python scripts/translations_sprint31.py
"""
from __future__ import annotations

import re
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"

# ── Chaînes longues, factorisées pour garder les dictionnaires lisibles ────

_REMINDER_BODY = (
    "Bonjour %(name)s,\n\nLa facture %(num)s d'un montant de %(amount)s, échue "
    "le %(due)s, n'a pas encore été réglée.\nMerci de passer à la bibliothèque "
    "pour la régler.\n\n%(library)s"
)
_INVOICE_BODY = (
    "Bonjour %(name)s,\n\nVous trouverez ci-joint la facture %(num)s d'un "
    "montant de %(amount)s, à régler avant le %(due)s.\n\n%(library)s"
)
_SHUTDOWN_NOTE = (
    "BibliOfelia tourne dans un conteneur et ne peut pas éteindre la Box "
    "elle-même : elle dépose une demande que le service système de la Box "
    "surveille. Si ce service n'est pas installé, la demande est enregistrée "
    "mais la Box ne s'éteindra pas."
)
_SHUTDOWN_DONE = (
    "Demande d'extinction enregistrée (%(p)s). La Box s'éteindra si le service "
    "système d'extinction est installé."
)
_OFFLINE_QUEUE = (
    "La Box n'est pas en ligne : les emails sont mis en file et partiront dès "
    "qu'elle le sera. Un administrateur peut aussi les envoyer depuis l'écran "
    "de la caisse."
)
_ATTENDANCE_HINT = (
    "Les non-membres sont simplement comptés. Les membres présents s'ajoutent "
    "après enregistrement, en scannant leur carte ou en tapant les 4 derniers "
    "chiffres de leur numéro."
)
_STATS_SENTENCE = (
    "La bibliothèque a organisé %(s)s animation(s), auxquelles ont participé "
    "%(m)s membre(s) et, parmi les non-membres, %(a)s adulte(s) et %(c)s "
    "enfant(s)."
)
_DEACTIVATED_TYPE = (
    "Une nature désactivée disparaît du formulaire, mais les saisies passées "
    "restent comptées dans les statistiques."
)
_FREE_LABEL_HINT = (
    "Un animateur peut aussi créer un intitulé depuis son formulaire de saisie "
    "— une animation s'invente le jour même."
)
_MEMBERSHIP_HINT = (
    "La cotisation est facturée automatiquement à l'inscription et à chaque "
    "renouvellement de carte. Elle se modifie dans l'administration des "
    "catégories d'usager."
)
_FEE_FREE_HINT = (
    "Le motif propose un montant, mais celui-ci reste modifiable. Aucun montant "
    "n'est calculé automatiquement."
)
_LINES_HINT = (
    "Laissez une ligne vide si vous n'en avez pas besoin. Le montant est libre : "
    "rien n'est calculé automatiquement."
)
_EMAILS_PENDING = (
    "%(n)s email(s) en attente : ils partiront dès que la Box sera en ligne."
)


TRANSLATIONS: dict[str, dict[str, str]] = {
    # ══════════════════════════════════════════════════════════════════════
    "en": {
        # ── FEAT-085 : durées, activités, animations ──
        "Heures": "Hours",
        "Minutes": "Minutes",
        "Indiquez le temps passé.": "Enter the time spent.",
        "Modifiable : une journée oubliée se rattrape plus tard.":
            "Editable: a forgotten day can be caught up later.",
        "On ne saisit pas le travail de demain.":
            "Tomorrow's work cannot be recorded.",
        "— Nouvelle animation —": "— New event —",
        "Laissez vide si vous avez choisi une animation dans la liste.":
            "Leave empty if you picked an event from the list.",
        "Choisissez une animation ou donnez un intitulé.":
            "Pick an event or give it a name.",
        "libellé": "label",
        "Libellé": "Label",
        "ordre": "order",
        "Ordre": "Order",
        "employé": "staff member",
        "temps passé (minutes)": "time spent (minutes)",
        "%(h)s h %(m)02d": "%(h)s h %(m)02d",
        "%(h)s h": "%(h)s h",
        "%(m)s min": "%(m)s min",
        "non-membres adultes": "non-member adults",
        "non-membres enfants": "non-member children",
        "Non-membres adultes": "Non-member adults",
        "Non-membres enfants": "Non-member children",
        "bouclement": "day closing",
        "bouclements": "day closings",
        "Bouclement": "Day closing",
        "actif": "active",
        "nature d'activité": "activity type",
        "natures d'activité": "activity types",
        "Natures d'activité": "Activity types",
        "activité": "activity",
        "activités": "activities",
        "note": "note",
        "Note": "Note",
        "intitulé": "name",
        "Intitulé": "Name",
        "type d'animation": "event type",
        "types d'animation": "event types",
        "Types d'animation": "Event types",
        "animation": "event",
        "animations": "events",
        "Animation": "Event",
        "Animations": "Events",
        "animateur": "presenter",
        "présence": "attendance",
        "présences": "attendances",
        "Nouvelle animation": "New event",
        "Activité enregistrée.": "Activity saved.",
        "Animation enregistrée. Ajoutez maintenant les personnes présentes.":
            "Event saved. Now add the people who attended.",
        "%(name)s ajouté(e) à l'animation.": "%(name)s added to the event.",
        "%(name)s était déjà noté(e) présent(e).":
            "%(name)s was already marked as attending.",
        "%(name)s retiré(e).": "%(name)s removed.",
        "Aucun usager ne correspond à « %(q)s ».":
            "No member matches “%(q)s”.",
        "Vous ne pouvez retirer que vos propres saisies.":
            "You may only remove your own entries.",
        "Vous ne pouvez retirer que vos propres animations.":
            "You may only remove your own events.",
        "Saisie retirée.": "Entry removed.",
        "Animation supprimée.": "Event deleted.",
        "Nature d'activité ajoutée.": "Activity type added.",
        "Type d'animation ajouté.": "Event type added.",
        "« %(label)s » activé.": "“%(label)s” enabled.",
        "« %(label)s » désactivé — les saisies passées restent comptées.":
            "“%(label)s” disabled — past entries are still counted.",
        "Mes activités": "My activities",
        "Ce que vous avez fait et le temps que vous y avez passé.":
            "What you did, and how long it took.",
        "Aucune nature d'activité n'est définie.":
            "No activity type has been defined.",
        "En créer": "Create one",
        "Demandez à un administrateur d'en créer.":
            "Ask an administrator to create one.",
        "Mes dernières saisies": "My latest entries",
        "Date": "Date",
        "rattrapage": "caught up later",
        "Temps": "Time",
        "Retirer cette saisie ?": "Remove this entry?",
        "Aucune saisie pour l'instant.": "No entry yet.",
        "Retour au bouclement": "Back to day closing",
        "Saisir une activité": "Record an activity",
        "Saisir une animation": "Record an event",
        "Ce que vous avez présenté, et qui était là.":
            "What you ran, and who was there.",
        "Enregistrer et ajouter les présents": "Save and add attendees",
        _ATTENDANCE_HINT: (
            "Non-members are simply counted. Attending members are added after "
            "saving, by scanning their card or typing the last 4 digits of "
            "their number."
        ),
        "Dernières animations": "Latest events",
        "Aucune animation enregistrée.": "No event recorded.",
        "Ajouter une personne présente": "Add an attendee",
        "N° de carte ou 4 derniers chiffres": "Card number or last 4 digits",
        "0017 ou 2910000000017": "0017 or 2910000000017",
        "Plusieurs usagers correspondent à « %(q)s ». Choisissez la bonne personne.":
            "Several members match “%(q)s”. Pick the right person.",
        "Membres présents": "Attending members",
        "Personne n'a encore été noté(e) présent(e).":
            "Nobody has been marked as attending yet.",
        "Toutes les animations": "All events",
        "Supprimer cette animation et toutes ses presences ?":
            "Delete this event and all its attendances?",
        "%(m)s membre(s), %(n)s non-membre(s)":
            "%(m)s member(s), %(n)s non-member(s)",
        "Activités et animations": "Activities and events",
        "Les listes dans lesquelles les employés choisissent.":
            "The lists staff pick from.",
        "Les listes dans lesquelles les employés choisissent au bouclement.":
            "The lists staff pick from at day closing.",
        _DEACTIVATED_TYPE: (
            "A disabled type disappears from the form, but past entries are "
            "still counted in the statistics."
        ),
        "Aucun type d'animation.": "No event type.",
        "Aucune nature d'activité.": "No activity type.",
        "Ajouter une nature d'activité": "Add an activity type",
        "Ajouter un type d'animation": "Add an event type",
        "Activer": "Enable",
        "Créé par": "Created by",
        _FREE_LABEL_HINT: (
            "A presenter can also create a name from their own form — an event "
            "is invented on the day."
        ),
        # ── FEAT-085 : statistiques ──
        "Statistiques d'activité": "Activity statistics",
        "Animations, participants et temps passé.":
            "Events, attendance and time spent.",
        "Afficher": "Show",
        "Export CSV": "CSV export",
        _STATS_SENTENCE: (
            "The library ran %(s)s event(s), attended by %(m)s member(s) and, "
            "among non-members, %(a)s adult(s) and %(c)s child(ren)."
        ),
        "Participations de membres": "Member attendances",
        "Heures d'animation": "Event hours",
        "Mois par mois": "Month by month",
        "Mois": "Month",
        "Non-membres": "Non-members",
        "Minutes d'activité": "Activity minutes",
        "Saisies": "Entries",
        "Temps par nature d'activité": "Time per activity type",
        "Aucune activité saisie sur cette année.":
            "No activity recorded for this year.",
        # ── FEAT-086 : bouclement ──
        "Fin de service du %(d)s": "End of shift, %(d)s",
        "1. Vos activités et animations du jour":
            "1. Your activities and events for today",
        "Saisi": "Recorded",
        "À faire": "To do",
        "Vous n'avez rien saisi aujourd'hui.": "You have not recorded anything today.",
        "2. Mouvements de caisse du jour": "2. Today's till movements",
        "Entrées": "In",
        "Sorties": "Out",
        "Aucun mouvement aujourd'hui.": "No movement today.",
        "Solde du jour": "Today's balance",
        "Ouvrir la caisse": "Open the till",
        "3. Factures et relances à envoyer": "3. Invoices and reminders to send",
        "En ligne": "Online",
        "Hors ligne": "Offline",
        "Factures jamais envoyées": "Invoices never sent",
        "Relances dues": "Reminders due",
        "échue depuis %(d)s jour(s)": "overdue by %(d)s day(s)",
        "Voir la file": "View the queue",
        _OFFLINE_QUEUE: (
            "The Box is offline: emails are queued and will go out as soon as "
            "it is back online. An administrator can also send them from the "
            "till screen."
        ),
        "Envoyer maintenant": "Send now",
        "Mettre en file d'attente": "Add to the queue",
        "4. Sauvegardes": "4. Backups",
        "Faite": "Done",
        "Lancer la sauvegarde": "Run the backup",
        "5. Éteindre la Box": "5. Shut down the Box",
        "Demande d'extinction enregistrée.": "Shutdown request recorded.",
        _SHUTDOWN_NOTE: (
            "BibliOfelia runs in a container and cannot shut the Box down "
            "itself: it files a request that the Box's system service watches "
            "for. If that service is not installed, the request is recorded but "
            "the Box will not shut down."
        ),
        "Demander l extinction de la Box ? Toutes les applications seront arretees.":
            "Request a Box shutdown? Every application will be stopped.",
        "Demander l'extinction": "Request shutdown",
        "Seul un administrateur peut éteindre la Box.":
            "Only an administrator can shut the Box down.",
        "Cette instance n'est pas la Box : rien à éteindre.":
            "This instance is not the Box: nothing to shut down.",
        _SHUTDOWN_DONE: (
            "Shutdown request recorded (%(p)s). The Box will shut down if the "
            "system shutdown service is installed."
        ),
        "Demande impossible : %(e)s": "Request failed: %(e)s",
        "Activités, caisse, sauvegardes et fin de journée":
            "Activities, till, backups and end of day",
        # ── FEAT-084 : réglages ──
        "Caisse — devise et échéances": "Till — currency and due dates",
        "Email (SMTP)": "Email (SMTP)",
        "Pays": "Country",
        "Devise": "Currency",
        "Décimales affichées": "Decimals shown",
        "Vide = valeur usuelle de la devise choisie.":
            "Empty = the usual value for the chosen currency.",
        "Délai de paiement (jours)": "Payment terms (days)",
        "Échéance par défaut d'une facture, à compter de son émission.":
            "Default due date of an invoice, counted from its issue date.",
        "Envoi d'emails activé": "Email sending enabled",
        "Serveur SMTP": "SMTP server",
        "Port": "Port",
        "Chiffrement TLS": "TLS encryption",
        "Adresse d'expéditeur": "Sender address",
        "Indiquez un serveur SMTP, ou désactivez l'envoi d'emails.":
            "Enter an SMTP server, or disable email sending.",
        "Bolívar (VES)": "Bolívar (VES)",
        "Franc suisse (CHF)": "Swiss franc (CHF)",
        "Euro (EUR)": "Euro (EUR)",
        "Dollar américain (USD)": "US dollar (USD)",
        "Peso argentin (ARS)": "Argentine peso (ARS)",
        "Ariary (MGA)": "Ariary (MGA)",
        # ── FEAT-084 : modèles ──
        "nature": "kind",
        "Nature": "Kind",
        "montant proposé": "suggested amount",
        "tarif": "tariff",
        "tarifs": "tariffs",
        "Tarifs": "Tariffs",
        "n° de facture": "invoice no.",
        "date d'émission": "issue date",
        "total": "total",
        "réglé": "paid",
        "émise par": "issued by",
        "envoyée le": "sent on",
        "relancée le": "reminded on",
        "facture": "invoice",
        "factures": "invoices",
        "Facture": "Invoice",
        "Factures": "Invoices",
        "montant unitaire": "unit amount",
        "quantité": "quantity",
        "ligne de facture": "invoice line",
        "lignes de facture": "invoice lines",
        "montant": "amount",
        "Montant": "Amount",
        "mode de paiement": "payment method",
        "encaissé par": "received by",
        "Encaissé par": "Received by",
        "paiement": "payment",
        "paiements": "payments",
        "sens": "direction",
        "Sens": "Direction",
        "saisi par": "recorded by",
        "Saisi par": "Recorded by",
        "mouvement de caisse": "till movement",
        "mouvements de caisse": "till movements",
        "destinataire": "recipient",
        "Destinataire": "Recipient",
        "message": "message",
        "erreur": "error",
        "tentatives": "attempts",
        "envoyé le": "sent on",
        "Envoyé": "Sent",
        "objet": "subject",
        "Objet": "Subject",
        "email en file": "queued email",
        "emails en file": "queued emails",
        "Relance": "Reminder",
        "Amende": "Fine",
        "Nouvelle amende": "New fine",
        "Cotisation": "Membership fee",
        "cotisation annuelle": "annual membership fee",
        "Cotisation annuelle": "Annual membership fee",
        "À régler": "Due",
        "Réglée": "Paid",
        "Espèces": "Cash",
        "Virement": "Bank transfer",
        "Entrée": "In",
        "Sortie": "Out",
        # ── FEAT-084 : formulaires ──
        "Ajoutez au moins une ligne à la facture.":
            "Add at least one line to the invoice.",
        "Le montant doit être positif.": "The amount must be positive.",
        "Le montant dépasse le solde de la facture (%(b)s).":
            "The amount exceeds the invoice balance (%(b)s).",
        "Libellé obligatoire.": "Label required.",
        "Montant obligatoire.": "Amount required.",
        "Autre motif (à décrire)": "Other reason (describe it)",
        "Motif": "Reason",
        "Décrivez le motif.": "Describe the reason.",
        "0 = pas de cotisation pour cette catégorie.":
            "0 = no membership fee for this category.",
        # ── FEAT-084 : PDF ──
        "Facture %(num)s": "Invoice %(num)s",
        "Émise le %(d)s": "Issued on %(d)s",
        "Échéance : %(d)s": "Due: %(d)s",
        "DESTINATAIRE": "RECIPIENT",
        "N° de carte : %(n)s": "Card no.: %(n)s",
        "Désignation": "Description",
        "Qté": "Qty",
        "P.U.": "Unit",
        "Déjà réglé": "Already paid",
        "Reste à payer": "Balance due",
        "Réglée — merci.": "Paid — thank you.",
        "Facture annulée": "Invoice cancelled",
        "%(lib)s — document généré par BibliOfelia":
            "%(lib)s — document generated by BibliOfelia",
        # ── FEAT-084 : services et messages ──
        "Cotisation %(cat)s — %(year)s": "%(cat)s membership fee — %(year)s",
        "Facture %(num)s — %(member)s": "Invoice %(num)s — %(member)s",
        "Rappel — facture %(num)s": "Reminder — invoice %(num)s",
        _REMINDER_BODY: (
            "Hello %(name)s,\n\nInvoice %(num)s for %(amount)s, due on %(due)s, "
            "has not been paid yet.\nPlease come to the library to settle it."
            "\n\n%(library)s"
        ),
        _INVOICE_BODY: (
            "Hello %(name)s,\n\nPlease find attached invoice %(num)s for "
            "%(amount)s, to be paid before %(due)s.\n\n%(library)s"
        ),
        "%(n)s email(s) envoyé(s).": "%(n)s email(s) sent.",
        "%(n)s échec(s) d'envoi.": "%(n)s sending failure(s).",
        "%(n)s email(s) laissé(s) en file : la Box n'est pas en ligne.":
            "%(n)s email(s) left in the queue: the Box is offline.",
        _EMAILS_PENDING: (
            "%(n)s email(s) waiting: they will go out as soon as the Box is "
            "online."
        ),
        "Rien à envoyer aujourd'hui.": "Nothing to send today.",
        "Aucun email en attente.": "No email waiting.",
        "Mouvement de caisse enregistré.": "Till movement saved.",
        "Mouvement refusé : %(e)s": "Movement rejected: %(e)s",
        "Facture %(num)s créée (%(amount)s).": "Invoice %(num)s created (%(amount)s).",
        "Facture %(num)s réglée intégralement.": "Invoice %(num)s paid in full.",
        "Encaissement enregistré. Reste %(b)s.": "Payment saved. %(b)s left.",
        "Cette facture est annulée.": "This invoice is cancelled.",
        "Facture déjà encaissée : elle ne peut plus être annulée.":
            "Invoice already paid: it can no longer be cancelled.",
        "Facture %(num)s annulée.": "Invoice %(num)s cancelled.",
        "%(name)s n'a pas d'adresse email sur sa fiche.":
            "%(name)s has no email address on their record.",
        "Facture envoyée par email.": "Invoice sent by email.",
        "Facture mise en file : elle partira dès que la Box sera en ligne.":
            "Invoice queued: it will go out as soon as the Box is online.",
        "Tarif ajouté.": "Tariff added.",
        "Tarif modifié.": "Tariff updated.",
        "Tarif supprimé.": "Tariff deleted.",
        "Frais d'animation": "Event fee",
        "Autre montant à facturer": "Other amount to invoice",
        # ── FEAT-084 : écrans ──
        "Caisse": "Till",
        "Cotisations, amendes, factures et paiements":
            "Membership fees, fines, invoices and payments",
        "Entrées, sorties et paiements dus.": "Money in, money out and amounts due.",
        "Solde de caisse": "Till balance",
        "Entrées sur la période": "In over the period",
        "Sorties sur la période": "Out over the period",
        "Dû par les usagers": "Owed by members",
        "La Box est en ligne : ils peuvent partir maintenant.":
            "The Box is online: they can go out now.",
        "La Box n'est pas en ligne. Ils partiront dès qu'elle le sera.":
            "The Box is offline. They will go out as soon as it is online.",
        "La Box est en ligne.": "The Box is online.",
        "La Box n'est pas en ligne : les envois attendent.":
            "The Box is offline: sending is on hold.",
        "Mouvements de la période": "Movements over the period",
        "Toutes les factures": "All invoices",
        "Aucun mouvement sur cette période.": "No movement over this period.",
        "Saisir un mouvement": "Record a movement",
        "Factures en retard": "Overdue invoices",
        "Échue depuis %(d)s jour(s)": "Overdue by %(d)s day(s)",
        "En retard de %(d)s jour(s)": "%(d)s day(s) overdue",
        "Total dû par les usagers : %(t)s": "Total owed by members: %(t)s",
        "Tous": "All",
        "N°": "No.",
        "Solde": "Balance",
        "Aucune facture.": "No invoice.",
        "N° de facture, nom, n° de carte…": "Invoice no., name, card no.…",
        "Nouvelle facture": "New invoice",
        "Créer la facture": "Create the invoice",
        "Lignes": "Lines",
        _LINES_HINT: (
            "Leave a line empty if you do not need it. The amount is free: "
            "nothing is calculated automatically."
        ),
        "Tarifs de la bibliothèque": "Library tariffs",
        "Rappel des montants usuels — à recopier dans les lignes ci-dessus.":
            "The usual amounts, for reference — copy them into the lines above.",
        _FEE_FREE_HINT: (
            "The reason suggests an amount, but it stays editable. No amount is "
            "calculated automatically."
        ),
        "Facture PDF": "Invoice PDF",
        "Envoyer par email": "Send by email",
        "Cet usager n’a pas d’adresse email.": "This member has no email address.",
        "Annuler cette facture ? Elle restera visible, numérotée, mais ne sera plus due.":
            "Cancel this invoice? It stays visible and numbered, but is no "
            "longer owed.",
        "Annuler la facture": "Cancel the invoice",
        "Compte de l'usager": "Member's account",
        "Émise le": "Issued on",
        "Envoyée le": "Sent on",
        "Relancée le": "Reminded on",
        "Encaissements": "Payments",
        "Aucun encaissement pour l'instant.": "No payment yet.",
        "Encaisser": "Record a payment",
        "Enregistrer l'encaissement": "Save the payment",
        "Un règlement en espèces crée automatiquement une entrée de caisse.":
            "A cash payment automatically creates a till entry.",
        "Emails": "Emails",
        "File d'emails": "Email queue",
        "Factures et relances en attente d'envoi quand la Box est hors ligne.":
            "Invoices and reminders waiting to be sent while the Box is offline.",
        "Aucun email en file.": "No email in the queue.",
        "Compte": "Account",
        "Compte et factures": "Account and invoices",
        "Aucune facture pour cet usager.": "No invoice for this member.",
        "Modifier un tarif": "Edit a tariff",
        "Montants proposés pour les animations, les amendes et les autres frais.":
            "Suggested amounts for events, fines and other fees.",
        "Cotisations par catégorie d'usager": "Membership fees per member category",
        "Cotisation par catégorie d'usager, montants proposés pour les animations et les amendes.":
            "Membership fee per member category, suggested amounts for events "
            "and fines.",
        "Validité": "Validity",
        "%(n)s mois": "%(n)s months",
        "gratuit": "free",
        _MEMBERSHIP_HINT: (
            "The membership fee is invoiced automatically on registration and "
            "at every card renewal. It is edited in the member category "
            "administration."
        ),
        "Autres tarifs": "Other tariffs",
        "Supprimer ce tarif ?": "Delete this tariff?",
        "Aucun tarif enregistré.": "No tariff recorded.",
        "Ajouter un tarif": "Add a tariff",
        # ── FEAT-084 : encadré compte ──
        "À jour sur ses paiements": "Up to date with payments",
        "En retard de paiement : %(amount)s depuis le %(d)s":
            "Overdue payment: %(amount)s since %(d)s",
        "Total dû : %(total)s": "Total owed: %(total)s",
        "%(amount)s à régler": "%(amount)s due",
        "Prochaine échéance le %(d)s": "Next due date %(d)s",
        "%(d)s j de retard": "%(d)s d overdue",
        # ── FEAT-083 : coordonnées ──
        "Coordonnées": "Contact details",
        "email": "email",
        "Reçoit les factures et les relances.": "Receives invoices and reminders.",
        "rue et n°": "street and number",
        "complément d'adresse": "address line 2",
        "code postal": "postcode",
        "localité": "town",
        "état / province": "state / province",
        "pays": "country",
        "Facultatif.": "Optional.",
        "commentaire": "comment",
        "Commentaire": "Comment",
        "Commentaire libre, 500 caractères au maximum.":
            "Free comment, 500 characters at most.",
        # ── BUG-041 et FEAT-084 : renouvellement ──
        "Carte valable jusqu'au %(d)s — renouvellement inutile.":
            "Card valid until %(d)s — no renewal needed.",
        "Carte déjà valable jusqu'au %(date)s : rien à renouveler.":
            "Card already valid until %(date)s: nothing to renew.",
        "Facture de cotisation %(num)s émise.":
            "Membership fee invoice %(num)s issued.",
        "Facture de cotisation %(num)s émise (%(amount)s).":
            "Membership fee invoice %(num)s issued (%(amount)s).",
        # ── FEAT-088 + présences dès la création (2026-09-01) ──
        'Scannez une carte ou tapez les 4 derniers chiffres': 'Scan a card or type the last 4 digits',
        'Plusieurs cartes séparées par un espace ou une virgule. Vous pourrez aussi en ajouter après enregistrement.': 'Several cards separated by a space or a comma. You can also add more after saving.',
        'Codes non reconnus ou ambigus : %(codes)s. Ajoutez ces personnes ci-dessous.': 'Unrecognised or ambiguous codes: %(codes)s. Add these people below.',
        'Choisissez une devise.': 'Choose a currency.',
        '« %(q)s » correspond à plusieurs devises : précisez.': '“%(q)s” matches several currencies: be more specific.',
        '« %(q)s » ne correspond à aucune devise en circulation.': '“%(q)s” matches no currency in circulation.',
        'Tapez au moins deux lettres : trigramme (CHF, VES…) ou nom de pays.': 'Type at least two letters: code (CHF, VES…) or country name.',
        'CHF, Suisse, bolívar…': 'CHF, Switzerland, bolívar…',
        'Sélectionnée : <b>%(code)s</b> — %(name)s (%(countries)s)': 'Selected: <b>%(code)s</b> — %(name)s (%(countries)s)',
        'Aucune devise sélectionnée.': 'No currency selected.',
    },
    # ══════════════════════════════════════════════════════════════════════
    "es": {
        "Heures": "Horas",
        "Minutes": "Minutos",
        "Indiquez le temps passé.": "Indique el tiempo dedicado.",
        "Modifiable : une journée oubliée se rattrape plus tard.":
            "Modificable: una jornada olvidada se puede registrar más tarde.",
        "On ne saisit pas le travail de demain.":
            "No se registra el trabajo de mañana.",
        "— Nouvelle animation —": "— Nueva actividad pública —",
        "Laissez vide si vous avez choisi une animation dans la liste.":
            "Déjelo vacío si ha elegido una actividad de la lista.",
        "Choisissez une animation ou donnez un intitulé.":
            "Elija una actividad o indique un título.",
        "libellé": "etiqueta",
        "Libellé": "Etiqueta",
        "ordre": "orden",
        "Ordre": "Orden",
        "employé": "empleado",
        "temps passé (minutes)": "tiempo dedicado (minutos)",
        "%(h)s h %(m)02d": "%(h)s h %(m)02d",
        "%(h)s h": "%(h)s h",
        "%(m)s min": "%(m)s min",
        "non-membres adultes": "adultos no miembros",
        "non-membres enfants": "niños no miembros",
        "Non-membres adultes": "Adultos no miembros",
        "Non-membres enfants": "Niños no miembros",
        "bouclement": "cierre del día",
        "bouclements": "cierres del día",
        "Bouclement": "Cierre del día",
        "actif": "activo",
        "nature d'activité": "tipo de actividad interna",
        "natures d'activité": "tipos de actividad interna",
        "Natures d'activité": "Tipos de actividad interna",
        "activité": "actividad interna",
        "activités": "actividades internas",
        "note": "nota",
        "Note": "Nota",
        "intitulé": "título",
        "Intitulé": "Título",
        "type d'animation": "tipo de actividad pública",
        "types d'animation": "tipos de actividad pública",
        "Types d'animation": "Tipos de actividad pública",
        "animation": "actividad pública",
        "animations": "actividades públicas",
        "Animation": "Actividad pública",
        "Animations": "Actividades públicas",
        "animateur": "animador",
        "présence": "asistencia",
        "présences": "asistencias",
        "Nouvelle animation": "Nueva actividad pública",
        "Activité enregistrée.": "Actividad guardada.",
        "Animation enregistrée. Ajoutez maintenant les personnes présentes.":
            "Actividad guardada. Añada ahora las personas asistentes.",
        "%(name)s ajouté(e) à l'animation.": "%(name)s añadido/a a la actividad.",
        "%(name)s était déjà noté(e) présent(e).":
            "%(name)s ya constaba como asistente.",
        "%(name)s retiré(e).": "%(name)s retirado/a.",
        "Aucun usager ne correspond à « %(q)s ».":
            "Ningún usuario coincide con «%(q)s».",
        "Vous ne pouvez retirer que vos propres saisies.":
            "Solo puede retirar sus propios registros.",
        "Vous ne pouvez retirer que vos propres animations.":
            "Solo puede retirar sus propias actividades.",
        "Saisie retirée.": "Registro retirado.",
        "Animation supprimée.": "Actividad eliminada.",
        "Nature d'activité ajoutée.": "Tipo de actividad interna añadido.",
        "Type d'animation ajouté.": "Tipo de actividad pública añadido.",
        "« %(label)s » activé.": "«%(label)s» activado.",
        "« %(label)s » désactivé — les saisies passées restent comptées.":
            "«%(label)s» desactivado: los registros anteriores siguen contando.",
        "Mes activités": "Mis actividades",
        "Ce que vous avez fait et le temps que vous y avez passé.":
            "Lo que ha hecho y el tiempo que le ha dedicado.",
        "Aucune nature d'activité n'est définie.":
            "No hay ningún tipo de actividad definido.",
        "En créer": "Crear uno",
        "Demandez à un administrateur d'en créer.":
            "Pida a un administrador que cree uno.",
        "Mes dernières saisies": "Mis últimos registros",
        "Date": "Fecha",
        "rattrapage": "registro posterior",
        "Temps": "Tiempo",
        "Retirer cette saisie ?": "¿Retirar este registro?",
        "Aucune saisie pour l'instant.": "Ningún registro por ahora.",
        "Retour au bouclement": "Volver al cierre del día",
        "Saisir une activité": "Registrar una actividad",
        "Saisir une animation": "Registrar una actividad pública",
        "Ce que vous avez présenté, et qui était là.":
            "Lo que ha presentado y quién estuvo allí.",
        "Enregistrer et ajouter les présents": "Guardar y añadir asistentes",
        _ATTENDANCE_HINT: (
            "Los no miembros simplemente se cuentan. Los miembros asistentes se "
            "añaden después de guardar, escaneando su carné o tecleando los 4 "
            "últimos dígitos de su número."
        ),
        "Dernières animations": "Últimas actividades públicas",
        "Aucune animation enregistrée.": "Ninguna actividad registrada.",
        "Ajouter une personne présente": "Añadir un asistente",
        "N° de carte ou 4 derniers chiffres": "N.º de carné o 4 últimos dígitos",
        "0017 ou 2910000000017": "0017 o 2910000000017",
        "Plusieurs usagers correspondent à « %(q)s ». Choisissez la bonne personne.":
            "Varios usuarios coinciden con «%(q)s». Elija la persona correcta.",
        "Membres présents": "Miembros asistentes",
        "Personne n'a encore été noté(e) présent(e).":
            "Todavía no consta ningún asistente.",
        "Toutes les animations": "Todas las actividades públicas",
        "Supprimer cette animation et toutes ses presences ?":
            "¿Eliminar esta actividad y todas sus asistencias?",
        "%(m)s membre(s), %(n)s non-membre(s)":
            "%(m)s miembro(s), %(n)s no miembro(s)",
        "Activités et animations": "Actividades internas y públicas",
        "Les listes dans lesquelles les employés choisissent.":
            "Las listas entre las que elige el personal.",
        "Les listes dans lesquelles les employés choisissent au bouclement.":
            "Las listas entre las que elige el personal en el cierre del día.",
        _DEACTIVATED_TYPE: (
            "Un tipo desactivado desaparece del formulario, pero los registros "
            "anteriores siguen contando en las estadísticas."
        ),
        "Aucun type d'animation.": "Ningún tipo de actividad pública.",
        "Aucune nature d'activité.": "Ningún tipo de actividad interna.",
        "Ajouter une nature d'activité": "Añadir un tipo de actividad interna",
        "Ajouter un type d'animation": "Añadir un tipo de actividad pública",
        "Activer": "Activar",
        "Créé par": "Creado por",
        _FREE_LABEL_HINT: (
            "Un animador también puede crear un título desde su formulario de "
            "registro: una actividad se inventa el mismo día."
        ),
        "Statistiques d'activité": "Estadísticas de actividad",
        "Animations, participants et temps passé.":
            "Actividades públicas, asistencia y tiempo dedicado.",
        "Afficher": "Mostrar",
        "Export CSV": "Exportación CSV",
        _STATS_SENTENCE: (
            "La biblioteca organizó %(s)s actividad(es), a las que asistieron "
            "%(m)s miembro(s) y, entre los no miembros, %(a)s adulto(s) y %(c)s "
            "niño(s)."
        ),
        "Participations de membres": "Asistencias de miembros",
        "Heures d'animation": "Horas de actividad pública",
        "Mois par mois": "Mes a mes",
        "Mois": "Mes",
        "Non-membres": "No miembros",
        "Minutes d'activité": "Minutos de actividad",
        "Saisies": "Registros",
        "Temps par nature d'activité": "Tiempo por tipo de actividad",
        "Aucune activité saisie sur cette année.":
            "Ninguna actividad registrada en este año.",
        "Fin de service du %(d)s": "Fin de jornada del %(d)s",
        "1. Vos activités et animations du jour":
            "1. Sus actividades internas y públicas de hoy",
        "Saisi": "Registrado",
        "À faire": "Pendiente",
        "Vous n'avez rien saisi aujourd'hui.": "Hoy no ha registrado nada.",
        "2. Mouvements de caisse du jour": "2. Movimientos de caja de hoy",
        "Entrées": "Entradas",
        "Sorties": "Salidas",
        "Aucun mouvement aujourd'hui.": "Ningún movimiento hoy.",
        "Solde du jour": "Saldo del día",
        "Ouvrir la caisse": "Abrir la caja",
        "3. Factures et relances à envoyer": "3. Facturas y avisos por enviar",
        "En ligne": "En línea",
        "Hors ligne": "Sin conexión",
        "Factures jamais envoyées": "Facturas nunca enviadas",
        "Relances dues": "Avisos pendientes",
        "échue depuis %(d)s jour(s)": "vencida hace %(d)s día(s)",
        "Voir la file": "Ver la cola",
        _OFFLINE_QUEUE: (
            "La Box no está en línea: los correos se ponen en cola y saldrán en "
            "cuanto lo esté. Un administrador también puede enviarlos desde la "
            "pantalla de la caja."
        ),
        "Envoyer maintenant": "Enviar ahora",
        "Mettre en file d'attente": "Poner en cola",
        "4. Sauvegardes": "4. Copias de seguridad",
        "Faite": "Hecha",
        "Lancer la sauvegarde": "Lanzar la copia de seguridad",
        "5. Éteindre la Box": "5. Apagar la Box",
        "Demande d'extinction enregistrée.": "Solicitud de apagado registrada.",
        _SHUTDOWN_NOTE: (
            "BibliOfelia funciona en un contenedor y no puede apagar la Box por "
            "sí misma: deja una solicitud que el servicio de sistema de la Box "
            "vigila. Si ese servicio no está instalado, la solicitud queda "
            "registrada pero la Box no se apagará."
        ),
        "Demander l extinction de la Box ? Toutes les applications seront arretees.":
            "¿Solicitar el apagado de la Box? Se detendrán todas las aplicaciones.",
        "Demander l'extinction": "Solicitar el apagado",
        "Seul un administrateur peut éteindre la Box.":
            "Solo un administrador puede apagar la Box.",
        "Cette instance n'est pas la Box : rien à éteindre.":
            "Esta instancia no es la Box: no hay nada que apagar.",
        _SHUTDOWN_DONE: (
            "Solicitud de apagado registrada (%(p)s). La Box se apagará si el "
            "servicio de sistema de apagado está instalado."
        ),
        "Demande impossible : %(e)s": "Solicitud imposible: %(e)s",
        "Activités, caisse, sauvegardes et fin de journée":
            "Actividades, caja, copias de seguridad y fin de jornada",
        "Caisse — devise et échéances": "Caja — moneda y vencimientos",
        "Email (SMTP)": "Correo electrónico (SMTP)",
        "Pays": "País",
        "Devise": "Moneda",
        "Décimales affichées": "Decimales mostrados",
        "Vide = valeur usuelle de la devise choisie.":
            "Vacío = el valor habitual de la moneda elegida.",
        "Délai de paiement (jours)": "Plazo de pago (días)",
        "Échéance par défaut d'une facture, à compter de son émission.":
            "Vencimiento predeterminado de una factura, desde su emisión.",
        "Envoi d'emails activé": "Envío de correos activado",
        "Serveur SMTP": "Servidor SMTP",
        "Port": "Puerto",
        "Chiffrement TLS": "Cifrado TLS",
        "Adresse d'expéditeur": "Dirección del remitente",
        "Indiquez un serveur SMTP, ou désactivez l'envoi d'emails.":
            "Indique un servidor SMTP o desactive el envío de correos.",
        "Bolívar (VES)": "Bolívar (VES)",
        "Franc suisse (CHF)": "Franco suizo (CHF)",
        "Euro (EUR)": "Euro (EUR)",
        "Dollar américain (USD)": "Dólar estadounidense (USD)",
        "Peso argentin (ARS)": "Peso argentino (ARS)",
        "Ariary (MGA)": "Ariary (MGA)",
        "nature": "tipo",
        "Nature": "Tipo",
        "montant proposé": "importe propuesto",
        "tarif": "tarifa",
        "tarifs": "tarifas",
        "Tarifs": "Tarifas",
        "n° de facture": "n.º de factura",
        "date d'émission": "fecha de emisión",
        "total": "total",
        "réglé": "pagado",
        "émise par": "emitida por",
        "envoyée le": "enviada el",
        "relancée le": "avisada el",
        "facture": "factura",
        "factures": "facturas",
        "Facture": "Factura",
        "Factures": "Facturas",
        "montant unitaire": "importe unitario",
        "quantité": "cantidad",
        "ligne de facture": "línea de factura",
        "lignes de facture": "líneas de factura",
        "montant": "importe",
        "Montant": "Importe",
        "mode de paiement": "forma de pago",
        "encaissé par": "cobrado por",
        "Encaissé par": "Cobrado por",
        "paiement": "pago",
        "paiements": "pagos",
        "sens": "sentido",
        "Sens": "Sentido",
        "saisi par": "registrado por",
        "Saisi par": "Registrado por",
        "mouvement de caisse": "movimiento de caja",
        "mouvements de caisse": "movimientos de caja",
        "destinataire": "destinatario",
        "Destinataire": "Destinatario",
        "message": "mensaje",
        "erreur": "error",
        "tentatives": "intentos",
        "envoyé le": "enviado el",
        "Envoyé": "Enviado",
        "objet": "asunto",
        "Objet": "Asunto",
        "email en file": "correo en cola",
        "emails en file": "correos en cola",
        "Relance": "Aviso",
        "Amende": "Multa",
        "Nouvelle amende": "Nueva multa",
        "Cotisation": "Cuota",
        "cotisation annuelle": "cuota anual",
        "Cotisation annuelle": "Cuota anual",
        "À régler": "Por pagar",
        "Réglée": "Pagada",
        "Espèces": "Efectivo",
        "Virement": "Transferencia",
        "Entrée": "Entrada",
        "Sortie": "Salida",
        "Ajoutez au moins une ligne à la facture.":
            "Añada al menos una línea a la factura.",
        "Le montant doit être positif.": "El importe debe ser positivo.",
        "Le montant dépasse le solde de la facture (%(b)s).":
            "El importe supera el saldo de la factura (%(b)s).",
        "Libellé obligatoire.": "Etiqueta obligatoria.",
        "Montant obligatoire.": "Importe obligatorio.",
        "Autre motif (à décrire)": "Otro motivo (descríbalo)",
        "Motif": "Motivo",
        "Décrivez le motif.": "Describa el motivo.",
        "0 = pas de cotisation pour cette catégorie.":
            "0 = sin cuota para esta categoría.",
        "Facture %(num)s": "Factura %(num)s",
        "Émise le %(d)s": "Emitida el %(d)s",
        "Échéance : %(d)s": "Vencimiento: %(d)s",
        "DESTINATAIRE": "DESTINATARIO",
        "N° de carte : %(n)s": "N.º de carné: %(n)s",
        "Désignation": "Concepto",
        "Qté": "Cant.",
        "P.U.": "P. unit.",
        "Déjà réglé": "Ya pagado",
        "Reste à payer": "Saldo pendiente",
        "Réglée — merci.": "Pagada — gracias.",
        "Facture annulée": "Factura anulada",
        "%(lib)s — document généré par BibliOfelia":
            "%(lib)s — documento generado por BibliOfelia",
        "Cotisation %(cat)s — %(year)s": "Cuota %(cat)s — %(year)s",
        "Facture %(num)s — %(member)s": "Factura %(num)s — %(member)s",
        "Rappel — facture %(num)s": "Recordatorio — factura %(num)s",
        _REMINDER_BODY: (
            "Hola %(name)s:\n\nLa factura %(num)s por un importe de %(amount)s, "
            "vencida el %(due)s, todavía no se ha pagado.\nPase por la "
            "biblioteca para abonarla.\n\n%(library)s"
        ),
        _INVOICE_BODY: (
            "Hola %(name)s:\n\nAdjuntamos la factura %(num)s por un importe de "
            "%(amount)s, que debe pagarse antes del %(due)s.\n\n%(library)s"
        ),
        "%(n)s email(s) envoyé(s).": "%(n)s correo(s) enviado(s).",
        "%(n)s échec(s) d'envoi.": "%(n)s fallo(s) de envío.",
        "%(n)s email(s) laissé(s) en file : la Box n'est pas en ligne.":
            "%(n)s correo(s) en cola: la Box no está en línea.",
        _EMAILS_PENDING: (
            "%(n)s correo(s) en espera: saldrán en cuanto la Box esté en línea."
        ),
        "Rien à envoyer aujourd'hui.": "Nada que enviar hoy.",
        "Aucun email en attente.": "Ningún correo en espera.",
        "Mouvement de caisse enregistré.": "Movimiento de caja guardado.",
        "Mouvement refusé : %(e)s": "Movimiento rechazado: %(e)s",
        "Facture %(num)s créée (%(amount)s).": "Factura %(num)s creada (%(amount)s).",
        "Facture %(num)s réglée intégralement.": "Factura %(num)s pagada por completo.",
        "Encaissement enregistré. Reste %(b)s.": "Pago registrado. Quedan %(b)s.",
        "Cette facture est annulée.": "Esta factura está anulada.",
        "Facture déjà encaissée : elle ne peut plus être annulée.":
            "Factura ya cobrada: ya no se puede anular.",
        "Facture %(num)s annulée.": "Factura %(num)s anulada.",
        "%(name)s n'a pas d'adresse email sur sa fiche.":
            "%(name)s no tiene dirección de correo en su ficha.",
        "Facture envoyée par email.": "Factura enviada por correo.",
        "Facture mise en file : elle partira dès que la Box sera en ligne.":
            "Factura en cola: saldrá en cuanto la Box esté en línea.",
        "Tarif ajouté.": "Tarifa añadida.",
        "Tarif modifié.": "Tarifa modificada.",
        "Tarif supprimé.": "Tarifa eliminada.",
        "Frais d'animation": "Cuota de actividad",
        "Autre montant à facturer": "Otro importe que facturar",
        "Caisse": "Caja",
        "Cotisations, amendes, factures et paiements":
            "Cuotas, multas, facturas y pagos",
        "Entrées, sorties et paiements dus.": "Entradas, salidas y pagos pendientes.",
        "Solde de caisse": "Saldo de caja",
        "Entrées sur la période": "Entradas del periodo",
        "Sorties sur la période": "Salidas del periodo",
        "Dû par les usagers": "Adeudado por los usuarios",
        "La Box est en ligne : ils peuvent partir maintenant.":
            "La Box está en línea: pueden salir ahora.",
        "La Box n'est pas en ligne. Ils partiront dès qu'elle le sera.":
            "La Box no está en línea. Saldrán en cuanto lo esté.",
        "La Box est en ligne.": "La Box está en línea.",
        "La Box n'est pas en ligne : les envois attendent.":
            "La Box no está en línea: los envíos esperan.",
        "Mouvements de la période": "Movimientos del periodo",
        "Toutes les factures": "Todas las facturas",
        "Aucun mouvement sur cette période.": "Ningún movimiento en este periodo.",
        "Saisir un mouvement": "Registrar un movimiento",
        "Factures en retard": "Facturas vencidas",
        "Échue depuis %(d)s jour(s)": "Vencida hace %(d)s día(s)",
        "En retard de %(d)s jour(s)": "%(d)s día(s) de retraso",
        "Total dû par les usagers : %(t)s": "Total adeudado por los usuarios: %(t)s",
        "Tous": "Todas",
        "N°": "N.º",
        "Solde": "Saldo",
        "Aucune facture.": "Ninguna factura.",
        "N° de facture, nom, n° de carte…": "N.º de factura, nombre, n.º de carné…",
        "Nouvelle facture": "Nueva factura",
        "Créer la facture": "Crear la factura",
        "Lignes": "Líneas",
        _LINES_HINT: (
            "Deje una línea vacía si no la necesita. El importe es libre: no se "
            "calcula nada automáticamente."
        ),
        "Tarifs de la bibliothèque": "Tarifas de la biblioteca",
        "Rappel des montants usuels — à recopier dans les lignes ci-dessus.":
            "Recordatorio de los importes habituales, para copiarlos en las "
            "líneas de arriba.",
        _FEE_FREE_HINT: (
            "El motivo propone un importe, pero sigue siendo modificable. No se "
            "calcula ningún importe automáticamente."
        ),
        "Facture PDF": "Factura PDF",
        "Envoyer par email": "Enviar por correo",
        "Cet usager n’a pas d’adresse email.":
            "Este usuario no tiene dirección de correo.",
        "Annuler cette facture ? Elle restera visible, numérotée, mais ne sera plus due.":
            "¿Anular esta factura? Seguirá visible y numerada, pero ya no se "
            "adeudará.",
        "Annuler la facture": "Anular la factura",
        "Compte de l'usager": "Cuenta del usuario",
        "Émise le": "Emitida el",
        "Envoyée le": "Enviada el",
        "Relancée le": "Avisada el",
        "Encaissements": "Cobros",
        "Aucun encaissement pour l'instant.": "Ningún cobro por ahora.",
        "Encaisser": "Cobrar",
        "Enregistrer l'encaissement": "Guardar el cobro",
        "Un règlement en espèces crée automatiquement une entrée de caisse.":
            "Un pago en efectivo crea automáticamente una entrada de caja.",
        "Emails": "Correos",
        "File d'emails": "Cola de correos",
        "Factures et relances en attente d'envoi quand la Box est hors ligne.":
            "Facturas y avisos pendientes de envío cuando la Box está sin conexión.",
        "Aucun email en file.": "Ningún correo en cola.",
        "Compte": "Cuenta",
        "Compte et factures": "Cuenta y facturas",
        "Aucune facture pour cet usager.": "Ninguna factura para este usuario.",
        "Modifier un tarif": "Modificar una tarifa",
        "Montants proposés pour les animations, les amendes et les autres frais.":
            "Importes propuestos para las actividades, las multas y otros gastos.",
        "Cotisations par catégorie d'usager": "Cuotas por categoría de usuario",
        "Cotisation par catégorie d'usager, montants proposés pour les animations et les amendes.":
            "Cuota por categoría de usuario, importes propuestos para las "
            "actividades y las multas.",
        "Validité": "Validez",
        "%(n)s mois": "%(n)s meses",
        "gratuit": "gratuito",
        _MEMBERSHIP_HINT: (
            "La cuota se factura automáticamente al inscribirse y en cada "
            "renovación del carné. Se modifica en la administración de las "
            "categorías de usuario."
        ),
        "Autres tarifs": "Otras tarifas",
        "Supprimer ce tarif ?": "¿Eliminar esta tarifa?",
        "Aucun tarif enregistré.": "Ninguna tarifa registrada.",
        "Ajouter un tarif": "Añadir una tarifa",
        "À jour sur ses paiements": "Al día con sus pagos",
        "En retard de paiement : %(amount)s depuis le %(d)s":
            "Pago atrasado: %(amount)s desde el %(d)s",
        "Total dû : %(total)s": "Total adeudado: %(total)s",
        "%(amount)s à régler": "%(amount)s por pagar",
        "Prochaine échéance le %(d)s": "Próximo vencimiento el %(d)s",
        "%(d)s j de retard": "%(d)s d de retraso",
        "Coordonnées": "Datos de contacto",
        "email": "correo electrónico",
        "Reçoit les factures et les relances.": "Recibe las facturas y los avisos.",
        "rue et n°": "calle y número",
        "complément d'adresse": "complemento de dirección",
        "code postal": "código postal",
        "localité": "localidad",
        "état / province": "estado / provincia",
        "pays": "país",
        "Facultatif.": "Opcional.",
        "commentaire": "comentario",
        "Commentaire": "Comentario",
        "Commentaire libre, 500 caractères au maximum.":
            "Comentario libre, 500 caracteres como máximo.",
        "Carte valable jusqu'au %(d)s — renouvellement inutile.":
            "Carné válido hasta el %(d)s: no hace falta renovarlo.",
        "Carte déjà valable jusqu'au %(date)s : rien à renouveler.":
            "El carné ya es válido hasta el %(date)s: no hay nada que renovar.",
        "Facture de cotisation %(num)s émise.": "Factura de cuota %(num)s emitida.",
        "Facture de cotisation %(num)s émise (%(amount)s).":
            "Factura de cuota %(num)s emitida (%(amount)s).",
        # ── FEAT-088 + présences dès la création (2026-09-01) ──
        'Scannez une carte ou tapez les 4 derniers chiffres': 'Escanee un carné o teclee los 4 últimos dígitos',
        'Plusieurs cartes séparées par un espace ou une virgule. Vous pourrez aussi en ajouter après enregistrement.': 'Varios carnés separados por un espacio o una coma. También podrá añadir más después de guardar.',
        'Codes non reconnus ou ambigus : %(codes)s. Ajoutez ces personnes ci-dessous.': 'Códigos no reconocidos o ambiguos: %(codes)s. Añada a estas personas más abajo.',
        'Choisissez une devise.': 'Elija una moneda.',
        '« %(q)s » correspond à plusieurs devises : précisez.': '«%(q)s» coincide con varias monedas: sea más preciso.',
        '« %(q)s » ne correspond à aucune devise en circulation.': '«%(q)s» no coincide con ninguna moneda en circulación.',
        'Tapez au moins deux lettres : trigramme (CHF, VES…) ou nom de pays.': 'Teclee al menos dos letras: código (CHF, VES…) o nombre de país.',
        'CHF, Suisse, bolívar…': 'CHF, Suiza, bolívar…',
        'Sélectionnée : <b>%(code)s</b> — %(name)s (%(countries)s)': 'Seleccionada: <b>%(code)s</b> — %(name)s (%(countries)s)',
        'Aucune devise sélectionnée.': 'Ninguna moneda seleccionada.',
    },
    # ══════════════════════════════════════════════════════════════════════
    "mg": {
        "Heures": "Ora",
        "Minutes": "Minitra",
        "Indiquez le temps passé.": "Soraty ny fotoana lany.",
        "Modifiable : une journée oubliée se rattrape plus tard.":
            "Azo ovaina : ny andro hadino dia azo soratana any aoriana.",
        "On ne saisit pas le travail de demain.":
            "Tsy soratana ny asan'ny ampitso.",
        "— Nouvelle animation —": "— Hetsika vaovao —",
        "Laissez vide si vous avez choisi une animation dans la liste.":
            "Avelao foana raha efa nisafidy hetsika tao amin'ny lisitra ianao.",
        "Choisissez une animation ou donnez un intitulé.":
            "Misafidiana hetsika na omeo anarana.",
        "libellé": "anarana",
        "Libellé": "Anarana",
        "ordre": "filaharana",
        "Ordre": "Filaharana",
        "employé": "mpiasa",
        "temps passé (minutes)": "fotoana lany (minitra)",
        "%(h)s h %(m)02d": "%(h)s ora %(m)02d",
        "%(h)s h": "%(h)s ora",
        "%(m)s min": "%(m)s min",
        "non-membres adultes": "olon-dehibe tsy mpikambana",
        "non-membres enfants": "ankizy tsy mpikambana",
        "Non-membres adultes": "Olon-dehibe tsy mpikambana",
        "Non-membres enfants": "Ankizy tsy mpikambana",
        "bouclement": "famaranana ny andro",
        "bouclements": "famaranana ny andro",
        "Bouclement": "Famaranana ny andro",
        "actif": "mavitrika",
        "nature d'activité": "karazana asa",
        "natures d'activité": "karazana asa",
        "Natures d'activité": "Karazana asa",
        "activité": "asa",
        "activités": "asa",
        "note": "fanamarihana",
        "Note": "Fanamarihana",
        "intitulé": "lohateny",
        "Intitulé": "Lohateny",
        "type d'animation": "karazana hetsika",
        "types d'animation": "karazana hetsika",
        "Types d'animation": "Karazana hetsika",
        "animation": "hetsika",
        "animations": "hetsika",
        "Animation": "Hetsika",
        "Animations": "Hetsika",
        "animateur": "mpitarika",
        "présence": "fanatrehana",
        "présences": "fanatrehana",
        "Nouvelle animation": "Hetsika vaovao",
        "Activité enregistrée.": "Voatahiry ny asa.",
        "Animation enregistrée. Ajoutez maintenant les personnes présentes.":
            "Voatahiry ny hetsika. Ampio izao ireo olona nanatrika.",
        "%(name)s ajouté(e) à l'animation.": "Nampiana tao amin'ny hetsika i %(name)s.",
        "%(name)s était déjà noté(e) présent(e).":
            "Efa voasoratra ho nanatrika i %(name)s.",
        "%(name)s retiré(e).": "Nesorina i %(name)s.",
        "Aucun usager ne correspond à « %(q)s ».":
            "Tsy misy mpampiasa mifanaraka amin'ny « %(q)s ».",
        "Vous ne pouvez retirer que vos propres saisies.":
            "Ny soratrao ihany no azonao esorina.",
        "Vous ne pouvez retirer que vos propres animations.":
            "Ny hetsika nataonao ihany no azonao esorina.",
        "Saisie retirée.": "Nesorina ny soratra.",
        "Animation supprimée.": "Voafafa ny hetsika.",
        "Nature d'activité ajoutée.": "Nampiana karazana asa.",
        "Type d'animation ajouté.": "Nampiana karazana hetsika.",
        "« %(label)s » activé.": "Nalefa ny « %(label)s ».",
        "« %(label)s » désactivé — les saisies passées restent comptées.":
            "Natsahatra ny « %(label)s » — mbola isaina ireo soratra taloha.",
        "Mes activités": "Ny asako",
        "Ce que vous avez fait et le temps que vous y avez passé.":
            "Izay nataonao sy ny fotoana lany tamin'izany.",
        "Aucune nature d'activité n'est définie.":
            "Tsy misy karazana asa voafaritra.",
        "En créer": "Hamorona iray",
        "Demandez à un administrateur d'en créer.":
            "Angataho ny mpitantana hamorona iray.",
        "Mes dernières saisies": "Ny soratro farany",
        "Date": "Daty",
        "rattrapage": "nosoratana taty aoriana",
        "Temps": "Fotoana",
        "Retirer cette saisie ?": "Esorina ity soratra ity?",
        "Aucune saisie pour l'instant.": "Tsy misy soratra aloha.",
        "Retour au bouclement": "Miverina amin'ny famaranana ny andro",
        "Saisir une activité": "Manoratra asa",
        "Saisir une animation": "Manoratra hetsika",
        "Ce que vous avez présenté, et qui était là.":
            "Izay natolotrao, sy ireo izay tao.",
        "Enregistrer et ajouter les présents": "Tehirizo ary ampio ny mpanatrika",
        _ATTENDANCE_HINT: (
            "Isaina fotsiny ireo tsy mpikambana. Ny mpikambana nanatrika dia "
            "ampiana aorian'ny fitehirizana, amin'ny fanaovana scan ny karatra "
            "na amin'ny fanoratana ny isa 4 farany amin'ny laharany."
        ),
        "Dernières animations": "Hetsika farany",
        "Aucune animation enregistrée.": "Tsy misy hetsika voasoratra.",
        "Ajouter une personne présente": "Manampy olona nanatrika",
        "N° de carte ou 4 derniers chiffres": "Laharan-karatra na isa 4 farany",
        "0017 ou 2910000000017": "0017 na 2910000000017",
        "Plusieurs usagers correspondent à « %(q)s ». Choisissez la bonne personne.":
            "Mpampiasa maromaro no mifanaraka amin'ny « %(q)s ». Fidio ilay "
            "olona marina.",
        "Membres présents": "Mpikambana nanatrika",
        "Personne n'a encore été noté(e) présent(e).":
            "Mbola tsy nisy voasoratra ho nanatrika.",
        "Toutes les animations": "Ny hetsika rehetra",
        "Supprimer cette animation et toutes ses presences ?":
            "Fafana ity hetsika ity sy ny fanatrehana rehetra?",
        "%(m)s membre(s), %(n)s non-membre(s)":
            "mpikambana %(m)s, tsy mpikambana %(n)s",
        "Activités et animations": "Asa sy hetsika",
        "Les listes dans lesquelles les employés choisissent.":
            "Ireo lisitra isafidianan'ny mpiasa.",
        "Les listes dans lesquelles les employés choisissent au bouclement.":
            "Ireo lisitra isafidianan'ny mpiasa amin'ny famaranana ny andro.",
        _DEACTIVATED_TYPE: (
            "Ny karazana natsahatra dia manjavona amin'ny taratasy fenoina, "
            "saingy mbola isaina amin'ny antontan'isa ireo soratra taloha."
        ),
        "Aucun type d'animation.": "Tsy misy karazana hetsika.",
        "Aucune nature d'activité.": "Tsy misy karazana asa.",
        "Ajouter une nature d'activité": "Manampy karazana asa",
        "Ajouter un type d'animation": "Manampy karazana hetsika",
        "Activer": "Alefaso",
        "Créé par": "Noforonin'i",
        _FREE_LABEL_HINT: (
            "Ny mpitarika koa dia afaka mamorona lohateny avy amin'ny taratasy "
            "fenoiny — mipoitra amin'io andro io ihany ny hetsika iray."
        ),
        "Statistiques d'activité": "Antontan'isa momba ny asa",
        "Animations, participants et temps passé.":
            "Hetsika, mpanatrika ary fotoana lany.",
        "Afficher": "Asehoy",
        "Export CSV": "Fanondranana CSV",
        _STATS_SENTENCE: (
            "Nikarakara hetsika %(s)s ny tranomboky, ka mpikambana %(m)s no "
            "nanatrika ary, amin'ireo tsy mpikambana, olon-dehibe %(a)s sy "
            "ankizy %(c)s."
        ),
        "Participations de membres": "Fanatrehan'ny mpikambana",
        "Heures d'animation": "Ora hetsika",
        "Mois par mois": "Isam-bolana",
        "Mois": "Volana",
        "Non-membres": "Tsy mpikambana",
        "Minutes d'activité": "Minitra asa",
        "Saisies": "Soratra",
        "Temps par nature d'activité": "Fotoana isaky ny karazana asa",
        "Aucune activité saisie sur cette année.":
            "Tsy misy asa voasoratra amin'ity taona ity.",
        "Fin de service du %(d)s": "Fiafaran'ny asa ny %(d)s",
        "1. Vos activités et animations du jour":
            "1. Ny asanao sy ny hetsikao androany",
        "Saisi": "Voasoratra",
        "À faire": "Mbola atao",
        "Vous n'avez rien saisi aujourd'hui.": "Tsy nanoratra na inona na inona ianao androany.",
        "2. Mouvements de caisse du jour": "2. Fihetsehan'ny vola androany",
        "Entrées": "Vola miditra",
        "Sorties": "Vola mivoaka",
        "Aucun mouvement aujourd'hui.": "Tsy misy fihetsehana androany.",
        "Solde du jour": "Ambim-bola androany",
        "Ouvrir la caisse": "Sokafy ny kitapom-bola",
        "3. Factures et relances à envoyer": "3. Faktiora sy fampahatsiahivana halefa",
        "En ligne": "Misy fifandraisana",
        "Hors ligne": "Tsy misy fifandraisana",
        "Factures jamais envoyées": "Faktiora mbola tsy nalefa",
        "Relances dues": "Fampahatsiahivana tokony halefa",
        "échue depuis %(d)s jour(s)": "efa lany andro %(d)s",
        "Voir la file": "Jereo ny filaharana",
        _OFFLINE_QUEUE: (
            "Tsy misy fifandraisana ny Box : mijanona eo amin'ny filaharana ny "
            "mailaka ary halefa raha vao misy fifandraisana. Ny mpitantana koa "
            "dia afaka mandefa azy ireo avy amin'ny efijery kitapom-bola."
        ),
        "Envoyer maintenant": "Alefaso izao",
        "Mettre en file d'attente": "Apetraho eo amin'ny filaharana",
        "4. Sauvegardes": "4. Tahiry",
        "Faite": "Vita",
        "Lancer la sauvegarde": "Alefaso ny tahiry",
        "5. Éteindre la Box": "5. Vonoy ny Box",
        "Demande d'extinction enregistrée.": "Voarakitra ny fangatahana famonoana.",
        _SHUTDOWN_NOTE: (
            "Miasa anaty conteneur ny BibliOfelia ka tsy afaka mamono ny Box "
            "mivantana : mametraka fangatahana arahin'ny serivisy rafitry ny Box "
            "izy. Raha tsy misy io serivisy io, voarakitra ny fangatahana "
            "saingy tsy hivonona ny Box."
        ),
        "Demander l extinction de la Box ? Toutes les applications seront arretees.":
            "Angatahina ny famonoana ny Box? Hatsahatra daholo ny rindrambaiko rehetra.",
        "Demander l'extinction": "Angataho ny famonoana",
        "Seul un administrateur peut éteindre la Box.":
            "Ny mpitantana ihany no afaka mamono ny Box.",
        "Cette instance n'est pas la Box : rien à éteindre.":
            "Tsy Box ity : tsy misy vonoina.",
        _SHUTDOWN_DONE: (
            "Voarakitra ny fangatahana famonoana (%(p)s). Hivonona ny Box raha "
            "misy ny serivisy rafitra famonoana."
        ),
        "Demande impossible : %(e)s": "Tsy vita ny fangatahana : %(e)s",
        "Activités, caisse, sauvegardes et fin de journée":
            "Asa, kitapom-bola, tahiry ary fiafaran'ny andro",
        "Caisse — devise et échéances": "Kitapom-bola — vola sy daty farany",
        "Email (SMTP)": "Mailaka (SMTP)",
        "Pays": "Firenena",
        "Devise": "Vola",
        "Décimales affichées": "Isa aorian'ny faingo aseho",
        "Vide = valeur usuelle de la devise choisie.":
            "Foana = ny sanda mahazatra amin'ny vola nofidina.",
        "Délai de paiement (jours)": "Fe-potoana fandoavam-bola (andro)",
        "Échéance par défaut d'une facture, à compter de son émission.":
            "Daty farany mahazatra amin'ny faktiora, manomboka amin'ny "
            "famoahana azy.",
        "Envoi d'emails activé": "Alefa ny mailaka",
        "Serveur SMTP": "Serivera SMTP",
        "Port": "Port",
        "Chiffrement TLS": "Fanafenana TLS",
        "Adresse d'expéditeur": "Adiresin'ny mpandefa",
        "Indiquez un serveur SMTP, ou désactivez l'envoi d'emails.":
            "Soraty ny serivera SMTP, na atsaharo ny fandefasana mailaka.",
        "Bolívar (VES)": "Bolívar (VES)",
        "Franc suisse (CHF)": "Farantsa soisa (CHF)",
        "Euro (EUR)": "Eoro (EUR)",
        "Dollar américain (USD)": "Dolara amerikana (USD)",
        "Peso argentin (ARS)": "Peso arzantina (ARS)",
        "Ariary (MGA)": "Ariary (MGA)",
        "nature": "karazana",
        "Nature": "Karazana",
        "montant proposé": "sandan-bola atolotra",
        "tarif": "sarany",
        "tarifs": "sarany",
        "Tarifs": "Sarany",
        "n° de facture": "laharan'ny faktiora",
        "date d'émission": "daty namoahana",
        "total": "totaly",
        "réglé": "voaloa",
        "émise par": "navoakan'i",
        "envoyée le": "nalefa ny",
        "relancée le": "nampahatsiahivina ny",
        "facture": "faktiora",
        "factures": "faktiora",
        "Facture": "Faktiora",
        "Factures": "Faktiora",
        "montant unitaire": "sandan'ny iray",
        "quantité": "isa",
        "ligne de facture": "andalan'ny faktiora",
        "lignes de facture": "andalan'ny faktiora",
        "montant": "sandan-bola",
        "Montant": "Sandan-bola",
        "mode de paiement": "fomba fandoavana",
        "encaissé par": "noraisin'i",
        "Encaissé par": "Noraisin'i",
        "paiement": "fandoavam-bola",
        "paiements": "fandoavam-bola",
        "sens": "lalana",
        "Sens": "Lalana",
        "saisi par": "nosoratan'i",
        "Saisi par": "Nosoratan'i",
        "mouvement de caisse": "fihetsehan'ny vola",
        "mouvements de caisse": "fihetsehan'ny vola",
        "destinataire": "mpandray",
        "Destinataire": "Mpandray",
        "message": "hafatra",
        "erreur": "hadisoana",
        "tentatives": "andrana",
        "envoyé le": "nalefa ny",
        "Envoyé": "Nalefa",
        "objet": "lohahevitra",
        "Objet": "Lohahevitra",
        "email en file": "mailaka miandry",
        "emails en file": "mailaka miandry",
        "Relance": "Fampahatsiahivana",
        "Amende": "Lamandy",
        "Nouvelle amende": "Lamandy vaovao",
        "Cotisation": "Saram-pikambanana",
        "cotisation annuelle": "saram-pikambanana isan-taona",
        "Cotisation annuelle": "Saram-pikambanana isan-taona",
        "À régler": "Tsy mbola voaloa",
        "Réglée": "Voaloa",
        "Espèces": "Vola vaventy",
        "Virement": "Famindram-bola",
        "Entrée": "Miditra",
        "Sortie": "Mivoaka",
        "Ajoutez au moins une ligne à la facture.":
            "Ampio andalana iray farafahakeliny ny faktiora.",
        "Le montant doit être positif.": "Tsy maintsy mihoatra ny aotra ny sandan-bola.",
        "Le montant dépasse le solde de la facture (%(b)s).":
            "Mihoatra ny ambim-bolan'ny faktiora ny sandan-bola (%(b)s).",
        "Libellé obligatoire.": "Tsy maintsy misy anarana.",
        "Montant obligatoire.": "Tsy maintsy misy sandan-bola.",
        "Autre motif (à décrire)": "Antony hafa (lazao)",
        "Motif": "Antony",
        "Décrivez le motif.": "Lazao ny antony.",
        "0 = pas de cotisation pour cette catégorie.":
            "0 = tsy misy saram-pikambanana amin'ity sokajy ity.",
        "Facture %(num)s": "Faktiora %(num)s",
        "Émise le %(d)s": "Navoaka ny %(d)s",
        "Échéance : %(d)s": "Daty farany : %(d)s",
        "DESTINATAIRE": "MPANDRAY",
        "N° de carte : %(n)s": "Laharan-karatra : %(n)s",
        "Désignation": "Anarana",
        "Qté": "Isa",
        "P.U.": "Vidiny",
        "Déjà réglé": "Efa voaloa",
        "Reste à payer": "Sisa haloa",
        "Réglée — merci.": "Voaloa — misaotra.",
        "Facture annulée": "Faktiora nofoanana",
        "%(lib)s — document généré par BibliOfelia":
            "%(lib)s — antontan-taratasy noforonin'ny BibliOfelia",
        "Cotisation %(cat)s — %(year)s": "Saram-pikambanana %(cat)s — %(year)s",
        "Facture %(num)s — %(member)s": "Faktiora %(num)s — %(member)s",
        "Rappel — facture %(num)s": "Fampahatsiahivana — faktiora %(num)s",
        _REMINDER_BODY: (
            "Salama %(name)s,\n\nNy faktiora %(num)s mitentina %(amount)s, lany "
            "ny %(due)s, dia mbola tsy voaloa.\nAndeha any amin'ny tranomboky "
            "handoa azy.\n\n%(library)s"
        ),
        _INVOICE_BODY: (
            "Salama %(name)s,\n\nIndro ny faktiora %(num)s mitentina %(amount)s, "
            "tokony haloa alohan'ny %(due)s.\n\n%(library)s"
        ),
        "%(n)s email(s) envoyé(s).": "Mailaka %(n)s no nalefa.",
        "%(n)s échec(s) d'envoi.": "Tsy tafiditra ny mailaka %(n)s.",
        "%(n)s email(s) laissé(s) en file : la Box n'est pas en ligne.":
            "Mailaka %(n)s no navela eo amin'ny filaharana : tsy misy "
            "fifandraisana ny Box.",
        _EMAILS_PENDING: (
            "Mailaka %(n)s no miandry : halefa raha vao misy fifandraisana ny Box."
        ),
        "Rien à envoyer aujourd'hui.": "Tsy misy alefa androany.",
        "Aucun email en attente.": "Tsy misy mailaka miandry.",
        "Mouvement de caisse enregistré.": "Voatahiry ny fihetsehan'ny vola.",
        "Mouvement refusé : %(e)s": "Tsy nekena ny fihetsehana : %(e)s",
        "Facture %(num)s créée (%(amount)s).": "Noforonina ny faktiora %(num)s (%(amount)s).",
        "Facture %(num)s réglée intégralement.": "Voaloa tanteraka ny faktiora %(num)s.",
        "Encaissement enregistré. Reste %(b)s.": "Voatahiry ny fandoavana. Sisa %(b)s.",
        "Cette facture est annulée.": "Nofoanana ity faktiora ity.",
        "Facture déjà encaissée : elle ne peut plus être annulée.":
            "Efa voaloa ny faktiora : tsy azo foanana intsony.",
        "Facture %(num)s annulée.": "Nofoanana ny faktiora %(num)s.",
        "%(name)s n'a pas d'adresse email sur sa fiche.":
            "Tsy manana adiresy mailaka ao amin'ny taratasiny i %(name)s.",
        "Facture envoyée par email.": "Nalefa tamin'ny mailaka ny faktiora.",
        "Facture mise en file : elle partira dès que la Box sera en ligne.":
            "Napetraka eo amin'ny filaharana ny faktiora : halefa raha vao misy "
            "fifandraisana ny Box.",
        "Tarif ajouté.": "Nampiana sarany.",
        "Tarif modifié.": "Novaina ny sarany.",
        "Tarif supprimé.": "Voafafa ny sarany.",
        "Frais d'animation": "Saran'ny hetsika",
        "Autre montant à facturer": "Sandan-bola hafa hofakturaina",
        "Caisse": "Kitapom-bola",
        "Cotisations, amendes, factures et paiements":
            "Saram-pikambanana, lamandy, faktiora ary fandoavam-bola",
        "Entrées, sorties et paiements dus.":
            "Vola miditra, vola mivoaka ary vola tokony haloa.",
        "Solde de caisse": "Ambim-bola",
        "Entrées sur la période": "Vola niditra tamin'ny vanim-potoana",
        "Sorties sur la période": "Vola nivoaka tamin'ny vanim-potoana",
        "Dû par les usagers": "Trosan'ny mpampiasa",
        "La Box est en ligne : ils peuvent partir maintenant.":
            "Misy fifandraisana ny Box : azo alefa izao izy ireo.",
        "La Box n'est pas en ligne. Ils partiront dès qu'elle le sera.":
            "Tsy misy fifandraisana ny Box. Halefa izy ireo raha vao misy.",
        "La Box est en ligne.": "Misy fifandraisana ny Box.",
        "La Box n'est pas en ligne : les envois attendent.":
            "Tsy misy fifandraisana ny Box : miandry ny fandefasana.",
        "Mouvements de la période": "Fihetsehana tamin'ny vanim-potoana",
        "Toutes les factures": "Ny faktiora rehetra",
        "Aucun mouvement sur cette période.":
            "Tsy misy fihetsehana tamin'ity vanim-potoana ity.",
        "Saisir un mouvement": "Manoratra fihetsehana",
        "Factures en retard": "Faktiora efa lany daty",
        "Échue depuis %(d)s jour(s)": "Efa lany andro %(d)s",
        "En retard de %(d)s jour(s)": "Tara andro %(d)s",
        "Total dû par les usagers : %(t)s": "Totalin'ny trosan'ny mpampiasa : %(t)s",
        "Tous": "Rehetra",
        "N°": "Lah.",
        "Solde": "Ambim-bola",
        "Aucune facture.": "Tsy misy faktiora.",
        "N° de facture, nom, n° de carte…":
            "Laharan'ny faktiora, anarana, laharan-karatra…",
        "Nouvelle facture": "Faktiora vaovao",
        "Créer la facture": "Hamorona ny faktiora",
        "Lignes": "Andalana",
        _LINES_HINT: (
            "Avelao foana ny andalana raha tsy ilainao. Malalaka ny sandan-bola : "
            "tsy misy kajy mandeha ho azy."
        ),
        "Tarifs de la bibliothèque": "Saran'ny tranomboky",
        "Rappel des montants usuels — à recopier dans les lignes ci-dessus.":
            "Fampahatsiahivana ny sandan-bola mahazatra — adikao ao amin'ny "
            "andalana etsy ambony.",
        _FEE_FREE_HINT: (
            "Manolotra sandan-bola ny antony, saingy azo ovaina izany. Tsy misy "
            "sandan-bola kajiana mandeha ho azy."
        ),
        "Facture PDF": "Faktiora PDF",
        "Envoyer par email": "Alefaso amin'ny mailaka",
        "Cet usager n’a pas d’adresse email.":
            "Tsy manana adiresy mailaka ity mpampiasa ity.",
        "Annuler cette facture ? Elle restera visible, numérotée, mais ne sera plus due.":
            "Foanana ity faktiora ity? Mbola hita sy misy laharana izy, saingy "
            "tsy trosa intsony.",
        "Annuler la facture": "Foano ny faktiora",
        "Compte de l'usager": "Kaontin'ny mpampiasa",
        "Émise le": "Navoaka ny",
        "Envoyée le": "Nalefa ny",
        "Relancée le": "Nampahatsiahivina ny",
        "Encaissements": "Vola noraisina",
        "Aucun encaissement pour l'instant.": "Tsy mbola nisy vola noraisina.",
        "Encaisser": "Mandray vola",
        "Enregistrer l'encaissement": "Tehirizo ny vola noraisina",
        "Un règlement en espèces crée automatiquement une entrée de caisse.":
            "Ny fandoavana amin'ny vola vaventy dia mamorona vola miditra "
            "mandeha ho azy.",
        "Emails": "Mailaka",
        "File d'emails": "Filaharan'ny mailaka",
        "Factures et relances en attente d'envoi quand la Box est hors ligne.":
            "Faktiora sy fampahatsiahivana miandry halefa rehefa tsy misy "
            "fifandraisana ny Box.",
        "Aucun email en file.": "Tsy misy mailaka eo amin'ny filaharana.",
        "Compte": "Kaonty",
        "Compte et factures": "Kaonty sy faktiora",
        "Aucune facture pour cet usager.": "Tsy misy faktiora ho an'ity mpampiasa ity.",
        "Modifier un tarif": "Hanova sarany",
        "Montants proposés pour les animations, les amendes et les autres frais.":
            "Sandan-bola atolotra ho an'ny hetsika, ny lamandy ary ny sarany hafa.",
        "Cotisations par catégorie d'usager":
            "Saram-pikambanana isaky ny sokajin'ny mpampiasa",
        "Cotisation par catégorie d'usager, montants proposés pour les animations et les amendes.":
            "Saram-pikambanana isaky ny sokajin'ny mpampiasa, sandan-bola "
            "atolotra ho an'ny hetsika sy ny lamandy.",
        "Validité": "Faharetany",
        "%(n)s mois": "Volana %(n)s",
        "gratuit": "maimaim-poana",
        _MEMBERSHIP_HINT: (
            "Fakturaina mandeha ho azy ny saram-pikambanana rehefa misoratra "
            "anarana sy isaky ny fanavaozana ny karatra. Ovaina ao amin'ny "
            "fitantanana ny sokajin'ny mpampiasa izy."
        ),
        "Autres tarifs": "Sarany hafa",
        "Supprimer ce tarif ?": "Fafana ity sarany ity?",
        "Aucun tarif enregistré.": "Tsy misy sarany voasoratra.",
        "Ajouter un tarif": "Manampy sarany",
        "À jour sur ses paiements": "Mandoa ara-potoana",
        "En retard de paiement : %(amount)s depuis le %(d)s":
            "Tara ny fandoavana : %(amount)s hatramin'ny %(d)s",
        "Total dû : %(total)s": "Totalin'ny trosa : %(total)s",
        "%(amount)s à régler": "%(amount)s tsy mbola voaloa",
        "Prochaine échéance le %(d)s": "Daty farany manaraka ny %(d)s",
        "%(d)s j de retard": "Tara andro %(d)s",
        "Coordonnées": "Fifandraisana",
        "email": "mailaka",
        "Reçoit les factures et les relances.":
            "Mandray ny faktiora sy ny fampahatsiahivana.",
        "rue et n°": "arabe sy laharana",
        "complément d'adresse": "fanampin'ny adiresy",
        "code postal": "kaody paositra",
        "localité": "tanàna",
        "état / province": "faritany",
        "pays": "firenena",
        "Facultatif.": "Tsy voatery.",
        "commentaire": "fanamarihana",
        "Commentaire": "Fanamarihana",
        "Commentaire libre, 500 caractères au maximum.":
            "Fanamarihana malalaka, 500 litera farafahabetsany.",
        "Carte valable jusqu'au %(d)s — renouvellement inutile.":
            "Manan-kery hatramin'ny %(d)s ny karatra — tsy ilaina ny "
            "fanavaozana.",
        "Carte déjà valable jusqu'au %(date)s : rien à renouveler.":
            "Efa manan-kery hatramin'ny %(date)s ny karatra : tsy misy "
            "havaozina.",
        "Facture de cotisation %(num)s émise.":
            "Navoaka ny faktioran'ny saram-pikambanana %(num)s.",
        "Facture de cotisation %(num)s émise (%(amount)s).":
            "Navoaka ny faktioran'ny saram-pikambanana %(num)s (%(amount)s).",
        # ── FEAT-088 + présences dès la création (2026-09-01) ──
        'Scannez une carte ou tapez les 4 derniers chiffres': 'Scannez karatra na soraty ny isa 4 farany',
        'Plusieurs cartes séparées par un espace ou une virgule. Vous pourrez aussi en ajouter après enregistrement.': "Karatra maromaro sarahin'ny elanelana na faingo. Afaka manampy koa ianao aorian'ny fitehirizana.",
        'Codes non reconnus ou ambigus : %(codes)s. Ajoutez ces personnes ci-dessous.': 'Kaody tsy fantatra na tsy mazava : %(codes)s. Ampio etsy ambany ireo olona ireo.',
        'Choisissez une devise.': 'Misafidiana vola.',
        '« %(q)s » correspond à plusieurs devises : précisez.': "Mifanaraka amin'ny vola maromaro ny « %(q)s » : hazavao.",
        '« %(q)s » ne correspond à aucune devise en circulation.': "Tsy mifanaraka amin'ny vola mandeha ny « %(q)s ».",
        'Tapez au moins deux lettres : trigramme (CHF, VES…) ou nom de pays.': 'Soraty litera roa farafahakeliny : kaody (CHF, VES…) na anaram-pirenena.',
        'CHF, Suisse, bolívar…': 'CHF, Soisa, bolívar…',
        'Sélectionnée : <b>%(code)s</b> — %(name)s (%(countries)s)': 'Voafidy : <b>%(code)s</b> — %(name)s (%(countries)s)',
        'Aucune devise sélectionnée.': 'Tsy misy vola voafidy.',
    },
}


PLURALS: dict[str, dict[str, tuple[str, str]]] = {
    "en": {
        'Animation enregistrée avec %(n)s personne présente.': (
            'Event saved with %(n)s attendee.',
            'Event saved with %(n)s attendees.',
        ),
        "%(n)s email attend encore dans la file.": (
            "%(n)s email is still waiting in the queue.",
            "%(n)s emails are still waiting in the queue.",
        ),
        "%(n)s email en attente d'envoi": (
            "%(n)s email waiting to be sent",
            "%(n)s emails waiting to be sent",
        ),
        "Envoyer %(n)s email en attente": (
            "Send %(n)s waiting email",
            "Send the %(n)s waiting emails",
        ),
    },
    "es": {
        'Animation enregistrée avec %(n)s personne présente.': (
            'Actividad guardada con %(n)s asistente.',
            'Actividad guardada con %(n)s asistentes.',
        ),
        "%(n)s email attend encore dans la file.": (
            "%(n)s correo sigue esperando en la cola.",
            "%(n)s correos siguen esperando en la cola.",
        ),
        "%(n)s email en attente d'envoi": (
            "%(n)s correo pendiente de envío",
            "%(n)s correos pendientes de envío",
        ),
        "Envoyer %(n)s email en attente": (
            "Enviar %(n)s correo pendiente",
            "Enviar los %(n)s correos pendientes",
        ),
    },
    "mg": {
        'Animation enregistrée avec %(n)s personne présente.': (
            "Voatahiry ny hetsika miaraka amin'ny mpanatrika %(n)s.",
            "Voatahiry ny hetsika miaraka amin'ny mpanatrika %(n)s.",
        ),
        "%(n)s email attend encore dans la file.": (
            "Mailaka %(n)s no mbola miandry eo amin'ny filaharana.",
            "Mailaka %(n)s no mbola miandry eo amin'ny filaharana.",
        ),
        "%(n)s email en attente d'envoi": (
            "Mailaka %(n)s miandry halefa",
            "Mailaka %(n)s miandry halefa",
        ),
        "Envoyer %(n)s email en attente": (
            "Alefaso ny mailaka %(n)s miandry",
            "Alefaso ny mailaka %(n)s miandry",
        ),
    },
}


def _unescape(value: str) -> str:
    return value.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _read_value(lines: list[str], start: int, keyword: str) -> tuple[str, int]:
    """Lit `keyword "..."` + ses lignes de continuation. Renvoie (valeur, index suivant)."""
    first = lines[start][len(keyword):].strip()
    parts = [_unescape(first.strip('"'))]
    i = start + 1
    while i < len(lines) and lines[i].startswith('"'):
        parts.append(_unescape(lines[i].strip().strip('"')))
        i += 1
    return "".join(parts), i


def _clean_comments(block: list[str]) -> list[str]:
    """Retire le drapeau `fuzzy` et les anciens msgid `#|` d'un bloc traduit."""
    out = []
    for line in block:
        if line.startswith("#|"):
            continue
        if line.startswith("#,"):
            flags = [f.strip() for f in line[2:].split(",") if f.strip() != "fuzzy"]
            if not flags:
                continue
            line = "#, " + ", ".join(flags)
        out.append(line)
    return out


def apply_lang(lang: str) -> tuple[int, int]:
    """Applique les traductions du sprint à un `.po`. Renvoie (simples, pluriels)."""
    po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"
    if not po_path.exists():
        return 0, 0
    singles = TRANSLATIONS.get(lang, {})
    plurals = PLURALS.get(lang, {})
    lines = po_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    pending: list[str] = []  # commentaires en attente du msgid courant
    n_single = n_plural = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("#"):
            pending.append(line)
            i += 1
            continue
        if not line.startswith("msgid "):
            out.extend(pending)
            pending = []
            out.append(line)
            i += 1
            continue

        msgid, j = _read_value(lines, i, "msgid ")
        header = lines[i:j]

        if j < len(lines) and lines[j].startswith("msgid_plural "):
            _plural_id, k = _read_value(lines, j, "msgid_plural ")
            header = header + lines[j:k]
            while k < len(lines) and re.match(r"^msgstr\[\d\] ", lines[k]):
                _v, k = _read_value(lines, k, lines[k][: lines[k].index(" ") + 1])
            if msgid in plurals:
                sing, plur = plurals[msgid]
                out.extend(_clean_comments(pending))
                out.extend(header)
                out.append(f'msgstr[0] "{_escape(sing)}"')
                out.append(f'msgstr[1] "{_escape(plur)}"')
                n_plural += 1
            else:
                out.extend(pending)
                out.extend(lines[i:k])
            pending = []
            i = k
            continue

        if j < len(lines) and lines[j].startswith("msgstr "):
            _v, k = _read_value(lines, j, "msgstr ")
            if msgid in singles and singles[msgid]:
                out.extend(_clean_comments(pending))
                out.extend(header)
                out.append(f'msgstr "{_escape(singles[msgid])}"')
                n_single += 1
            else:
                out.extend(pending)
                out.extend(lines[i:k])
            pending = []
            i = k
            continue

        out.extend(pending)
        pending = []
        out.extend(header)
        i = j

    out.extend(pending)
    # « Écrire un fichier sans le vider » : on encode d'abord, on écrit ensuite
    # en binaire. `write_text` tronquerait le .po AVANT d'encoder, et un seul
    # caractère non encodable laisserait un fichier de traductions vide.
    payload = ("\n".join(out) + "\n").encode("utf-8")
    with open(po_path, "wb") as handle:
        handle.write(payload)
    return n_single, n_plural


def main() -> None:
    for lang in ("en", "es", "mg"):
        single, plural = apply_lang(lang)
        print(f"[{lang}] {single} chaîne(s) + {plural} pluriel(s)")


if __name__ == "__main__":
    main()
