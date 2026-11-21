# PROMPTS.md – Développer Vakoa avec une IA dans VS Code

## Comment travailler (à lire une fois)

1. Mets `CONTEXTE.md` à la racine du projet. Au début de chaque conversation, dis : « Lis d'abord CONTEXTE.md. Tous les noms du code sont en français, sans accents. »
2. Un prompt à la fois. Ne passe au suivant que lorsque les tests passent et que tu as compris le code.
3. Après chaque prompt :
   - lance `pytest` ;
   - teste dans Swagger (`/api/docs/`) ;
   - lis le code ; si tu ne comprends pas, demande : « Explique-moi ce fichier ligne par ligne, en français simple » ;
   - fais un commit : `git add . && git commit -m "message clair"`.
4. Ajoute à la fin de chaque prompt : **« Donne le code, les tests, et une explication simple en français. »**
5. Si l'IA se trompe, colle l'erreur complète et dis : « Corrige, et explique la cause. »
6. Prépare ton jury à chaque étape avec ce prompt, une fois les tests passés :

```text
Prépare-moi 5 questions qu'un jury pourrait me poser sur ce code, avec des réponses simples
que je peux dire avec mes mots. Ajoute une question piège sur une décision de conception.
```

7. Si l'IA écrit un nom en anglais ou avec un accent, demande-lui de le renommer avant de continuer.

## Prompts deja realises (à garder en premier)

- Prompt 0 – Preparation : structure du projet, .gitignore, README, requirements, sans code applicatif.
- Prompt 1 – Projet Django, base de donnees, Swagger : settings, .env, docker-compose, DRF, JWT, Swagger, route /api/sante/ et test.
- Prompt 2 – Utilisateurs et connexion par code SMS : modele Utilisateur, CodeOtp, Consentement, endpoints /api/auth/demander-code/ et /api/auth/verifier-code/, JWT, tests OTP.

### Mots de Django à connaître pour expliquer ton code
| Mot | Ce que ça veut dire |
|---|---|
| modèle (`models.py`) | une table de la base de données, écrite en Python |
| migration | le fichier qui crée ou modifie les tables |
| sérialiseur (`serializer`) | transforme un objet en JSON (et l'inverse), et vérifie les données reçues |
| vue (`view` / `viewset`) | reçoit une requête de l'application et renvoie une réponse |
| permission | la règle qui dit qui a le droit de faire quoi |
| service (`services.py`) | la logique métier : calculs, règles de la tontine |
| tâche Celery | un travail lancé automatiquement (rappels, pénalités) |
| test | un petit programme qui vérifie que ton code fait ce qu'il doit |

---

## Partie A – Backend Django

### Prompt 0 – Préparation
```text
Lis CONTEXTE.md. Crée la structure de dossiers décrite au §7 (dossiers et fichiers vides
avec __init__.py), un fichier .gitignore pour Python/Django, un README.md court en
français, et un requirements.txt avec : django, djangorestframework,
djangorestframework-simplejwt, drf-spectacular, psycopg[binary], celery, redis,
python-dotenv, pytest, pytest-django, freezegun, django-cors-headers.
Ne code rien d'autre pour l'instant. Tous les noms sont en français, sans accents.
```

### Prompt 1 – Projet Django, base de données, Swagger
```text
Initialise le projet Django dans config/ avec des settings séparés (base, dev, prod) lus
depuis .env (fournis .env.example). Ajoute un docker-compose.yml avec PostgreSQL et Redis.
Configure DRF, SimpleJWT, drf-spectacular (Swagger sur /api/docs/), CORS, pytest.ini et
un conftest.py de base. La langue est fr-fr, le fuseau Africa/Douala.
Ajoute une route /api/sante/ qui renvoie {"statut": "ok"} et son test.
Donne le code, les tests et une explication simple en français.
```

### Prompt 2 – Utilisateurs et connexion par code SMS
```text
Dans apps/utilisateurs, crée :
- un modèle Utilisateur identifié par le numéro de téléphone (unique, format international),
  avec nom, ville, langue, statut (c'est le modèle utilisateur du projet) ;
- CodeOtp (telephone, code_hash, expiration, tentatives, utilise) ;
- Consentement (utilisateur, type, version_texte, date).
Endpoints : POST /api/auth/demander-code/ et POST /api/auth/verifier-code/ (renvoie un JWT
accès + refresh, crée l'utilisateur s'il n'existe pas, et enregistre le consentement).
Règles du §5.10 de CONTEXTE.md : code haché, expiration 5 minutes, 5 essais, limitation des
envois par numéro. L'envoi SMS passe par une interface PasserelleSms avec une
implémentation PasserelleSmsConsole (affiche le code dans la console) pour le développement.
Écris des tests : bon code, mauvais code, code expiré, trop d'essais, trop de demandes.
Donne le code, les tests et une explication simple en français.
```

### Prompt 3 – Tontines, membres, rôles, invitations, isolation
```text
Dans apps/tontines, crée Tontine (nom, montant_cotisation, frequence, nombre_mains_total,
mode_passage, pourcentage_reserve, date_debut, statut, regles_penalite en JSON, cree_par),
Adhesion (utilisateur, tontine, role, mains, statut) et Invitation (jeton, role_propose,
expire_le, usage_unique, utilise_par).
Endpoints : créer une tontine (le créateur devient président), lister MES tontines,
détail, créer un lien d'invitation, rejoindre avec un lien, changer le rôle d'un membre.
Écris une permission DRF réutilisable qui vérifie l'appartenance à la tontine ET le rôle,
selon le tableau du §8 de CONTEXTE.md. L'isolation est obligatoire (§5.8).
Tests : un utilisateur d'une autre tontine ne voit rien (404), un membre ne peut pas
inviter, un lien expiré ou déjà utilisé est refusé.
Donne le code, les tests et une explication simple en français.
```

### Prompt 4 – Cycles, mains et montant dû
```text
Dans apps/tontines, crée Cycle (tontine, numero, date_limite, montant_a_verser,
montant_encaisse, beneficiaire peut être vide, montant_offert, interet_distribue,
regle_penalite_appliquee, statut) et dans apps/finances, Cotisation (cycle, adhesion,
montant_du, montant_paye, statut).
Écris UNE fonction pure calculer_montant_du(mains, montant_cotisation, penalite_reportee)
dans apps/finances/services.py, commentée en français, qui applique la formule du §5.2.
Écris le service generer_cycles qui crée les cycles d'une tontine et les cotisations de
chaque membre.
Ajoute en base les contraintes : un membre ne peut pas être bénéficiaire plus souvent que
son nombre de mains ; un cycle ne peut pas avoir à la fois un bénéficiaire d'ordre fixe et
une enchère (§5.6 et §5.7).
Tests : membre à 1 main et à 2 mains, pénalité reportée, dépassement du nombre de mains
refusé, ordre verrouillé après le démarrage.
Donne le code, les tests et une explication simple en français.
```

### Prompt 5 – Paiements, reçu vérifiable, annulation
```text
Dans apps/finances, crée Paiement (cotisation, montant, mode, reference_transaction,
enregistre_par, date, preuve, code_verification, annulation_de, motif_annulation).
Règles : seul le trésorier enregistre un paiement ; un paiement n'est JAMAIS supprimé ni
modifié (bloque la suppression et la modification dans le modèle et dans l'API) ; une
correction crée un paiement négatif d'annulation qui pointe vers l'original (§5.3).
Écris calculer_code_verification(identifiant, montant, horodatage, cle_secrete) : HMAC-SHA256,
6 caractères (§5.11).
Écris le service calculer_solde(adhesion) à partir des cotisations, paiements et pénalités
(§5.4). Chaque écriture crée une ligne JournalAudit (crée le modèle minimal dans apps/audit
si besoin).
Endpoints : enregistrer un paiement, voir le reçu, vérifier un code (n'importe quel membre
de la tontine peut contrôler).
Tests : paiement partiel puis complet, annulation, code correct et incorrect, un membre
simple ne peut pas enregistrer, suppression impossible.
Donne le code, les tests et une explication simple en français.
```

### Prompt 6 – Pénalités (le plus critique : beaucoup de tests)
```text
Dans apps/finances, crée Penalite (cotisation, type, montant, regle_appliquee en JSON, motif,
date). Les règles d'une tontine sont dans regles_penalite, par exemple :
{"retard": {"jours_de_grace": 1, "type": "fixe", "montant": 500},
 "absence": {"type": "pourcentage", "valeur": 10}}
Écris des fonctions pures calculer_penalite_retard(...) et calculer_penalite_absence(...),
puis un service appliquer_penalites(cycle, aujourdhui) qui crée les pénalités manquantes
SANS doublon (il doit pouvoir être relancé sans rien dupliquer) et copie la règle utilisée
dans regle_appliquee (§5.5).
Tests (au moins 15, sous forme de tableau paramétré) : pas de retard, retard dans le délai
de grâce, retard après, pourcentage, absence, double exécution, barème modifié après coup
(les anciennes pénalités ne changent pas), arrondi en entiers.
Donne le code, les tests et une explication simple en français.
```

### Prompt 7 – Défaillance, couverture collective, caisse de réserve
```text
Dans apps/couverture, crée Defaut (cycle, adhesion, montant_manquant, mode_repartition,
statut, date_constat), RepartitionDefaut (defaut, adhesion, montant_du, montant_paye) et
MouvementReserve (tontine, cycle, sens, montant, motif, enregistre_par, date).
Écris les fonctions pures :
- calculer_contribution_reserve(montant_encaisse, pourcentage_reserve) pour alimenter la caisse ;
- calculer_couverture(montant_manquant, solde_reserve, membres, mode_repartition) qui utilise
d'abord la caisse de réserve, puis répartit le reste entre les autres membres (égal ou
selon les mains), en entiers, sans perdre un seul franc (le reste de la division va au
premier membre) (§5.12).
Écris le service declarer_defaut (rôle trésorier). Une sortie de caisse (ponction) exige
l'accord du président ET du trésorier, avec motif, et ne dépasse pas le plafond (§5.13).
Tests : caisse suffisante, caisse insuffisante, répartition égale et selon les mains,
arrondis, sortie sans double accord refusée.
Donne le code, les tests et une explication simple en français.
```

### Prompt 8 – Audit et contestation
```text
Dans apps/audit, finalise JournalAudit (utilisateur, action, objet, ancienne_valeur,
nouvelle_valeur, date) alimenté par les services financiers. Ajoute un modèle simple
Contestation (adhesion, type_objet, id_objet, motif, statut, traitee_par, date) : un membre
peut contester une écriture qui le concerne ; le président ou le trésorier répond.
Endpoints pour créer, lister et répondre.
Tests : seul le concerné peut contester, la contestation ne modifie jamais l'écriture
d'origine, l'audit trace chaque action.
Donne le code, les tests et une explication simple en français.
```

### Prompt 9 – Rappels et tâches automatiques (Celery)
```text
Dans apps/notifications, crée Notification (utilisateur, canal, message, statut,
cout_estime). Configure Celery + Celery Beat. Écris les tâches :
- envoyer_rappels_echeance : rappel 2 jours avant l'échéance (push par défaut) ;
- appliquer_penalites_retard : après l'échéance, appelle appliquer_penalites du Prompt 6 ;
- envoyer_confirmation_paiement : confirme chaque paiement avec le code du reçu (SMS autorisé).
Les tâches doivent être idempotentes (relancées deux fois, elles n'envoient pas deux fois).
Le canal SMS passe par l'interface PasserelleSms du Prompt 2 ; enregistre le coût estimé.
Tests avec freezegun : J-2, J-0, J+1, double exécution.
Donne le code, les tests et une explication simple en français.
```

### Prompt 10 – Revue sécurité et documentation
```text
Fais une revue de sécurité de tout le backend :
1. liste chaque route avec son rôle requis et vérifie qu'un test d'isolation existe ;
2. vérifie la limitation de débit sur /api/auth/demander-code/ et /api/auth/verifier-code/ ;
3. vérifie qu'aucune donnée sensible n'est écrite dans les journaux (téléphone, codes) ;
4. vérifie que settings/prod.py force HTTPS et désactive DEBUG ;
5. complète la documentation Swagger (descriptions en français, exemples).
Propose les corrections sous forme de liste, puis applique-les une par une avec tests.
```

---

## Partie B – Application Flutter (Android)

Donne à l'IA l'URL de ton API et copie la réponse JSON de Swagger dans le prompt. Les noms Flutter sont aussi en français (`ecran_connexion`, `liste_tontines`), sauf les mots imposés par les outils (`Widget`, `build`, `State`).

### Prompt F1 – Projet Flutter
```text
Crée un projet Flutter (Android seulement, pas de web). Utilise Riverpod pour l'état, dio pour les appels
API, flutter_secure_storage pour les jetons JWT, go_router pour la navigation. Prépare un
tème simple, des gros boutons, texte en français. Crée une couche client_api avec
intercepteur qui ajoute le JWT et rafraîchit le jeton. Application légère : pas de
paquets inutiles. Noms de fichiers, classes et variables en français sans accents.
```

### Prompt F2 – Connexion par code SMS
```text
Crée les écrans : saisie du numéro de téléphone, saisie du code à 6 chiffres, avec gestion
des erreurs (code faux, expiré, trop d'essais) et un écran de consentement avant la
première connexion. Branche-les sur POST /api/auth/demander-code/ et
/api/auth/verifier-code/.
Voici un exemple de réponse de l'API : [colle ici le JSON de Swagger]
```

### Prompt F3 – Mes tontines et détail
```text
Crée l'écran "Mes tontines" (liste) et l'écran "Détail d'une tontine" : membres, cycle en
cours, prochain bénéficiaire, mon solde. Ajoute un cache en lecture (les données déjà
consultées restent visibles sans réseau, avec un bandeau "Hors connexion"). La saisie reste
désactivée hors connexion.
Exemple de réponse API : [colle ici le JSON]
```

### Prompt F4 – Cotisations et soldes
```text
Crée l'écran de suivi des cotisations du cycle en cours : une ligne par membre avec le
statut (payé, partiel, en retard, absent), le montant dû et le reste à payer. Pour le
membre, ajoute son historique et ses reçus.
```

### Prompt F5 – Enregistrer un paiement (trésorier)
```text
Crée le parcours trésorier en MOINS DE 4 ÉCRANS : choix du membre, montant pré-rempli
avec le reste à payer, confirmation, puis affichage du reçu avec son code de vérification.
Gros boutons, textes courts. Seul le rôle trésorier voit ce parcours.
```

### Prompt F6 – Vérifier un reçu et déclarer une défaillance
```text
Crée l'écran "Vérifier un reçu" (saisie du code à 6 caractères) et l'écran du trésorier
"Déclarer une défaillance" qui affiche le calcul de la couverture (part de la caisse de
réserve, part de chaque membre) avant de confirmer.
```

## Partie B2 – Site web React (léger et rapide)

Le site web est volontairement réduit aux écrans essentiels (connexion, mes tontines, cotisations, saisie d'un paiement, vérification d'un reçu). Il utilise la même API que Flutter. Objectif : se charger vite en 3G.

### Prompt R1 – Projet React léger
```text
Crée un projet React avec Vite dans web/ (JavaScript, pas de TypeScript). Utilise seulement
react-router pour la navigation et l'API fetch native pour les appels (pas d'axios, pas de
grosse bibliothèque d'interface comme Bootstrap ou Material UI). Écris un CSS simple, des
gros boutons, texte en français, mise en page pour téléphone d'abord. Crée un module
client_api qui ajoute le JWT aux requêtes et rafraîchit le jeton. Garde le jeton d'accès en
mémoire et explique-moi le risque de chaque endroit de stockage du jeton de rafraîchissement.
Noms de fichiers, composants et variables en français sans accents. Le projet doit rester
léger : dis-moi le poids du build à la fin.
```

### Prompt R2 – Connexion par code SMS
```text
Crée les pages : saisie du numéro de téléphone, saisie du code à 6 chiffres, avec gestion
des erreurs (code faux, expiré, trop d'essais) et une page de consentement avant la première
connexion. Branche-les sur POST /api/auth/demander-code/ et /api/auth/verifier-code/.
Exemple de réponse de l'API : [colle ici le JSON de Swagger]
```

### Prompt R3 – Mes tontines, détail et cotisations
```text
Crée la page "Mes tontines" (liste), la page "Détail d'une tontine" (membres, cycle en cours,
prochain bénéficiaire, mon solde) et la page de suivi des cotisations du cycle en cours :
une ligne par membre avec statut, montant dû et reste à payer. Charge chaque page à la
demande (lazy loading) pour garder le site léger.
Exemple de réponse API : [colle ici le JSON]
```

### Prompt R4 – Saisie d'un paiement (trésorier) et vérification d'un reçu
```text
Crée le parcours trésorier en MOINS DE 4 ÉCRANS : choix du membre, montant pré-rempli avec le
reste à payer, confirmation, puis reçu avec son code de vérification. Crée aussi la page
"Vérifier un reçu" (saisie du code à 6 caractères). Seul le rôle trésorier voit le parcours
de saisie. Gros boutons, textes courts.
```

### Prompt R5 – Poids, vitesse et installation sur téléphone
```text
Optimise le site pour la 3G : découpage du code par page, images compressées, polices
système, build de production. Mesure le poids de la première page et le temps de chargement
(Lighthouse) et donne-moi les chiffres avant et après. Ajoute un manifeste pour que le site
puisse être ajouté à l'écran d'accueil du téléphone (utile sur iPhone). Ne passe pas
au-dessus de l'objectif de 300 Ko pour la première page sans me prévenir.
```

---

## Partie C – Mise en ligne (si le temps le permet)

### Prompt D1 – Déploiement
```text
Prépare un déploiement sur un petit serveur Linux (VPS) : Dockerfile du backend,
docker-compose de production (Django + Gunicorn, PostgreSQL, Redis, Celery worker et beat,
Nginx avec HTTPS, qui sert aussi les fichiers du site React construit), sauvegarde quotidienne chiffrée de la base, et un guide de déploiement
pas à pas en français.
```

---

## Ordre conseillé et durée indicative (à temps partiel)
| Étape | Prompts | Durée indicative |
|---|---|---|
| Socle | 0, 1, 2 | 1 semaine |
| Cœur métier | 3, 4, 5 | 2 semaines |
| Règles critiques | 6, 7, 8 | 2 semaines |
| Automatisation et sécurité | 9, 10 | 1 à 2 semaines |
| Application Android (Flutter) | F1 à F6 | 3 à 5 semaines |
| Site web (React) | R1 à R5 | 2 à 3 semaines |
| Déploiement | D1 | 1 semaine |

## À ne jamais faire
- Accepter du code que tu ne comprends pas.
- Passer au prompt suivant avec des tests qui échouent.
- Laisser l'IA changer une règle du §5 de CONTEXTE.md sans que tu l'aies décidé.
- Mettre des vrais numéros de téléphone ou des clés secrètes dans le dépôt Git.

