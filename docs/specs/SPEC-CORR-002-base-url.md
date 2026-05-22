# SPEC-CORR-002 — `/pairing/info` renvoie `base_url` (URL absolue)

Statut : **APPLIQUÉ** — intégré dans `SPEC_BIBLIOFELIA.md` §6.10 le 2026-05-22
Version : 1.0
Date : 2026-05-22
Cible : `SPEC_BIBLIOFELIA.md` §6.10 (Pairing) — amende `SPEC-CORR-001` §4.1
Auteur : OfeliaScan (client de l'API)

---

## 1. Problème constaté

`SPEC-CORR-001` §4.1 définissait le champ `api_base` de `GET /pairing/info`
comme un **chemin** (`"/biblio/api/v1/"`). Deux conséquences :

1. **Chemin imposé.** La box devait servir l'API exactement sous
   `/biblio/api/v1/`. Or la route nginx de l'UI BibliOfelia est `/bibliofelia/`
   (`/biblio/` étant le Koha de keebee) — conflit de routage.
2. **Désalignement de nom.** Le DTO de pairing d'OfeliaScan
   (`PairingInfoDto`) stocke le champ sous le nom **`base_url`**, pas
   `api_base`. Une réponse box avec `api_base` n'est pas trouvée par l'app →
   l'appairage automatique échoue et la saisie manuelle devient nécessaire.

## 2. Correction

`GET /pairing/info` renvoie le champ **`base_url`** (et non `api_base`) :

```json
{
  "box_name": "OfeliaBox-Tulear",
  "library_name": "Bibliothèque de Tuléar",
  "version": "1.4.0",
  "base_url": "http://192.168.0.147/bibliofelia/api/v1/"
}
```

| Champ      | Type   | Requis | Notes                                             |
|------------|--------|--------|---------------------------------------------------|
| `base_url` | string | oui    | **URL absolue complète** : scheme + host + chemin + slash final |

- `base_url` est une **URL absolue** (`http://<host>/<chemin>/`), slash final
  inclus. OfeliaScan la passe telle quelle à `BibliOfeliaApiFactory.forBaseUrl()`
  et l'utilise pour tous les appels suivants (il normalise le slash final si
  absent, mais le reste — scheme + host + chemin — doit être complet).
- La box n'a donc **plus à se conformer à un chemin imposé** : elle publie sa
  propre adresse réelle, et OfeliaScan s'y adapte sans recompilation.

## 3. Implémentation côté BibliOfelia

- `apps/api/views.py:PairingInfoView` : le champ `base_url` est **reconstruit
  depuis la requête entrante** (`request.build_absolute_uri`) — la box publie
  l'URL réellement utilisée par le client, quel que soit le préfixe.
- Réglage `API_BASE_URL` : si défini (URL absolue), il **force** la valeur de
  `base_url` ; utile lorsque nginx réécrit le chemin et que la reconstruction
  depuis la requête n'est pas fiable.
- Contrainte de déploiement (Task #18) : la conf nginx doit transmettre les
  en-têtes `Host` et `X-Forwarded-Proto`, sinon fixer `API_BASE_URL`.

## 4. Côté OfeliaScan

Aucune modification de code requise : `PairingInfoDto.base_url` et
`BibliOfeliaApiFactory.forBaseUrl()` attendent déjà ce format. La box devait
seulement publier le bon nom de champ et une URL absolue.

## 5. Note — enregistrement TXT mDNS

L'enregistrement TXT mDNS conserve le nom `api_base` (`SPEC-CORR-001` §7.2) : il
porte un *chemin*, pas une URL absolue, et n'est pas exploité par OfeliaScan v1.
`base_url` (URL absolue, via `/pairing/info`) reste la source faisant foi.
