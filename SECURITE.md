# Revue de securite

## Routes et controles

| Route | Acces requis | Controle et tests |
|---|---|---|
| `GET /api/sante/` | Public | Endpoint de sante ; pas de donnee personnelle renvoyee. |
| `POST /api/auth/demander-code/` | Public, limite par telephone et IP | OTP hache, limite d'envoi testee, throttle IP teste. |
| `POST /api/auth/verifier-code/` | Public, limite par IP | Expiration, cinq essais, usage unique et throttle IP ; compte suspendu refuse. |
| `GET /api/tontines/` | JWT valide | Liste limitee aux adhesions de l'utilisateur ; test d'isolation entre tontines. |
| `POST /api/tontines/` | JWT valide | Le createur devient president ; acces authentifie. |
| `GET /api/tontines/{id}/` | JWT et adhesion a cette tontine | Retourne 404 hors adhesion ; test d'isolation. |
| `POST /api/tontines/{id}/inviter/` | President de la tontine | Controle d'appartenance et de role ; test qu'un membre ne peut pas inviter. |
| `POST /api/tontines/rejoindre/` | JWT valide et invitation valide | Jeton expire ou deja utilise refuse. |
| `PATCH /api/tontines/{id}/membres/{utilisateur_id}/role/` | President de la tontine | Membre cible recherche dans la meme tontine ; changement de role teste. |
| `GET /api/schema/`, `GET /api/docs/` | Public | Schema et interface Swagger. |
| `/admin/` | Compte Django staff | Acces protege par l'administration Django ; utiliser un mot de passe unique. |

## Mesures appliquees

- Les OTP sont haches, expirent et sont invalides apres utilisation ou cinq erreurs.
- Les demandes sont limitees par numero et les deux routes OTP sont aussi limitees par adresse IP.
- Les comptes inactifs ou marques `suspendu` ne recoivent pas de JWT.
- En production, une cle secrete explicite est obligatoire ; HTTPS, HSTS, cookies securises, protection contre le sniffing MIME et refus d'integration en iframe sont actives.
- Les routes de tontines filtrent les donnees par adhesion cote serveur.
- La passerelle SMS console est reservee au developpement et masque le numero affiche.

## Limites et actions de deploiement

- Les throttles DRF s'appuient sur le cache Django. En production multi-processus, configurer un cache partage avant exposition publique.
- La passerelle SMS de production n'est pas configuree dans ce depot ; ne pas deployer la passerelle console.
- `check --deploy` doit etre execute avec les variables de production. Les en-tetes transmis par un proxy HTTPS ne doivent etre approuves que si le proxy est sous controle de l'exploitant.
- Les paiements restent des enregistrements manuels : aucune integration de transfert d'argent n'est presente en v1.

## Journalisation

Les vues d'authentification ne journalisent pas le numero ni le code OTP. La passerelle de developpement affiche un numero partiellement masque et le code OTP dans la console ; ces journaux restent sensibles et ne doivent pas etre conserves ni utilises en production.