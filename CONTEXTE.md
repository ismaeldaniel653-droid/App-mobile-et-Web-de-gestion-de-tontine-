# CONTEXTE.md – Projet Vakoa (à lire avant chaque tâche)

## 1. Le projet en 5 lignes
Vakoa est une application de tontine (njangi) pour le Cameroun, sur Android (application Flutter) et sur le web (site React léger).
Elle remplace le cahier : cotisations, tours de rôle, mains multiples, enchères, pénalités, rappels.
**Version 1 : suivi et organisation seulement. L'application ne détient ni ne transfère jamais d'argent.**
Le trésorier enregistre à la main les paiements faits en dehors de l'application.
Deux fonctions différenciantes : le **reçu à code de vérification** et la **couverture collective des défaillances** (avec caisse de réserve).

## 2. Stack
- Backend : Python, Django, Django REST Framework, SimpleJWT, drf-spectacular (Swagger)
- Base : PostgreSQL (via docker-compose)
- Tâches automatiques : Celery + Redis
- Tests : pytest + pytest-django
- Application mobile (plus tard) : Flutter (Android seulement), Riverpod, dio
- Site web (plus tard) : React (Vite) en JavaScript, léger et rapide sur réseau 3G, qui appelle la même API Django
- Cibles : Android 8+ (Flutter) et navigateurs modernes (React). **Pas d'application iOS en v1** : les utilisateurs d'iPhone passent par le site web.

## 3. Conventions de code (IMPORTANT : tout en français)
- **Tous les noms du code sont en français, sans accents** : modèles, champs, fonctions, variables, applications, routes. Exemples : `Cotisation`, `montant_du`, `calculer_solde`, `/api/paiements/`.
- Les mots imposés par les outils restent en anglais (`models`, `queryset`, `serializer`, `viewset`, `migration`, `test_`). Ne les traduis pas.
- Les commentaires et les messages affichés à l'utilisateur sont en français.
- Ne mélange jamais deux langues pour un même concept (pas de `Payment` et `paiement` dans le même projet).
- Flutter et React : noms de fichiers, composants et variables en français sans accents (par exemple `EcranConnexion`, `ListeTontines`). Les mots imposés (`useState`, `useEffect`, `Widget`, `build`) restent en anglais.
- **Site web : rester léger.** Pas de grosse bibliothèque d'interface, code découpé par écran, images compressées. Objectif à mesurer : première page sous 300 Ko.
- Une application Django par domaine. La logique métier va dans des fichiers `services.py`, pas dans les vues ni dans les modèles.
- Les fonctions de calcul sont **pures** (sans accès à la base) quand c'est possible : elles sont plus faciles à tester et à expliquer.
- Chaque fonctionnalité = code + tests + explication simple en français de ce qui a été fait.

## 4. Vocabulaire du projet
| Idée | Nom dans le code |
|---|---|
| utilisateur | `Utilisateur` |
| code SMS | `CodeOtp` |
| consentement | `Consentement` |
| tontine | `Tontine` |
| membre d'une tontine | `Adhesion` (rôles : `president`, `tresorier`, `membre`) |
| main (part d'un membre) | `mains` (champ de `Adhesion`) |
| lien d'invitation | `Invitation` |
| cycle / tour | `Cycle` |
| cotisation due par un membre pour un cycle | `Cotisation` |
| paiement | `Paiement` |
| pénalité | `Penalite` |
| défaut / trou de caisse | `Defaut` |
| part de couverture d'un membre | `RepartitionDefaut` |
| mouvement de la caisse de réserve | `MouvementReserve` |
| journal d'audit | `JournalAudit` |
| contestation d'une écriture | `Contestation` |
| notification | `Notification` |
| mode de passage | `mode_passage` : `ordre_fixe` ou `encheres` |
| statuts d'une cotisation | `paye`, `partiel`, `en_retard`, `absent` |
| mode de répartition d'un défaut | `egal` ou `selon_mains` |

## 5. Règles métier NON NÉGOCIABLES
1. **Montants en entiers (FCFA)**, jamais de `float` ni de décimal pour l'argent.
2. **Montant dû par cycle = `mains` du membre × `montant_cotisation` de la tontine**, plus la pénalité éventuelle du cycle précédent. Cette formule vit dans UNE seule fonction, `calculer_montant_du`, commentée, jamais dupliquée.
3. **Aucune écriture financière n'est supprimée ni modifiée.** Un paiement se corrige par une écriture d'annulation (`annulation_de` pointe vers le paiement annulé) avec motif et auteur.
4. **Le solde d'un membre se calcule** (`calculer_solde`) à partir des cotisations, paiements et pénalités. Jamais un champ saisi à la main.
5. **Une pénalité garde la règle appliquée** (`regle_appliquee`, copie JSON au moment du calcul). Changer le barème d'une tontine ne réécrit jamais le passé.
6. **Un membre ne peut pas être bénéficiaire plus souvent que son nombre de mains** (contrainte en base, pas seulement dans l'API).
7. **Mode `ordre_fixe`** : le bénéficiaire suit l'ordre verrouillé. **Mode `encheres`** : le bénéficiaire est le gagnant, et `montant_offert` / `interet_distribue` du cycle portent le résultat. Un cycle ne peut pas avoir les deux. Le bénéficiaire peut être vide.
8. **Isolation par tontine** : un utilisateur ne voit que les tontines dont il est membre. Le contrôle est côté serveur, sur CHAQUE requête.
9. **Chaque écriture financière** porte l'auteur (`enregistre_par`) et l'horodatage, et crée une ligne dans `JournalAudit`.
10. **Code OTP** : haché en base, expire en 5 minutes, 5 essais maximum, envois limités par numéro.
11. **Reçu vérifiable** : chaque paiement a un `code_verification` de 6 caractères calculé par HMAC-SHA256 de `identifiant|montant|horodatage` avec une clé secrète du serveur.
12. **Couverture d'une défaillance** : calcul du montant manquant ; la caisse de réserve est utilisée en priorité ; le reste est réparti entre les autres membres (égal ou selon les mains, selon la tontine).
13. **Caisse de réserve** : plafonnée (par exemple à un cycle de cotisation) ; une sortie (`ponction`) exige l'accord du président ET du trésorier, avec motif.
14. **Données personnelles** : pas de pièce d'identité ni de photo en v1. Consentement enregistré avec la version du texte. Aucun PIN ni donnée bancaire stocké.
15. **Notifications** : push par défaut, SMS seulement pour les échéances critiques et les confirmations de paiement. Le coût estimé de chaque notification est enregistré.

## 6. Hors périmètre v1 (ne PAS coder)
Paiement MoMo / Orange Money, épargne, crédit, garants, score de fiabilité, interface d'enchères (le modèle de données existe, pas l'écran), synchronisation hors-ligne en saisie, application iOS, témoignages publics.

## 7. Structure du projet
```
vakoa/
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   └── prod.py
│   ├── urls.py
│   ├── celery.py
│   └── wsgi.py
├── apps/
│   ├── utilisateurs/
│   ├── tontines/
│   ├── finances/
│   ├── couverture/
│   ├── notifications/
│   └── audit/
├── tests/
│   ├── utilisateurs/  tontines/  finances/  couverture/  notifications/
│   └── conftest.py
├── mobile/
├── web/
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── pytest.ini
├── CONTEXTE.md
└── PROMPTS.md
```

## 8. Rôles et droits (résumé)
| Action | `president` | `tresorier` | `membre` |
|---|---|---|---|
| Créer / paramétrer la tontine | oui | non | non |
| Inviter, gérer les rôles | oui | non | non |
| Enregistrer un paiement | non | oui | non |
| Déclarer une défaillance | non | oui | non |
| Sortir de la caisse de réserve | accord requis | accord requis | non |
| Voir soldes et reçus du groupe | oui | oui | oui |
| Contester une écriture | oui | oui | oui |

## 9. Définition de « terminé » pour une tâche
- Les tests passent (`pytest`) et couvrent les cas limites.
- Les routes sont documentées dans Swagger.
- Les permissions sont testées (un membre d'une autre tontine reçoit 403 ou 404).
- Chaque fichier est expliqué en français simple (pour que l'auteur puisse le présenter au jury).
- Un commit Git clair est fait.