#!/usr/bin/env python3
"""Traductions Sprint 17 / FEAT-046 (catalogage caméra) — FR → EN/ES/MG.

Applique les traductions directement aux fichiers .po (stdlib, sans Docker).
- Gère les msgid mono- ET multi-lignes.
- **Overwrite + de-fuzzy** : pour tout msgid présent dans le dict, écrit le
  msgstr et retire le flag `fuzzy` (en préservant `python-format`). Indispensable
  car `makemessages` marque les nouvelles chaînes proches d'anciennes en
  `#, fuzzy` avec une traduction devinée → le gate `i18n_check.py` les rejette.
Rejoue : python scripts/translations_sprint19.py
"""
from __future__ import annotations

from pathlib import Path

TRANSLATIONS = {
    "en": {
        "Cataloguer en scannant": "Catalog by scanning",
        "Catalogage par scan": "Cataloging by scan",
        "Scanner les ISBN en rafale pour créer les notices et leurs exemplaires.":
            "Rapidly scan ISBNs to create records and their copies.",
        "Choisissez les valeurs par défaut du lot, puis scannez les livres en rafale.":
            "Pick the batch defaults, then scan books rapidly.",
        "Démarrer le catalogage": "Start cataloging",
        "Lots précédents": "Previous batches",
        "Lots": "Batches",
        "Lot de catalogage": "Cataloging batch",
        "Lots de catalogage": "Cataloging batches",
        "Nouveau lot": "New batch",
        "En cours": "In progress",
        "Validés": "Validated",
        "Continuer": "Continue",
        "Étiquettes": "Labels",
        "Aucun lot en cours.": "No batch in progress.",
        "Aucun lot validé.": "No validated batch.",
        "titre(s)": "title(s)",
        "titre(s) scanné(s)": "title(s) scanned",
        "Scannez en rafale les ISBN de vos livres pour les ajouter au catalogue.":
            "Rapidly scan your books’ ISBNs to add them to the catalog.",
        "Scanner des livres": "Scan books",
        "Saisir un ISBN à la main": "Enter an ISBN manually",
        "Saisissez l’ISBN à la main.": "Enter the ISBN manually.",
        "Ajouter": "Add",
        "Retirer": "Remove",
        "Enregistrer": "Save",
        "Envoyer au catalogue": "Send to catalog",
        "Aucun livre scanné pour l’instant. Lancez le scan ci-dessus.":
            "No book scanned yet. Start scanning above.",
        "Astuce : représentez un même livre après quelques secondes pour ajouter un 2ᵉ exemplaire.":
            "Tip: show the same book again after a few seconds to add a 2nd copy.",
        "Catégorie pour tout le lot": "Category for the whole batch",
        "Emplacement pour tout le lot": "Location for the whole batch",
        "Appliquer à toutes les lignes": "Apply to all rows",
        "Ex.": "Copies",
        "Ce lot a été envoyé au catalogue.": "This batch has been sent to the catalog.",
        "Imprimer les étiquettes de ce lot": "Print this batch’s labels",
        "Nom du lot (optionnel)": "Batch name (optional)",
        "Catégorie par défaut": "Default category",
        "Emplacement par défaut": "Default location",
        "Appliquée aux nouvelles notices ; modifiable ligne par ligne.":
            "Applied to new records; editable row by row.",
        "Appliqué aux nouveaux exemplaires ; modifiable ligne par ligne.":
            "Applied to new copies; editable row by row.",
        "Voir tous les exemplaires": "See all copies",
        # messages views.py
        "Lot de catalogage démarré.": "Cataloging batch started.",
        "ISBN %(isbn)s · %(lang)s": "ISBN %(isbn)s · %(lang)s",
        "%(rec)s notice(s) créée(s), %(match)s complétée(s), %(cop)s exemplaire(s) ajouté(s).":
            "%(rec)s record(s) created, %(match)s completed, %(cop)s copy(ies) added.",
        "Code refusé": "Code rejected",
        "Ce lot est déjà validé.": "This batch is already validated.",
        "Déjà catalogué": "Already cataloged",
        "Carte membre — pas un livre": "Member card — not a book",
        "Code invalide.": "Invalid code.",
        "exemplaire %(n)s": "copy %(n)s",
        "Ligne retirée.": "Row removed.",
        "Aucun livre scanné à envoyer.": "No scanned book to send.",
        "Modifications enregistrées.": "Changes saved.",
        "Étiquettes du lot de catalogage : <strong>%(session_label)s</strong>. Les exemplaires du lot sont pré-cochés.":
            "Labels for cataloging batch: <strong>%(session_label)s</strong>. The batch’s copies are pre-checked.",
        "Modifier les lignes cochées": "Edit checked rows",
        "(ne pas changer)": "(leave unchanged)",
        "Appliquer aux lignes cochées": "Apply to checked rows",
        "Cochez des lignes, choisissez les valeurs, puis appliquez.":
            "Check rows, pick values, then apply.",
        "Auteur / Titre": "Author / Title",
    },
    "es": {
        "Cataloguer en scannant": "Catalogar escaneando",
        "Catalogage par scan": "Catalogación por escaneo",
        "Scanner les ISBN en rafale pour créer les notices et leurs exemplaires.":
            "Escanear ISBN en ráfaga para crear las fichas y sus ejemplares.",
        "Choisissez les valeurs par défaut du lot, puis scannez les livres en rafale.":
            "Elija los valores por defecto del lote y luego escanee los libros en ráfaga.",
        "Démarrer le catalogage": "Iniciar la catalogación",
        "Lots précédents": "Lotes anteriores",
        "Lots": "Lotes",
        "Lot de catalogage": "Lote de catalogación",
        "Lots de catalogage": "Lotes de catalogación",
        "Nouveau lot": "Nuevo lote",
        "En cours": "En curso",
        "Validés": "Validados",
        "Continuer": "Continuar",
        "Étiquettes": "Etiquetas",
        "Aucun lot en cours.": "Ningún lote en curso.",
        "Aucun lot validé.": "Ningún lote validado.",
        "titre(s)": "título(s)",
        "titre(s) scanné(s)": "título(s) escaneado(s)",
        "Scannez en rafale les ISBN de vos livres pour les ajouter au catalogue.":
            "Escanee en ráfaga los ISBN de sus libros para añadirlos al catálogo.",
        "Scanner des livres": "Escanear libros",
        "Saisir un ISBN à la main": "Introducir un ISBN a mano",
        "Saisissez l’ISBN à la main.": "Introduzca el ISBN a mano.",
        "Ajouter": "Añadir",
        "Retirer": "Eliminar",
        "Enregistrer": "Guardar",
        "Envoyer au catalogue": "Enviar al catálogo",
        "Aucun livre scanné pour l’instant. Lancez le scan ci-dessus.":
            "Ningún libro escaneado por ahora. Inicie el escaneo arriba.",
        "Astuce : représentez un même livre après quelques secondes pour ajouter un 2ᵉ exemplaire.":
            "Consejo: vuelva a mostrar el mismo libro tras unos segundos para añadir un 2.º ejemplar.",
        "Catégorie pour tout le lot": "Categoría para todo el lote",
        "Emplacement pour tout le lot": "Ubicación para todo el lote",
        "Appliquer à toutes les lignes": "Aplicar a todas las filas",
        "Ex.": "Ejem.",
        "Ce lot a été envoyé au catalogue.": "Este lote se ha enviado al catálogo.",
        "Imprimer les étiquettes de ce lot": "Imprimir las etiquetas de este lote",
        "Nom du lot (optionnel)": "Nombre del lote (opcional)",
        "Catégorie par défaut": "Categoría por defecto",
        "Emplacement par défaut": "Ubicación por defecto",
        "Appliquée aux nouvelles notices ; modifiable ligne par ligne.":
            "Se aplica a las fichas nuevas; modificable fila por fila.",
        "Appliqué aux nouveaux exemplaires ; modifiable ligne par ligne.":
            "Se aplica a los ejemplares nuevos; modificable fila por fila.",
        "Voir tous les exemplaires": "Ver todos los ejemplares",
        "Lot de catalogage démarré.": "Lote de catalogación iniciado.",
        "ISBN %(isbn)s · %(lang)s": "ISBN %(isbn)s · %(lang)s",
        "%(rec)s notice(s) créée(s), %(match)s complétée(s), %(cop)s exemplaire(s) ajouté(s).":
            "%(rec)s ficha(s) creada(s), %(match)s completada(s), %(cop)s ejemplar(es) añadido(s).",
        "Code refusé": "Código rechazado",
        "Ce lot est déjà validé.": "Este lote ya está validado.",
        "Déjà catalogué": "Ya catalogado",
        "Carte membre — pas un livre": "Tarjeta de socio — no es un libro",
        "Code invalide.": "Código no válido.",
        "exemplaire %(n)s": "ejemplar %(n)s",
        "Ligne retirée.": "Fila eliminada.",
        "Aucun livre scanné à envoyer.": "Ningún libro escaneado para enviar.",
        "Modifications enregistrées.": "Cambios guardados.",
        "Étiquettes du lot de catalogage : <strong>%(session_label)s</strong>. Les exemplaires du lot sont pré-cochés.":
            "Etiquetas del lote de catalogación: <strong>%(session_label)s</strong>. Los ejemplares del lote están premarcados.",
        "Modifier les lignes cochées": "Modificar las filas marcadas",
        "(ne pas changer)": "(no cambiar)",
        "Appliquer aux lignes cochées": "Aplicar a las filas marcadas",
        "Cochez des lignes, choisissez les valeurs, puis appliquez.":
            "Marque filas, elija los valores y luego aplique.",
        "Auteur / Titre": "Autor / Título",
    },
    "mg": {
        "Cataloguer en scannant": "Mikatalaogy amin'ny scan",
        "Catalogage par scan": "Katalaogy amin'ny scan",
        "Scanner les ISBN en rafale pour créer les notices et leurs exemplaires.":
            "Scannevo haingana ny ISBN mba hamorona ireo notice sy ny kopiany.",
        "Choisissez les valeurs par défaut du lot, puis scannez les livres en rafale.":
            "Safidio ny sanda lasitra an'ny andiana, dia scannevo haingana ny boky.",
        "Démarrer le catalogage": "Atombohy ny katalaogy",
        "Lots précédents": "Andiana teo aloha",
        "Lots": "Andiana",
        "Lot de catalogage": "Andian-katalaogy",
        "Lots de catalogage": "Andiana katalaogy",
        "Nouveau lot": "Andiana vaovao",
        "En cours": "An-dalana",
        "Validés": "Voamarina",
        "Continuer": "Tohizo",
        "Étiquettes": "Etikety",
        "Aucun lot en cours.": "Tsy misy andiana an-dalana.",
        "Aucun lot validé.": "Tsy misy andiana voamarina.",
        "titre(s)": "lohateny",
        "titre(s) scanné(s)": "lohateny voa-scan",
        "Scannez en rafale les ISBN de vos livres pour les ajouter au catalogue.":
            "Scannevo haingana ny ISBN-n'ny bokinao mba hanampy azy ao amin'ny katalaogy.",
        "Scanner des livres": "Mi-scan boky",
        "Saisir un ISBN à la main": "Soraty an-tanana ny ISBN",
        "Saisissez l’ISBN à la main.": "Soraty an-tanana ny ISBN.",
        "Ajouter": "Hanampy",
        "Retirer": "Esory",
        "Enregistrer": "Tehirizo",
        "Envoyer au catalogue": "Alefa any amin'ny katalaogy",
        "Aucun livre scanné pour l’instant. Lancez le scan ci-dessus.":
            "Tsy misy boky voa-scan aloha. Atombohy ny scan eo ambony.",
        "Astuce : représentez un même livre après quelques secondes pour ajouter un 2ᵉ exemplaire.":
            "Torohevitra: asehoy indray ilay boky aorian'ny segondra vitsivitsy mba hanampy kopia faha-2.",
        "Catégorie pour tout le lot": "Sokajy ho an'ny andiana manontolo",
        "Emplacement pour tout le lot": "Toerana ho an'ny andiana manontolo",
        "Appliquer à toutes les lignes": "Ampiharo amin'ny andalana rehetra",
        "Ex.": "Kopia",
        "Ce lot a été envoyé au catalogue.": "Nalefa tany amin'ny katalaogy ity andiana ity.",
        "Imprimer les étiquettes de ce lot": "Atontay ny etikety amin'ity andiana ity",
        "Nom du lot (optionnel)": "Anaran'ny andiana (tsy voatery)",
        "Catégorie par défaut": "Sokajy lasitra",
        "Emplacement par défaut": "Toerana lasitra",
        "Appliquée aux nouvelles notices ; modifiable ligne par ligne.":
            "Ampiharina amin'ny notice vaovao; azo ovaina isaky ny andalana.",
        "Appliqué aux nouveaux exemplaires ; modifiable ligne par ligne.":
            "Ampiharina amin'ny kopia vaovao; azo ovaina isaky ny andalana.",
        "Voir tous les exemplaires": "Hijery ny kopia rehetra",
        "Lot de catalogage démarré.": "Nanomboka ny andian-katalaogy.",
        "ISBN %(isbn)s · %(lang)s": "ISBN %(isbn)s · %(lang)s",
        "%(rec)s notice(s) créée(s), %(match)s complétée(s), %(cop)s exemplaire(s) ajouté(s).":
            "%(rec)s notice noforonina, %(match)s nofenoina, %(cop)s kopia nampiana.",
        "Code refusé": "Kaody nolavina",
        "Ce lot est déjà validé.": "Efa voamarina ity andiana ity.",
        "Déjà catalogué": "Efa voakatalaogy",
        "Carte membre — pas un livre": "Karatra mpikambana — tsy boky",
        "Code invalide.": "Kaody tsy mety.",
        "exemplaire %(n)s": "kopia %(n)s",
        "Ligne retirée.": "Voaesotra ny andalana.",
        "Aucun livre scanné à envoyer.": "Tsy misy boky voa-scan halefa.",
        "Modifications enregistrées.": "Voatahiry ny fanovana.",
        "Étiquettes du lot de catalogage : <strong>%(session_label)s</strong>. Les exemplaires du lot sont pré-cochés.":
            "Etikety an'ny andian-katalaogy: <strong>%(session_label)s</strong>. Voamariky mialoha ireo kopian'ny andiana.",
        "Modifier les lignes cochées": "Hanova ny andalana voamarika",
        "(ne pas changer)": "(aza ovaina)",
        "Appliquer aux lignes cochées": "Ampiharo amin'ny andalana voamarika",
        "Cochez des lignes, choisissez les valeurs, puis appliquez.":
            "Mariho ny andalana, safidio ny sanda, dia ampiharo.",
        "Auteur / Titre": "Mpanoratra / Lohateny",
    },
}

LOCALE_DIR = Path(__file__).resolve().parent.parent / "locale"


def _po_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace('"', '\\"')


def _unescape(s: str) -> str:
    return s.replace('\\"', '"').replace("\\\\", "\\")


def _defuzz(comment: str) -> str | None:
    """Retire le flag `fuzzy` d'une ligne `#, ...`. Retourne None si la ligne
    ne contenait que `fuzzy` (à supprimer), sinon la ligne nettoyée."""
    if not comment.startswith("#,"):
        return comment
    flags = [f.strip() for f in comment[2:].split(",") if f.strip()]
    flags = [f for f in flags if f != "fuzzy"]
    return ("#, " + ", ".join(flags)) if flags else None


def _strip_trailing_fuzzy(out: list[str]) -> None:
    """De-fuzzy le bloc de commentaires déjà émis juste avant un msgid."""
    k = len(out) - 1
    while k >= 0 and out[k].startswith("#"):
        k -= 1
    block = out[k + 1:]
    if not block:
        return
    new: list[str] = []
    for c in block:
        if c.startswith("#|"):  # ancien msgid (previous) — cosmétique, on jette
            continue
        d = _defuzz(c)
        if d is not None:
            new.append(d)
    out[k + 1:] = new


def apply_lang(lang: str, mapping: dict[str, str]) -> int:
    po_path = LOCALE_DIR / lang / "LC_MESSAGES" / "django.po"
    if not po_path.exists():
        return 0
    lines = po_path.read_text(encoding="utf-8").splitlines(keepends=False)
    out: list[str] = []
    count = 0
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        # Tout msgid (précédé ou non d'un bloc de commentaires) ; on saute les
        # entrées plurielles (gérées à la main dans les .po).
        if line.startswith("msgid ") and not (
            i + 1 < n and lines[i + 1].startswith("msgid_plural")
        ):
            parts = [_unescape(line[len("msgid "):].strip().strip('"'))]
            j = i + 1
            while j < n and lines[j].startswith('"'):
                parts.append(_unescape(lines[j].strip().strip('"')))
                j += 1
            msgid = "".join(parts)
            if msgid in mapping and mapping[msgid]:
                _strip_trailing_fuzzy(out)
                m = j + 1  # j = ligne msgstr, saute ses continuations
                while m < n and lines[m].startswith('"'):
                    m += 1
                out.extend(lines[i:j])
                out.append(f'msgstr "{_po_escape(mapping[msgid])}"')
                count += 1
                i = m
                continue
        out.append(line)
        i += 1
    po_path.write_text("\n".join(out) + "\n", encoding="utf-8")
    return count


def main() -> None:
    for lang, mapping in TRANSLATIONS.items():
        print(f"[{lang}] {apply_lang(lang, mapping)} entrée(s) traitée(s)")


if __name__ == "__main__":
    main()
