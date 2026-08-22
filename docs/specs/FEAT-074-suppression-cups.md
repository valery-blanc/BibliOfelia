# FEAT-074 — Suppression du chemin d'impression CUPS

- **Statut** : DONE
- **Sprint** : 29
- **Demandé par** : Val (2026-08-22)
- **Sections spec impactées** : §2.1, §6.7, §11.3, §12 (risques)

## Contexte

L'écran **Étiquettes codes Ofelia** portait un bouton « **Imprimer (CUPS)** » qui
postait vers `printing:labels_send`. Ce bouton renvoyait systématiquement une page
**« Interdit (403) — La vérification CSRF a échoué »**.

Deux problèmes distincts, l'un cosmétique, l'autre de fond :

1. **Le 403** — le formulaire de la page est déclaré `method="get"` (il sert à
   ouvrir `labels.pdf`) et n'a donc pas de `{% csrf_token %}`. Le bouton CUPS
   forçait `formmethod="post"` sur ce même formulaire : Django recevait un POST
   sans jeton et le rejetait. **Le bouton n'a jamais pu fonctionner** depuis
   l'écran.
2. **L'architecture** — `submit_to_cups()` (FEAT-012, Sprint 4) suppose une
   imprimante visible **depuis le serveur**. Or :
   - l'étiqueteuse Brother QL-810W est branchée sur le **poste du bibliothécaire**,
     pas sur le serveur (déjà constaté en FEAT-062, Sprint 27) ;
   - le site est hébergé **hors de la bibliothèque** (chez Val ou sur un cloud),
     tandis que l'imprimante et le PC sont sur le **réseau local de la
     bibliothèque**, derrière son routeur. Un serveur distant ne peut pas
     atteindre une IP privée sur ce LAN.

Faire fonctionner CUPS supposerait donc soit d'exposer l'imprimante sur Internet
(exclu : ces imprimantes n'ont aucune authentification), soit un VPN permanent
par bibliothèque — un composant de plus à maintenir sur des sites sans
informaticien, contraire à l'exigence de robustesse du projet.

**Décision Val (2026-08-22)** : tout supprimer, plutôt que réparer le CSRF d'un
chemin qui ne servira jamais.

## Comportement retenu

Le chemin d'impression officiel et unique est le **PDF servi au navigateur** :

- **Générer PDF** — planche A4 (§6.7)
- **Ruban 62 mm (Brother QL)** — une étiquette par page, géométrie exacte du ruban
- **Étiquettes de tranche** — idem, cote de catégorie (FEAT-068)

Le poste client imprime ces PDF via son pilote Brother. Le réglage du format et
de l'orientation se fait **une fois pour toutes** dans les options d'impression
du pilote Windows (Paramètres → Bluetooth et appareils → Imprimantes et
scanners → QL-810W → Options d'impression), et non dans la fenêtre de propriétés
ouverte depuis le dialogue d'impression de Chrome, qui ne vaut que pour le job en
cours.

## Implémentation

Supprimé :

| Fichier | Suppression |
|---|---|
| `templates/printing/labels_picker.html` | bouton « Imprimer (CUPS) » |
| `apps/printing/views.py` | vue `labels_send()` |
| `apps/printing/urls.py` | route `printing:labels_send` (`labels/send/`) |
| `apps/printing/services.py` | `submit_to_cups()`, `PrintResult`, import `dataclass`, mention CUPS du docstring |
| `config/settings/base.py` | réglages `CUPS_HOST` / `CUPS_PORT` |
| `.env.example` | bloc `CUPS_HOST` / `CUPS_PORT` |
| `Dockerfile` | paquets `libcups2`, `libcups2-dev`, `pip install pycups==2.0.4` |
| `requirements.txt` | commentaire pycups |
| `apps/setup/forms.py` | `Step5PrinterForm` (« Activer l'impression CUPS », « Serveur CUPS ») |
| `apps/setup/views.py` | étape `step5` « Imprimante » du wizard |
| `apps/setup/services.py` | écriture du `Setting.printer_config` |

Modifié :

- `templates/core/advanced.html` — la description de l'écran d'étiquettes
  annonçait « PDF planche A4 ou envoi direct à l'imprimante CUPS » → « PDF
  planche A4 ou ruban 62 mm pour l'étiqueteuse Brother QL ».
- **Wizard renuméroté de 8 à 7 étapes** : l'étape « Imprimante » ne configurait
  que CUPS, la laisser aurait fait saisir des réglages sans effet. Les formulaires
  suivants sont décalés (`Step6BackupForm` → `Step5BackupForm`,
  `Step7ZerotierForm` → `Step6ZerotierForm`, `Step8DemoForm` → `Step7DemoForm`),
  ainsi que les clés de session (`step6..step8` → `step5..step7`). Les étapes
  obligatoires du `finalize` (`step2`, `step3`, `step4`) sont inchangées.

`gcc` est **conservé** dans le Dockerfile : il servait à compiler `pycups`, mais
il peut aussi servir à d'autres roues Python sans binaire précompilé sur ARM
(Raspberry Pi). Le retirer serait un pari sur le build de la Box, pour un gain
marginal.

## Impact

- **Aucune migration** — `printer_config` était un `Setting` JSON, plus lu par
  personne. Il subsiste sans effet sur les instances déjà installées (le wizard
  n'y repasse pas). Aucun code ne le lit désormais.
- **Aucune régression fonctionnelle** — le bouton supprimé renvoyait un 403 dans
  100 % des cas.
- **Image Docker allégée** — `libcups2-dev` et `pycups` en moins.

## Non retenu

- **Réparer le CSRF** : donnerait un bouton qui affiche « Imprimante
  indisponible » puis retombe sur le PDF, soit exactement ce que fait déjà
  « Générer PDF », en plus déroutant pour le bibliothécaire.
- **Agent d'impression local** (petit service sur le PC de la bibliothèque qui
  récupère les jobs et les envoie à l'imprimante avec les options figées) :
  techniquement propre, mais c'est un composant de plus à installer et dépanner à
  distance sur chaque site, pour remplacer un réglage Windows à faire une seule
  fois. À reconsidérer seulement si le réglage du pilote se révèle instable à
  l'usage.
