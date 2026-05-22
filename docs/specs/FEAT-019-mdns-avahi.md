# FEAT-019 — Publication mDNS / DNS-SD (service Avahi)

Statut : **DONE — commande + tests (6 verts) ; test mDNS réel à faire sur la Pi** (2026-05-22)
Sprint : 3
Task : #19 de `docs/tasks/TASKS.md`
Spec : `SPEC_BIBLIOFELIA.md` §6.10 (Découverte mDNS / DNS-SD) / `SPEC-CORR-001` §7

## Contexte

OfeliaScan découvre la box sur le réseau local via mDNS : il recherche le
service DNS-SD `_bibliofelia._tcp.`. La box doit donc le publier. Le choix
d'architecture retenu (cf. discussion 2026-05-22) est de **publier via
`avahi-daemon` sur l'hôte Raspberry Pi**, et non dans le conteneur — pour la
robustesse : service géré par systemd, fichier statique insensible aux coupures
de courant, découplé de la santé du conteneur applicatif, sans conflit avec
l'avahi déjà présent sur l'hôte.

## Périmètre

### Commande `generate_avahi_service` (`apps/core/management/commands/`)

Génère le fichier de service Avahi `_bibliofelia._tcp.` à partir de l'état
courant de la box :

| Donnée         | Source                                  |
|----------------|-----------------------------------------|
| `box_name`     | `Setting` `box_name` (wizard §11.3)     |
| `library_name` | `Setting` `library_name` (wizard §11.3) |
| `version`      | réglage `BIBLIOFELIA_VERSION`           |
| `api_base`     | réglage `API_BASE_PATH`                 |
| port           | réglage `MDNS_SERVICE_PORT` (défaut 80) |

Options :
- sans argument : écrit dans `settings.AVAHI_SERVICE_PATH`
  (défaut `/etc/avahi/services/bibliofelia.service`) ;
- `--output PATH` : écrit ailleurs (tests, vérification) ;
- `--dry-run` : affiche le XML sans écrire de fichier.

Toutes les valeurs interpolées sont échappées pour le XML. La commande est
idempotente. En cas d'échec d'écriture (dossier non monté / non accessible),
elle lève une `CommandError` explicite.

Fichier produit :

```xml
<?xml version="1.0" standalone='no'?>
<!DOCTYPE service-group SYSTEM "avahi-service.dtd">
<service-group>
  <name>OfeliaBox-Tulear</name>
  <service>
    <type>_bibliofelia._tcp</type>
    <port>80</port>
    <txt-record>library_name=Bibliothèque de Tuléar</txt-record>
    <txt-record>version=0.1.0-dev</txt-record>
    <txt-record>api_base=/biblio/api/v1/</txt-record>
  </service>
</service-group>
```

### Réglages (`config/settings/base.py`)

- `AVAHI_SERVICE_PATH` (défaut `/etc/avahi/services/bibliofelia.service`).
- `MDNS_SERVICE_PORT` (défaut `80`) — port HTTP public de l'API derrière nginx.

## Déploiement — à appliquer en Task #18 (intégration keebee)

1. **`avahi-daemon` sur l'hôte Raspberry Pi** : présent et activé par défaut
   sur Raspberry Pi OS. Vérifier `systemctl is-enabled avahi-daemon`.
2. **Bind-mount** dans le `docker-compose.yml` de prod : monter le dossier
   `/etc/avahi/services/` de l'hôte dans le conteneur web, en écriture, pour
   que la commande y dépose `bibliofelia.service`. `avahi-daemon` surveille ce
   dossier et recharge automatiquement.

   ```yaml
   services:
     web:
       volumes:
         - /etc/avahi/services:/etc/avahi/services
   ```

3. Au premier déploiement, exécuter une fois
   `docker compose exec web python manage.py generate_avahi_service`
   pour que la box soit découvrable même avant le wizard.

## Dépendances

- **Régénération au wizard de premier démarrage (Task #15)** : le wizard, une
  fois le nom de la bibliothèque saisi, appellera
  `call_command("generate_avahi_service")` pour republier le service avec les
  vraies valeurs. Ce branchement est **en attente de Task #15** (Sprint 4) ; la
  commande, elle, est livrée et prête.

## Test

- **Unitaire** : `apps/core/tests/test_avahi.py` — 6 tests verts (type de
  service, port, TXT records, valeurs issues des `Setting`, échappement XML,
  commande `--dry-run` et `--output`).
- **mDNS réel** : la découverte effective par OfeliaScan ne peut être testée
  que sur la Pi (avahi hôte). Depuis Docker Desktop / Windows le multicast ne
  sort pas sur le LAN. Sur la machine de dev, seule la bonne forme du fichier
  est vérifiable (`generate_avahi_service --dry-run`).
