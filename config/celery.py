import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

application_celery = Celery("vakoa")
application_celery.config_from_object("django.conf:settings", namespace="CELERY")
application_celery.autodiscover_tasks()

from celery.schedules import crontab

# Planification des tâches planifiées
application_celery.conf.beat_schedule = {
    # Rappel 2 jours avant l'échéance des cycles
    "envoyer-rappels-echeance-2-jours": {
        "task": "apps.notifications.tasks.envoyer_rappels_echeance",
        "schedule": crontab(minute=0, hour=9),
    },
    # Application des pénalités de retard automatiquement après l'échéance
    "appliquer-penalites-retard": {
        "task": "apps.notifications.tasks.appliquer_penalites_retard",
        "schedule": crontab(minute=0, hour=10),
    },
    # Confirmation de paiement par SMS
    "envoyer-confirmation-paiement": {
        "task": "apps.notifications.tasks.envoyer_confirmation_paiement",
        "schedule": crontab(minute=0, hour=12),
    },
}
