from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time

from apps.finances.models import Cotisation
from apps.notifications.models import Notification
from apps.notifications.tasks import (
    appliquer_penalites_retard,
    envoyer_confirmation_paiement,
    envoyer_rappels_echeance,
)
from apps.tontines.models import Adhesion, Cycle, Tontine
from apps.utilisateurs.models import Utilisateur


@pytest.fixture
def contexte_notifications():
    president = Utilisateur.objects.create(telephone="+237690000111")
    membre = Utilisateur.objects.create(telephone="+237690000222")
    tontine = Tontine.objects.create(
        nom="Tontine notifications",
        montant_cotisation=5000,
        frequence="mensuelle",
        nombre_mains_total=2,
        mode_passage="ordre_fixe",
        pourcentage_reserve=10,
        date_debut=timezone.now().date(),
        cree_par=president,
        regles_penalite={
            "retard": {"jours_de_grace": 1, "type": "fixe", "montant": 500},
        },
    )
    tontine.save(update_fields=["regles_penalite"])
    adhesion = Adhesion.objects.create(utilisateur=membre, tontine=tontine, role="membre", mains=1, statut="actif")
    cycle = Cycle.objects.create(
        tontine=tontine,
        numero=1,
        date_limite=timezone.now().date() - timedelta(days=2),
        montant_a_verser=5000,
        statut=Cycle.Statut.OUVERT,
    )
    cotisation = Cotisation.objects.create(
        cycle=cycle,
        adhesion=adhesion,
        montant_du=5000,
        montant_paye=0,
        statut=Cotisation.Statut.EN_RETARD,
    )
    return tontine, cycle, cotisation, membre


@pytest.mark.django_db
@freeze_time("2026-01-10")
def test_envoyer_rappels_echeance_cree_une_notification_j_2(contexte_notifications):
    tontine, cycle, _, membre = contexte_notifications
    cycle.date_limite = timezone.now().date() + timedelta(days=2)
    cycle.save(update_fields=["date_limite"])

    count = envoyer_rappels_echeance()

    assert count >= 1
    assert Notification.objects.filter(utilisateur=membre, canal="push").exists()


@pytest.mark.django_db
@freeze_time("2026-01-10")
def test_envoyer_rappels_echeance_est_idempotent(contexte_notifications):
    tontine, cycle, _, membre = contexte_notifications
    cycle.date_limite = timezone.now().date() + timedelta(days=2)
    cycle.save(update_fields=["date_limite"])

    envoyer_rappels_echeance()
    envoyer_rappels_echeance()

    assert Notification.objects.filter(utilisateur=membre, canal="push", message__icontains="échéance").count() == 1


@pytest.mark.django_db
@freeze_time("2026-01-10")
def test_appliquer_penalites_retard_cree_des_penalites_sans_doublon(contexte_notifications):
    _, cycle, cotisation, _ = contexte_notifications
    cycle.date_limite = timezone.now().date() - timedelta(days=2)
    cycle.save(update_fields=["date_limite"])

    appliquer_penalites_retard(cycle.pk, timezone.now().date())
    appliquer_penalites_retard(cycle.pk, timezone.now().date())

    assert cotisation.penalites.filter(type="retard").count() == 1


@pytest.mark.django_db
def test_envoyer_confirmation_paiement_est_idempotent(contexte_notifications):
    _, _, _, membre = contexte_notifications

    envoyer_confirmation_paiement(membre.pk, "ABC123", "REF123")
    envoyer_confirmation_paiement(membre.pk, "ABC123", "REF123")

    assert Notification.objects.filter(utilisateur=membre, canal="sms", message__icontains="ABC123").count() == 1


@pytest.mark.django_db
def test_envoyer_confirmation_paiement_ne_crée_pas_de_doublon_autre_paiement(contexte_notifications):
    _, _, _, membre = contexte_notifications

    envoyer_confirmation_paiement(membre.pk, "XYZ789", "REF456")
    envoyer_confirmation_paiement(membre.pk, "ABC123", "REF123")

    assert Notification.objects.filter(utilisateur=membre, canal="sms").count() == 2


@pytest.mark.django_db
@freeze_time("2026-01-10")
def test_envoyer_rappels_echeance_retourne_le_nombre_de_notifications(contexte_notifications):
    tontine, cycle, _, membre = contexte_notifications
    cycle.date_limite = timezone.now().date() + timedelta(days=2)
    cycle.save(update_fields=["date_limite"])

    count = envoyer_rappels_echeance()

    assert count == 1
    assert Notification.objects.filter(utilisateur=membre, canal="push").count() == 1


@pytest.mark.django_db
@freeze_time("2026-01-10")
def test_envoyer_rappels_echeance_pas_de_notification_j_0(contexte_notifications):
    """Le jour même de l'échéance (J-0), aucun rappel ne doit être envoyé."""
    tontine, cycle, _, membre = contexte_notifications
    cycle.date_limite = timezone.now().date()  # échéance aujourd'hui (J-0)
    cycle.save(update_fields=["date_limite"])

    count = envoyer_rappels_echeance()

    assert count == 0
    assert not Notification.objects.filter(
        utilisateur=membre, canal="push", message__icontains="échéance"
    ).exists()


@pytest.mark.django_db
@freeze_time("2026-01-10")
def test_envoyer_rappels_echeance_pas_de_notification_j_plus_1(contexte_notifications):
    """Le jour après l'échéance (J+1), aucun rappel ne doit être envoyé."""
    tontine, cycle, _, membre = contexte_notifications
    cycle.date_limite = timezone.now().date() - timedelta(days=1)  # échéance hier (J+1)
    cycle.save(update_fields=["date_limite"])

    count = envoyer_rappels_echeance()

    assert count == 0
    assert not Notification.objects.filter(
        utilisateur=membre, canal="push", message__icontains="échéance"
    ).exists()
