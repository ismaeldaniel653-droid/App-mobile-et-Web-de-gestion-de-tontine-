# Vakoa

Vakoa aide les groupes de tontine au Cameroun a organiser leurs cotisations et leurs tours. La version 1 suit les paiements effectues hors de l'application ; elle ne detient ni ne transfere d'argent.

## Demarrage local

1. Installer Python 3.13 et copier `.env.example` vers `.env`.
2. Installer les dependances avec `python -m pip install -r requirements.txt`.
3. Demarrer PostgreSQL et Redis avec `docker compose up -d`.
4. Appliquer les migrations avec `python manage.py migrate`.
5. Lancer l'API avec `python manage.py runserver`.

La configuration locale est `config.settings.dev`. La passerelle SMS de developpement affiche un numero masque et le code dans la console ; ne pas l'utiliser en production.

## Verification

Lancer les tests avec `python -m pytest`. La documentation interactive est disponible sur `/api/docs/` et le schema OpenAPI sur `/api/schema/`.

## Production

Utiliser `DJANGO_SETTINGS_MODULE=config.settings.prod`, definir une cle `DJANGO_SECRET_KEY` aleatoire et unique, renseigner `DJANGO_ALLOWED_HOSTS`, les parametres PostgreSQL, Redis et les origines CORS HTTPS. `config.settings.prod` refuse une cle absente ou la valeur d'exemple et active les protections HTTPS. Avant le deploiement, lancer `python manage.py check --deploy` avec les variables de production.

Les throttles DRF utilisent le cache Django. Pour plusieurs processus ou serveurs, configurer un cache partage (Redis ou equivalent) ; le cache local par processus ne fournit pas une limite globale.

## Securite et routes

Le detail des roles, des controles existants et des limites connues est dans [SECURITE.md](SECURITE.md). Les limites OTP combinent le numero de telephone et l'adresse IP ; les comptes suspendus ne peuvent pas obtenir de jetons.