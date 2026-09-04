#!/usr/bin/env python3
"""Traductions Sprint 32 — FR → EN/ES/MG.

Couvre FEAT-089 (catégories d'usagers gérées depuis la page tarifs).

Vocabulaire aligné sur le Sprint 31 : *cotisation* → membership fee / cuota /
saram-pikambanana ; *usager* → member / usuario / mpampiasa.

Le mécanisme (`apply_lang`, blocs `msgid_plural`, écriture binaire) est repris
de `scripts/translations_sprint31.py`.

À rejouer APRÈS `makemessages` (qui réinsère les msgid) :
    python scripts/translations_sprint32.py
"""
from __future__ import annotations

import re
from pathlib import Path

LOCALE_DIR = Path(__file__).parent.parent / "locale"

_SUBTITLE = (
    "Catégories d'usagers (cotisation, prêts, validité de la carte) et "
    "montants proposés pour les animations et les amendes."
)
_ADVANCED_SUB = (
    "Catégories d'usagers, cotisation, montants proposés pour les animations "
    "et les amendes."
)
_FEE_HINT = (
    "La cotisation est facturée automatiquement à l'inscription et à chaque "
    "renouvellement de carte. Un montant à 0 n'émet aucune facture."
)
_FEE_HELP = (
    "0 = gratuit : aucune facture à l'inscription ni au renouvellement."
)
_PROTECT = (
    "La fiche d'un usager tient à sa catégorie : la supprimer casserait "
    "ces fiches."
)
_CODE_ERR = (
    "Lettres, chiffres, tiret et underscore uniquement, sans espace."
)

TRANSLATIONS = {
    "en": {
        "Tarifs et Catégories d'usagers": "Tariffs and member categories",
        _SUBTITLE: (
            "Member categories (membership fee, loans, card validity) and "
            "suggested amounts for events and fines."
        ),
        _ADVANCED_SUB: (
            "Member categories, membership fee, suggested amounts for events "
            "and fines."
        ),
        "Catégories d'usagers": "Member categories",
        "Nouvelle catégorie": "New category",
        "Aucune catégorie d'usager.": "No member category.",
        "Prêts max": "Max loans",
        "Durée de prêt": "Loan period",
        "%(n)s j": "%(n)s d",
        "Usagers": "Members",
        _FEE_HINT: (
            "The membership fee is billed automatically at registration and "
            "at each card renewal. An amount of 0 issues no invoice."
        ),
        "Nouvelle catégorie d'usager": "New member category",
        "Modifier la catégorie d'usager": "Edit member category",
        "Modifier la catégorie": "Edit category",
        "Nom (français)": "Name (French)",
        "Nom (anglais)": "Name (English)",
        "Nom (espagnol)": "Name (Spanish)",
        "Nom (malgache)": "Name (Malagasy)",
        "Types de documents autorisés": "Allowed document types",
        "Aucun coché = tous les types sont autorisés.": (
            "None checked = every document type is allowed."
        ),
        "Court, sans espace : ADULTE, ENFANT…": (
            "Short, no spaces: ADULT, CHILD…"
        ),
        "Nom affiché si les autres traductions manquent.": (
            "Name shown if the other translations are missing."
        ),
        _FEE_HELP: (
            "0 = free: no invoice at registration or renewal."
        ),
        "Validité de la carte (mois)": "Card validity (months)",
        "Prêts simultanés maximum": "Maximum simultaneous loans",
        "Durée de prêt (jours)": "Loan period (days)",
        _CODE_ERR: "Letters, digits, hyphen and underscore only, no spaces.",
        "Le montant ne peut pas être négatif.": "The amount cannot be negative.",
        "Catégorie d'usager créée.": "Member category created.",
        "Catégorie d'usager mise à jour.": "Member category updated.",
        "Catégorie d'usager supprimée.": "Member category deleted.",
        "Supprimer la catégorie d'usager": "Delete member category",
        "Cette catégorie n'a aucun usager : elle peut être supprimée.": (
            "This category has no members: it can be deleted."
        ),
        _PROTECT: (
            "A member record is tied to its category: deleting it would "
            "break those records."
        ),
        "Retour": "Back",
        "Changement de catégorie : cotisation recalculée.": (
            "Category change: membership fee recalculated."
        ),
        "Changement de catégorie : plus de cotisation.": (
            "Category change: no membership fee."
        ),
        "Cotisation recalculée : facture %(old)s annulée, %(new)s émise (%(amount)s).": (
            "Membership fee updated: invoice %(old)s cancelled, %(new)s issued (%(amount)s)."
        ),
        "Facture de cotisation %(num)s annulée : la nouvelle catégorie n'en a pas.": (
            "Membership invoice %(num)s cancelled: the new category has none."
        ),
        "Email non configuré": "Email not configured",
        "L'envoi par email n'est pas configuré. Renseignez le serveur SMTP dans Avancé → Paramètres → Email, puis renvoyez.": (
            "Email sending is not configured. Fill in the SMTP server under "
            "Advanced → Settings → Email, then send again."
        ),
        "L'envoi par email n'est pas configuré (Avancé → Paramètres → Email).": (
            "Email sending is not configured (Advanced → Settings → Email)."
        ),
        "Les emails en attente partent tout de suite.": (
            "Queued emails will go out straight away."
        ),
        "Ils peuvent partir maintenant.": "They can go out now.",
        "Imprimer la carte (62 mm)": "Print the card (62 mm)",
        "La Box n'est pas en ligne : les emails restent en file jusqu'à ce qu'elle le soit. En attendant, prévenez les personnes par téléphone (liste ci-dessus).": (
            "The Box is offline: emails stay in the queue until it is back. "
            "In the meantime, notify people by phone (list above)."
        ),
        "La Box n'est pas en ligne : prévenez les personnes par téléphone, ou renvoyez quand elle le sera.": (
            "The Box is offline: notify people by phone, or send again when it is back."
        ),
        "La Box n'est pas en ligne. Prévenez les personnes par téléphone, ou renvoyez quand elle le sera.": (
            "The Box is offline. Notify people by phone, or send again when it is back."
        ),
    },
    "es": {
        "Tarifs et Catégories d'usagers": "Tarifas y categorías de usuarios",
        _SUBTITLE: (
            "Categorías de usuarios (cuota, préstamos, validez de la tarjeta) "
            "y importes propuestos para actividades y multas."
        ),
        _ADVANCED_SUB: (
            "Categorías de usuarios, cuota, importes propuestos para "
            "actividades y multas."
        ),
        "Catégories d'usagers": "Categorías de usuarios",
        "Nouvelle catégorie": "Nueva categoría",
        "Aucune catégorie d'usager.": "Ninguna categoría de usuario.",
        "Prêts max": "Préstamos máx.",
        "Durée de prêt": "Duración del préstamo",
        "%(n)s j": "%(n)s d",
        "Usagers": "Usuarios",
        _FEE_HINT: (
            "La cuota se factura automáticamente al inscribirse y en cada "
            "renovación de tarjeta. Un importe de 0 no emite factura."
        ),
        "Nouvelle catégorie d'usager": "Nueva categoría de usuario",
        "Modifier la catégorie d'usager": "Editar la categoría de usuario",
        "Modifier la catégorie": "Editar la categoría",
        "Nom (français)": "Nombre (francés)",
        "Nom (anglais)": "Nombre (inglés)",
        "Nom (espagnol)": "Nombre (español)",
        "Nom (malgache)": "Nombre (malgache)",
        "Types de documents autorisés": "Tipos de documento permitidos",
        "Aucun coché = tous les types sont autorisés.": (
            "Ninguno marcado = todos los tipos están permitidos."
        ),
        "Court, sans espace : ADULTE, ENFANT…": (
            "Corto, sin espacios: ADULTO, NIÑO…"
        ),
        "Nom affiché si les autres traductions manquent.": (
            "Nombre mostrado si faltan las otras traducciones."
        ),
        _FEE_HELP: (
            "0 = gratuito: ninguna factura al inscribirse ni al renovar."
        ),
        "Validité de la carte (mois)": "Validez de la tarjeta (meses)",
        "Prêts simultanés maximum": "Préstamos simultáneos máximos",
        "Durée de prêt (jours)": "Duración del préstamo (días)",
        _CODE_ERR: (
            "Solo letras, cifras, guion y guion bajo, sin espacios."
        ),
        "Le montant ne peut pas être négatif.": (
            "El importe no puede ser negativo."
        ),
        "Catégorie d'usager créée.": "Categoría de usuario creada.",
        "Catégorie d'usager mise à jour.": "Categoría de usuario actualizada.",
        "Catégorie d'usager supprimée.": "Categoría de usuario eliminada.",
        "Supprimer la catégorie d'usager": "Eliminar la categoría de usuario",
        "Cette catégorie n'a aucun usager : elle peut être supprimée.": (
            "Esta categoría no tiene usuarios: se puede eliminar."
        ),
        _PROTECT: (
            "La ficha de un usuario está ligada a su categoría: eliminarla "
            "rompería esas fichas."
        ),
        "Retour": "Volver",
        "Changement de catégorie : cotisation recalculée.": (
            "Cambio de categoría: cuota recalculada."
        ),
        "Changement de catégorie : plus de cotisation.": (
            "Cambio de categoría: ya no hay cuota."
        ),
        "Cotisation recalculée : facture %(old)s annulée, %(new)s émise (%(amount)s).": (
            "Cuota recalculada: factura %(old)s anulada, %(new)s emitida (%(amount)s)."
        ),
        "Facture de cotisation %(num)s annulée : la nouvelle catégorie n'en a pas.": (
            "Factura de cuota %(num)s anulada: la nueva categoría no tiene."
        ),
        "Email non configuré": "Correo no configurado",
        "L'envoi par email n'est pas configuré. Renseignez le serveur SMTP dans Avancé → Paramètres → Email, puis renvoyez.": (
            "El envío por correo no está configurado. Indique el servidor SMTP "
            "en Avanzado → Ajustes → Email y vuelva a enviar."
        ),
        "L'envoi par email n'est pas configuré (Avancé → Paramètres → Email).": (
            "El envío por correo no está configurado (Avanzado → Ajustes → Email)."
        ),
        "Les emails en attente partent tout de suite.": (
            "Los correos en espera se envían de inmediato."
        ),
        "Ils peuvent partir maintenant.": "Ya pueden enviarse.",
        "Imprimer la carte (62 mm)": "Imprimir la tarjeta (62 mm)",
        "La Box n'est pas en ligne : les emails restent en file jusqu'à ce qu'elle le soit. En attendant, prévenez les personnes par téléphone (liste ci-dessus).": (
            "La Box no está en línea: los correos quedan en cola hasta que lo esté. "
            "Mientras tanto, avise a las personas por teléfono (lista de arriba)."
        ),
        "La Box n'est pas en ligne : prévenez les personnes par téléphone, ou renvoyez quand elle le sera.": (
            "La Box no está en línea: avise por teléfono, o vuelva a enviar cuando lo esté."
        ),
        "La Box n'est pas en ligne. Prévenez les personnes par téléphone, ou renvoyez quand elle le sera.": (
            "La Box no está en línea. Avise por teléfono, o vuelva a enviar cuando lo esté."
        ),
    },
    "mg": {
        "Tarifs et Catégories d'usagers": (
            "Sarany sy sokajin'ny mpampiasa"
        ),
        _SUBTITLE: (
            "Sokajin'ny mpampiasa (saram-pikambanana, fampindramana, "
            "faharetan'ny karatra) ary sandan-bola atolotra ho an'ny hetsika "
            "sy ny lamandy."
        ),
        _ADVANCED_SUB: (
            "Sokajin'ny mpampiasa, saram-pikambanana, sandan-bola atolotra "
            "ho an'ny hetsika sy ny lamandy."
        ),
        "Catégories d'usagers": "Sokajin'ny mpampiasa",
        "Nouvelle catégorie": "Sokajy vaovao",
        "Aucune catégorie d'usager.": "Tsy misy sokajin'ny mpampiasa.",
        "Prêts max": "Fampindramana farany",
        "Durée de prêt": "Faharetan'ny fampindramana",
        "%(n)s j": "Andro %(n)s",
        "Usagers": "Mpampiasa",
        _FEE_HINT: (
            "Fakturaina mandeha ho azy ny saram-pikambanana rehefa misoratra "
            "anarana sy isaky ny fanavaozana ny karatra. Tsy mamoaka faktiora "
            "ny sandan-bola 0."
        ),
        "Nouvelle catégorie d'usager": "Sokajin'ny mpampiasa vaovao",
        "Modifier la catégorie d'usager": "Hanova ny sokajin'ny mpampiasa",
        "Modifier la catégorie": "Hanova ny sokajy",
        "Nom (français)": "Anarana (frantsay)",
        "Nom (anglais)": "Anarana (anglisy)",
        "Nom (espagnol)": "Anarana (espaniola)",
        "Nom (malgache)": "Anarana (malagasy)",
        "Types de documents autorisés": "Karazan-tahirin-kevitra azo atao",
        "Aucun coché = tous les types sont autorisés.": (
            "Tsy misy voamarika = azo atao ny karazany rehetra."
        ),
        "Court, sans espace : ADULTE, ENFANT…": (
            "Fohy, tsy misy elanelana: ADULTE, ENFANT…"
        ),
        "Nom affiché si les autres traductions manquent.": (
            "Anarana aseho raha tsy misy ny dikanteny hafa."
        ),
        _FEE_HELP: (
            "0 = maimaim-poana: tsy misy faktiora amin'ny fisoratana anarana "
            "na ny fanavaozana."
        ),
        "Validité de la carte (mois)": "Faharetan'ny karatra (volana)",
        "Prêts simultanés maximum": "Fampindramana miaraka farany",
        "Durée de prêt (jours)": "Faharetan'ny fampindramana (andro)",
        _CODE_ERR: (
            "Litera, isa, tsipika ary tsipika ambany ihany, tsy misy elanelana."
        ),
        "Le montant ne peut pas être négatif.": (
            "Tsy azo atao ratsy ny sandan-bola."
        ),
        "Catégorie d'usager créée.": "Voforona ny sokajin'ny mpampiasa.",
        "Catégorie d'usager mise à jour.": "Nohavaozina ny sokajin'ny mpampiasa.",
        "Catégorie d'usager supprimée.": "Voafafa ny sokajin'ny mpampiasa.",
        "Supprimer la catégorie d'usager": "Fafana ny sokajin'ny mpampiasa",
        "Cette catégorie n'a aucun usager : elle peut être supprimée.": (
            "Tsy misy mpampiasa io sokajy io: azo fafana izy."
        ),
        _PROTECT: (
            "Mifamatotra amin'ny sokajiny ny taratasin'ny mpampiasa: ny "
            "famafana azy dia hanimba ireo taratasy ireo."
        ),
        "Retour": "Hiverina",
        "Changement de catégorie : cotisation recalculée.": (
            "Fiovana sokajy: saram-pikambanana namboarina indray."
        ),
        "Changement de catégorie : plus de cotisation.": (
            "Fiovana sokajy: tsy misy saram-pikambanana intsony."
        ),
        "Cotisation recalculée : facture %(old)s annulée, %(new)s émise (%(amount)s).": (
            "Saram-pikambanana namboarina: faktiora %(old)s nofoanana, %(new)s navoaka (%(amount)s)."
        ),
        "Facture de cotisation %(num)s annulée : la nouvelle catégorie n'en a pas.": (
            "Faktiora saram-pikambanana %(num)s nofoanana: tsy manana izany ny sokajy vaovao."
        ),
        "Email non configuré": "Tsy voaamboatra ny mailaka",
        "L'envoi par email n'est pas configuré. Renseignez le serveur SMTP dans Avancé → Paramètres → Email, puis renvoyez.": (
            "Tsy voaamboatra ny fandefasana mailaka. Fenoy ny mpizara SMTP ao amin'ny "
            "Mandroso → Paramètre → Mailaka, dia alefaso indray."
        ),
        "L'envoi par email n'est pas configuré (Avancé → Paramètres → Email).": (
            "Tsy voaamboatra ny fandefasana mailaka (Mandroso → Paramètre → Mailaka)."
        ),
        "Les emails en attente partent tout de suite.": (
            "Mandalo avy hatrany ny mailaka miandry."
        ),
        "Ils peuvent partir maintenant.": "Afaka mandeha izy ireo izao.",
        "Imprimer la carte (62 mm)": "Atontay ny karatra (62 mm)",
        "La Box n'est pas en ligne : les emails restent en file jusqu'à ce qu'elle le soit. En attendant, prévenez les personnes par téléphone (liste ci-dessus).": (
            "Tsy an-tserasera ny Box: mijanona ao amin'ny filaharana ny mailaka. "
            "Ampahafantaro an-telefaonina ny olona (lisitra etsy ambony)."
        ),
        "La Box n'est pas en ligne : prévenez les personnes par téléphone, ou renvoyez quand elle le sera.": (
            "Tsy an-tserasera ny Box: ampahafantaro an-telefaonina, na alefaso indray rehefa miverina."
        ),
        "La Box n'est pas en ligne. Prévenez les personnes par téléphone, ou renvoyez quand elle le sera.": (
            "Tsy an-tserasera ny Box. Ampahafantaro an-telefaonina, na alefaso indray rehefa miverina."
        ),
    },
}


PLURALS: dict[str, dict[str, tuple[str, str]]] = {
    "en": {
        "%(counter)s usager est encore dans cette catégorie. Réaffectez-le avant de supprimer.": (
            "%(counter)s member is still in this category. Reassign them before deleting.",
            "%(counter)s members are still in this category. Reassign them before deleting.",
        ),
        "Impossible de supprimer : %(n)s usager est encore dans cette catégorie.": (
            "Cannot delete: %(n)s member is still in this category.",
            "Cannot delete: %(n)s members are still in this category.",
        ),
        "%(n)s email envoyé.": (
            "%(n)s email sent.",
            "%(n)s emails sent.",
        ),
        "%(n)s échec d'envoi.": (
            "%(n)s send failure.",
            "%(n)s send failures.",
        ),
        "%(n)s email reste en file : l'envoi n'est pas configuré (Avancé → Paramètres → Email).": (
            "%(n)s email is still queued: sending is not configured (Advanced → Settings → Email).",
            "%(n)s emails are still queued: sending is not configured (Advanced → Settings → Email).",
        ),
        "%(n)s email reste en file : la Box n'est pas en ligne. Prévenez la personne par téléphone, ou renvoyez quand la Box le sera.": (
            "%(n)s email is still queued: the Box is offline. Notify them by phone, or send again when the Box is back.",
            "%(n)s emails are still queued: the Box is offline. Notify people by phone, or send again when the Box is back.",
        ),
        "%(n)s email laissé en file.": (
            "%(n)s email left in the queue.",
            "%(n)s emails left in the queue.",
        ),
    },
    "es": {
        "%(counter)s usager est encore dans cette catégorie. Réaffectez-le avant de supprimer.": (
            "%(counter)s usuario sigue en esta categoría. Reasígnelo antes de eliminar.",
            "%(counter)s usuarios siguen en esta categoría. Reasígnelos antes de eliminar.",
        ),
        "Impossible de supprimer : %(n)s usager est encore dans cette catégorie.": (
            "No se puede eliminar: %(n)s usuario sigue en esta categoría.",
            "No se puede eliminar: %(n)s usuarios siguen en esta categoría.",
        ),
        "%(n)s email envoyé.": (
            "%(n)s correo enviado.",
            "%(n)s correos enviados.",
        ),
        "%(n)s échec d'envoi.": (
            "%(n)s envío fallido.",
            "%(n)s envíos fallidos.",
        ),
        "%(n)s email reste en file : l'envoi n'est pas configuré (Avancé → Paramètres → Email).": (
            "%(n)s correo sigue en cola: el envío no está configurado (Avanzado → Ajustes → Email).",
            "%(n)s correos siguen en cola: el envío no está configurado (Avanzado → Ajustes → Email).",
        ),
        "%(n)s email reste en file : la Box n'est pas en ligne. Prévenez la personne par téléphone, ou renvoyez quand la Box le sera.": (
            "%(n)s correo sigue en cola: la Box no está en línea. Avise por teléfono, o vuelva a enviar cuando la Box lo esté.",
            "%(n)s correos siguen en cola: la Box no está en línea. Avise por teléfono, o vuelva a enviar cuando la Box lo esté.",
        ),
        "%(n)s email laissé en file.": (
            "%(n)s correo dejado en cola.",
            "%(n)s correos dejados en cola.",
        ),
    },
    "mg": {
        "%(counter)s usager est encore dans cette catégorie. Réaffectez-le avant de supprimer.": (
            "Mbola ao amin'ity sokajy ity ny mpampiasa %(counter)s. Alefaso aloha alohan'ny hamafana.",
            "Mbola ao amin'ity sokajy ity ny mpampiasa %(counter)s. Alefaso aloha alohan'ny hamafana.",
        ),
        "Impossible de supprimer : %(n)s usager est encore dans cette catégorie.": (
            "Tsy azo fafana: mbola ao amin'ity sokajy ity ny mpampiasa %(n)s.",
            "Tsy azo fafana: mbola ao amin'ity sokajy ity ny mpampiasa %(n)s.",
        ),
        "%(n)s email envoyé.": (
            "Mailaka %(n)s no nalefa.",
            "Mailaka %(n)s no nalefa.",
        ),
        "%(n)s échec d'envoi.": (
            "Tsy nahomby ny fandefasana %(n)s.",
            "Tsy nahomby ny fandefasana %(n)s.",
        ),
        "%(n)s email reste en file : l'envoi n'est pas configuré (Avancé → Paramètres → Email).": (
            "Mailaka %(n)s mbola ao amin'ny filaharana: tsy voaamboatra ny fandefasana (Mandroso → Paramètre → Mailaka).",
            "Mailaka %(n)s mbola ao amin'ny filaharana: tsy voaamboatra ny fandefasana (Mandroso → Paramètre → Mailaka).",
        ),
        "%(n)s email reste en file : la Box n'est pas en ligne. Prévenez la personne par téléphone, ou renvoyez quand la Box le sera.": (
            "Mailaka %(n)s mbola ao amin'ny filaharana: tsy an-tserasera ny Box. Ampahafantaro an-telefaonina, na alefaso indray.",
            "Mailaka %(n)s mbola ao amin'ny filaharana: tsy an-tserasera ny Box. Ampahafantaro an-telefaonina, na alefaso indray.",
        ),
        "%(n)s email laissé en file.": (
            "Mailaka %(n)s navelana ao amin'ny filaharana.",
            "Mailaka %(n)s navelana ao amin'ny filaharana.",
        ),
    },
}


def _unescape(value: str) -> str:
    return value.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _read_value(lines: list[str], start: int, keyword: str) -> tuple[str, int]:
    first = lines[start][len(keyword):].strip()
    parts = [_unescape(first.strip('"'))]
    i = start + 1
    while i < len(lines) and lines[i].startswith('"'):
        parts.append(_unescape(lines[i].strip().strip('"')))
        i += 1
    return "".join(parts), i


def _clean_comments(block: list[str]) -> list[str]:
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
    po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"
    if not po_path.exists():
        return 0, 0
    singles = TRANSLATIONS.get(lang, {})
    plurals = PLURALS.get(lang, {})
    lines = po_path.read_text(encoding="utf-8").splitlines()

    out: list[str] = []
    pending: list[str] = []
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
