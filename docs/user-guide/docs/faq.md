# Foire aux questions

## Sur la connexion et les comptes

### J'ai oublié mon mot de passe, que faire ?

BibliOfelia fonctionne hors ligne et n'envoie pas de courriel de
réinitialisation. Demandez à l'administrateur de la Box de
réinitialiser votre mot de passe directement depuis la console
d'administration.

### Mon compte est bloqué après plusieurs essais

C'est une protection contre les tentatives d'intrusion. Attendez
quelques minutes ou demandez à l'administrateur de débloquer le
compte.

## Sur les prêts et retours

### Un membre peut-il emprunter un livre déjà en prêt ?

Non. Mais il peut le **réserver** : dès que le livre revient, il sera
mis de côté pour lui. Voir [Créer une
réservation](reservations/creer.md).

### Combien de livres un membre peut-il emprunter en même temps ?

Cela dépend de la catégorie du membre. Par défaut : 5 pour un adulte,
3 pour un enfant. L'administrateur peut ajuster.

### Peut-on prêter à un membre dont la carte est expirée ?

Non. Renouvelez d'abord la carte (voir
[Renouvellement](usagers/renouvellement.md)), puis enregistrez le
prêt.

## Sur le catalogue

### Comment ajouter un livre rapidement ?

Si le livre a un ISBN, tapez-le dans le formulaire de nouvelle
notice : BibliOfelia interroge OpenLibrary et pré-remplit la fiche
automatiquement. Voir [Ajouter un livre](catalogue/ajouter-livre.md).

### Que faire si l'ISBN n'est pas trouvé ?

Saisissez les informations manuellement. C'est rare mais possible
pour les livres très récents ou très anciens.

### Comment réorganiser un rayon ?

Faites un récolement dans la nouvelle localisation : tous
les livres scannés seront automatiquement reclassés. Voir
[Récolement](inventaire/recolement.md).

## Sur les réservations

### Plusieurs membres peuvent-ils réserver le même livre ?

Oui. Ils sont placés dans une file d'attente : le premier réservé
sera servi en premier quand le livre revient.

### Comment savoir quand prévenir un membre ?

Le tableau de bord affiche en permanence un cadre **Notifications à
faire**. Voir
[Notifications et relances](reservations/notifications.md).

## Sur OfeliaScan

### Faut-il un téléphone par bibliothécaire ?

Pas obligatoire. Vous pouvez vous partager un téléphone, ou utiliser
votre propre téléphone Android personnel.

### OfeliaScan a-t-il besoin d'internet ?

Non. Il communique avec BibliOfelia via le Wi-Fi local de la Ofelia
Box. Aucune connexion internet n'est requise pour l'usage quotidien.

## Sur les langues

### Puis-je écrire un titre en malagasy ?

Oui. BibliOfelia accepte tous les caractères Unicode (accents,
alphabets non-latins). Saisissez le titre tel quel.

### Le membre francophone peut-il avoir une carte en français même si je
travaille en anglais ?

Oui. Au moment d'imprimer la carte, choisissez la langue dans le
sélecteur. Vous pouvez générer des PDF dans des langues différentes
sans changer votre propre langue d'interface.

## Sur les sauvegardes

### Mes données sont-elles sauvegardées ?

L'administrateur configure des sauvegardes automatiques quotidiennes
sur la Box. Vous voyez la **Dernière sauvegarde** dans le panneau
**État système** du dashboard.

Si elle ne date pas d'aujourd'hui ou d'hier, prévenez l'administrateur.

## Sur les cas difficiles

### Un livre est perdu ou trop abîmé, comment le sortir ? { #livre-perdu }

Pour un livre perdu pendant un prêt : ouvrez la [fiche du
membre](usagers/fiche.md), trouvez le prêt dans **Prêts en cours** et
cliquez sur **Perdu**. Le prêt et l'exemplaire passent au statut
*Perdu* ; le membre garde son historique et peut continuer
d'emprunter. Pour un livre rendu trop abîmé : enregistrez le retour,
puis sur la [fiche de l'exemplaire](catalogue/exemplaires.md) cliquez
sur **Mettre au rebut**. BibliOfelia ne gère ni amende ni facturation :
le remplacement relève de vos règles internes.

### Comment supprimer définitivement une notice du catalogue ? { #supprimer-notice }

Si une notice n'a plus aucun exemplaire (tous perdus, donnés, jetés),
ouvrez sa fiche et cliquez sur **Supprimer la notice**, ou utilisez une
[opération en lot](catalogue/operations-lot.md). Le code Ofelia d'un
exemplaire supprimé reste réservé à vie : une étiquette qui circule
encore ne pourra jamais désigner un autre livre par erreur.

### Un membre a perdu sa carte, que faire ? { #carte-perdue }

Ouvrez la [fiche du membre](usagers/fiche.md) et cliquez sur
**Remplacer la carte** : BibliOfelia attribue un nouveau numéro, met
l'ancien de côté pour de bon et conserve tout l'historique. L'ancienne
carte ne fonctionne plus (tout scan renvoie une erreur), détruisez-la
si elle réapparaît. En attendant la nouvelle carte, le membre peut
emprunter en étant recherché par son nom. Réimprimez la carte depuis
[Imprimer les cartes](impressions/cartes.md).

### Comment gérer un retard prolongé ? { #retard }

Suivez les retards via le compteur **Prêts en retard** du tableau de
bord et **Rapports → Prêts en retard**. Selon la gravité : (1) appelez
le membre (téléphone visible sur sa fiche) ; (2) pour bloquer ses
emprunts, **désactivez** temporairement le membre depuis sa fiche et
réactivez-le au retour des livres ; (3) pour un retard de plusieurs
mois, marquez le prêt **Perdu**. BibliOfelia ne génère pas de lettre de
relance : téléphone, SMS ou affichage restent les plus efficaces dans
une petite bibliothèque.

## Une question qui n'est pas listée ?

Contactez l'administrateur de votre Box.
