from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from apps.finances.services import appliquer_penalites
from apps.notifications.models import Notification


# Coûts estimés des notifications (en FCFA, §5.15)
COUT_PUSH = 0      # Push gratuit
COUT_SMS = 25      # SMS environ 25 FCFA

@shared_task
def envoyer_rappels_echeance():
    """Envoie un rappel 2 jours avant l'échéance."""
    aujourd_hui = timezone.now().date()
    notifications_crees = 0
    from apps.tontines.models import Cycle

    for cycle in Cycle.objects.filter(statut="ouvert"):
        if (cycle.date_limite - aujourd_hui).days != 2:
            continue
        for adhesion in cycle.tontine.adhesions.filter(statut="actif"):
            message = f"Rappel : l'échéance du cycle {cycle.numero} est dans 2 jours."
            objet, created = Notification.objects.get_or_create(
                utilisateur=adhesion.utilisateur,
                canal=Notification.Canal.PUSH,
                message=message,
                defaults={
                    "statut": Notification.Statut.ENVOYEE,
                    "cout_estime": COUT_PUSH,
                },
            )
            if created:
                notifications_crees += 1
    return notifications_crees


@shared_task
def appliquer_penalites_retard(cycle_id=None, aujourdhui=None):
    """Applique les pénalités de retard sur un cycle donné, sans doublon."""
    from apps.tontines.models import Cycle

    if cycle_id is not None:
        cycle = Cycle.objects.get(pk=cycle_id)
    else:
        cycle = Cycle.objects.filter(statut="ouvert").order_by("numero").first()
    if cycle is None:
        return 0
    if aujourdhui is None:
        aujourdhui = timezone.now().date()
    appliquer_penalites(cycle, aujourdhui)
    return cycle.cotisations.count()


@shared_task
def envoyer_confirmation_paiement(utilisateur_id, code_recu, reference_transaction):
    """Envoie une confirmation de paiement de façon idempotente.

    Idempotence : on vérifie qu'aucune notification avec ce message
    n'existe déjà pour cet utilisateur avant de créer une nouvelle.
    Le canal est SMS (échéance critique).
    """
    from apps.utilisateurs.models import Utilisateur
    from apps.utilisateurs.passerelle_sms import PasserelleSmsConsole

    utilisateur = Utilisateur.objects.get(pk=utilisateur_id)
    message = f"Paiement confirme. Code du reçu : {code_recu}. (ref: {reference_transaction})"

    # Vérification idempotente : si une notification avec ce message existe déjà,
    # on ne crée pas de doublon
    if Notification.objects.filter(
        utilisateur=utilisateur,
        canal=Notification.Canal.SMS,
        message=message,
    ).exists():
        return 0

    # Envoi via la passerelle SMS (implémentation console en développement)
    passerelle = PasserelleSmsConsole()
    passerelle.envoyer_code(utilisateur.telephone, message)

    Notification.objects.create(
        utilisateur=utilisateur,
        canal=Notification.Canal.SMS,
        message=message,
        statut=Notification.Statut.ENVOYEE,
        cout_estime=COUT_SMS,
    )
    return 1
