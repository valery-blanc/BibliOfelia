# FEAT-032 — Gestion des emplacements (UI librarian + API)

**Status :** DONE
**Date :** 2026-05-24
**Sprint :** 10
**Spec parent :** `SPEC_BIBLIOFELIA.md` §6.1 (catalogue) + §6.10 (API OfeliaScan)

---

## Contexte

Le modèle `catalog.Location` (code, description, parent FK self) existe depuis
FEAT-002 (Sprint 1). Le champ `Item.location` est un FK SET_NULL vers
`Location`. Côté API, OfeliaScan envoie déjà un `location_code` dans chaque
`ScanItem` (catalogage) et un `scope_location_code` dans la création de session
de récolement. Le code envoyé est résolu par `_resolve_location` (`apps/api/
services.py:44`) qui fait un `filter(code=…).first()` — si inconnu, retourne
`None`, l'exemplaire est créé **sans emplacement** silencieusement.

**Problème actuel :** aucune UI librarian ne permet de créer/modifier/supprimer
des `Location`. Seul `/admin/catalog/location/` est disponible — réservé au
superadmin et au debug Claude (cf. mémoire `feedback_admin_django_scope`).
Conséquence : un bibliothécaire ne peut pas définir ses propres emplacements,
et OfeliaScan ne peut pas non plus proposer de picker de codes valides
(pas d'endpoint API de listing).

Décisions validées par Val (2026-05-24) :
- Nouvelle page librarian sous **Avancé → Inventaire** (pas dans Administration).
- Pas d'auto-création de Location côté API : si OfeliaScan envoie un code
  inconnu, l'exemplaire est créé sans emplacement (comportement actuel
  préservé — affiché `-------` dans l'UI).
- Pas de validation 400 côté API pour les codes inconnus : tolérance.
- Pas d'arbo visuelle des `parent` dans l'UI v1 (champ exposé en simple select).

---

## Comportement

### 1. UI librarian — page « Emplacements »

Nouvelle carte ajoutée dans `templates/core/advanced.html`, **section
Inventaire** (`{% if user.is_librarian %}` … `{# ── Inventaire ── #}`), juste
sous « Sessions d'inventaire ». Style olive identique aux autres entrées de la
section. Icône `map-pin`.

```
[map-pin]  Emplacements
           Définir les zones de rangement (Salle adulte, Réserve, A1…).
           Utilisé au catalogage et au récolement.
```

### 2. Routes

- `GET  /catalog/locations/`              → `location_list`   (librarian)
- `GET  /catalog/locations/new/`          → `location_create` (librarian, GET form)
- `POST /catalog/locations/new/`          → `location_create` (librarian, POST submit)
- `GET  /catalog/locations/<pk>/edit/`    → `location_edit`   (librarian, GET form)
- `POST /catalog/locations/<pk>/edit/`    → `location_edit`   (librarian, POST submit)
- `GET  /catalog/locations/<pk>/delete/`  → confirmation page (librarian)
- `POST /catalog/locations/<pk>/delete/`  → suppression       (librarian)

Routes déclarées dans `apps/catalog/urls.py` (déjà l'app où vit `Location`).
Namespace : `catalog:location_list`, `catalog:location_create`,
`catalog:location_edit`, `catalog:location_delete`.

Implémentation : function-based views (cohérent avec le reste de
`apps/catalog/views.py`), pas de CBV.

### 3. Liste — `LocationListView`

Template `templates/catalog/location_list.html`. Inspiration design :
`templates/accounts/user_list.html` (registre liste-admin légère, sobre).

Colonnes :
- **Code** (lien vers édition)
- **Description** (tronquée à 80 caractères)
- **Parent** (code du parent ou `—`)
- **Exemplaires** (compteur `items.count()`)
- **Actions** : Modifier / Supprimer

Header : titre `Emplacements`, bouton primaire `+ Nouvel emplacement`.
Tile strip actif sur `advanced`.

### 4. Formulaire — `LocationCreateView` / `LocationUpdateView`

Template `templates/catalog/location_form.html`. Inspiration :
`templates/accounts/user_form.html` via `partials/_field.html`.

Champs :
- **code** (required, max 20, label `Code`, help-hint `Court, sans espace : A1, JEU-BD, RES…`)
- **description** (optional, textarea 3 lignes, label `Description`)
- **parent** (optional, select de toutes les autres Location, label `Parent (optionnel)`,
  help-hint `Sous-emplacement de…`)

Validation : `code` unique avec `parent` (contrainte modèle déjà en place
`location_code_parent_unique`).

Boutons : `Enregistrer` (primaire) / `Annuler` (lien retour liste).

### 5. Suppression

Template `templates/catalog/location_confirm_delete.html`. Page de
confirmation avec :
- Récapitulatif : code, description, nombre d'exemplaires concernés
- Message : « La suppression libère les N exemplaires rattachés (ils n'auront
  plus d'emplacement). Les sessions de récolement passées qui ciblaient cet
  emplacement conservent leur historique. »
- Bouton `Supprimer définitivement` (danger) / `Annuler`

Comportement : `on_delete=SET_NULL` côté `Item.location` et
`InventorySession.scope_location` → la suppression libère les FK, ne casse
rien. Pas de garde-fou particulier.

### 6. Endpoint API — `GET /api/locations/`

Nouveau view dans `apps/api/views.py` : `LocationListView` (APIView, GET).
Auth Bearer (compte scanner OfeliaScan, comme les autres endpoints scan).
Throttle scope `scan`.

Réponse :

```json
{
  "locations": [
    {"code": "A1", "description": "Salle adulte rayon 1", "parent_code": null},
    {"code": "JEU", "description": "Coin jeunesse", "parent_code": null},
    {"code": "JEU-BD", "description": "BD jeunesse", "parent_code": "JEU"}
  ]
}
```

Ordre : par `code` croissant. Pas de pagination (fonds < 100 emplacements
attendus).

Route : `path("locations", LocationListView.as_view(), name="locations")`
dans `apps/api/urls.py` (pas de slash final, cohérent avec les autres
endpoints OfeliaScan).

### 7. Comportement OfeliaScan inchangé

`_resolve_location` (`apps/api/services.py:44`) reste tel quel :

```python
def _resolve_location(code: str) -> Location | None:
    if not code:
        return None
    return Location.objects.filter(code=code).first()
```

Si code inconnu → `Item.location = None` → affiché `-------` dans
`/catalog/<record>/`. Pas de log, pas d'erreur, pas de 400 côté API.
OfeliaScan est responsable de proposer un picker avec les codes valides
via `GET /api/locations/`.

---

## Spec technique

### Vues (apps/catalog/views.py)

Function-based views décorées `@require_role(*WRITE_ROLES)` (librarian +
superadmin), cohérent avec le pattern existant du module :

- `location_list(request)` : queryset annoté `Count('items')`, ordre `code`.
- `location_create(request)` : `LocationForm`, redirect liste en succès.
- `location_edit(request, pk)` : idem en mode update.
- `location_delete(request, pk)` : GET = confirm page (compteur items + enfants),
  POST = suppression. SET_NULL côté `Item.location` et
  `InventorySession.scope_location` (FK existantes) libère proprement.

### Form (apps/catalog/forms.py)

`LocationForm(forms.ModelForm)` :
- Fields `["code", "description", "parent"]`, description en textarea 3 lignes.
- `__init__` : exclut `self.instance` du queryset `parent` (impossible
  d'être son propre parent depuis l'UI).
- `clean()` : vérifie l'unicité `(code, parent)` (en plus de la contrainte DB,
  pour afficher une erreur form lisible plutôt qu'IntegrityError) + garde-fou
  parent == self.

### API (apps/api/views.py + apps/api/serializers.py)

```python
class LocationSerializer(serializers.ModelSerializer):
    parent_code = serializers.SerializerMethodField()

    class Meta:
        model = Location
        fields = ["code", "description", "parent_code"]

    def get_parent_code(self, obj):
        return obj.parent.code if obj.parent else None


class LocationListView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "scan"

    def get(self, request):
        qs = Location.objects.select_related("parent").order_by("code")
        return Response({"locations": LocationSerializer(qs, many=True).data})
```

### Migrations

Aucune. Modèle inchangé.

---

## Tests

### `apps/catalog/tests/test_locations.py`

- Création d'une Location (POST `/locations/new/`) → 302 + objet en base
- Édition d'une Location existante
- Suppression : libère les `Item.location` (vérifier que les exemplaires
  rattachés ont `location=None` après suppression)
- Validation : `code` unique avec `parent` → 200 + erreur form sur duplicate
- Validation : `parent = self` → 200 + erreur form
- Permissions : 302 redirect login pour anonyme, 403 pour member-only

### `apps/api/tests/test_locations_api.py`

- `GET /api/locations/` retourne la liste triée par code
- Auth Bearer requise (401 sans token)
- `parent_code` est bien le code du parent ou `null`
- Throttle scope `scan` appliqué

---

## Impact sur l'existant

- `templates/core/advanced.html` : +1 carte dans la section Inventaire.
- `apps/catalog/urls.py` : +6 routes.
- `apps/catalog/views.py` : +4 vues CBV.
- `apps/catalog/forms.py` : +1 form (créer le fichier si absent).
- `apps/api/urls.py` : +1 route.
- `apps/api/views.py` + `apps/api/serializers.py` : +1 vue + 1 serializer.
- 3 templates HTML : `location_list.html`, `location_form.html`,
  `location_confirm_delete.html`.
- 2 fichiers de tests.
- `SPEC_BIBLIOFELIA.md` : §6.1 (paragraphe « Gestion des emplacements ») +
  §6.10 (endpoint `GET /api/locations/`).

Pas de migration. Pas de changement de schéma.

---

## Hors scope

- Arbo visuelle des locations parent/enfant (tree view).
- Réassignation en masse d'exemplaires d'une location vers une autre.
- Endpoint API d'écriture sur les locations (POST/PUT/DELETE) — OfeliaScan ne
  doit pas créer de Location.
- Validation 400 côté API d'envoi si `location_code` inconnu : on garde le
  comportement silencieux actuel.

Note : la réassignation au récolement est traitée séparément dans **FEAT-033**.
