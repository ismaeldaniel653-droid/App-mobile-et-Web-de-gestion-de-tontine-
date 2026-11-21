import uuid
from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.tontines.models import Adhesion, Invitation, Tontine
from apps.utilisateurs.models import Utilisateur


@pytest.fixture
def client_api():
    return APIClient()


@pytest.fixture
def create_user():
    def _creer(telephone):
        return Utilisateur.objects.create(telephone=telephone)
    return _creer


@pytest.fixture
def tontine_president(create_user):
    utilisateur = create_user("+237690000111")
    tontine = Tontine.objects.create(
        nom="Tontine test",
        montant_cotisation=5000,
        frequence="hebdomadaire",
        nombre_mains_total=4,
        mode_passage="ordre_fixe",
        pourcentage_reserve=10,
        date_debut=timezone.now().date(),
        cree_par=utilisateur,
    )
    Adhesion.objects.create(utilisateur=utilisateur, tontine=tontine, role="president", mains=2, statut="actif")
    return utilisateur, tontine


@pytest.mark.django_db
def test_creer_tontine_et_lister_mes_tontines(client_api, create_user, tontine_president):
    utilisateur, tontine = tontine_president
    client_api.force_authenticate(user=utilisateur)

    reponse_creation = client_api.post(
        reverse("tontines_liste"),
        {
            "nom": "Nouvelle tontine",
            "montant_cotisation": 10000,
            "frequence": "mensuelle",
            "nombre_mains_total": 3,
            "mode_passage": "ordre_fixe",
            "pourcentage_reserve": 15,
            "date_debut": timezone.now().date(),
        },
        format="json",
    )

    assert reponse_creation.status_code == 201
    assert reponse_creation.json()["nom"] == "Nouvelle tontine"

    reponse_liste = client_api.get(reverse("tontines_liste"))
    assert reponse_liste.status_code == 200
    assert len(reponse_liste.json()) >= 2


@pytest.mark.django_db
def test_utilisateur_d_une_autre_tontine_ne_voit_rien(client_api, create_user, tontine_president):
    utilisateur, tontine = tontine_president
    autre_utilisateur = create_user("+237690000222")
    autre_tontine = Tontine.objects.create(
        nom="Autre tontine",
        montant_cotisation=2000,
        frequence="mensuelle",
        nombre_mains_total=2,
        mode_passage="ordre_fixe",
        pourcentage_reserve=5,
        date_debut=timezone.now().date(),
        cree_par=autre_utilisateur,
    )
    Adhesion.objects.create(utilisateur=autre_utilisateur, tontine=autre_tontine, role="president", mains=1, statut="actif")

    client_api.force_authenticate(user=utilisateur)
    reponse_liste = client_api.get(reverse("tontines_liste"))
    assert reponse_liste.status_code == 200
    assert all(item["id"] != autre_tontine.pk for item in reponse_liste.json())

    reponse_detail = client_api.get(reverse("tontine_detail", args=[autre_tontine.pk]))
    assert reponse_detail.status_code == 404


@pytest.mark.django_db
def test_membre_ne_peut_pas_inviter(client_api, create_user, tontine_president):
    utilisateur, tontine = tontine_president
    membre = create_user("+237690000333")
    Adhesion.objects.create(utilisateur=membre, tontine=tontine, role="membre", mains=1, statut="actif")
    client_api.force_authenticate(user=membre)

    reponse = client_api.post(
        reverse("tontine_invitation", args=[tontine.pk]),
        {"role_propose": "membre"},
        format="json",
    )

    assert reponse.status_code == 403


@pytest.mark.django_db
def test_invitation_expiree_ou_utilisee_est_refusee(client_api, create_user, tontine_president):
    utilisateur, tontine = tontine_president
    client_api.force_authenticate(user=utilisateur)

    invitation = Invitation.objects.create(
        tontine=tontine,
        role_propose="membre",
        jeton="token-expire",
        expire_le=timezone.now() - timedelta(days=1),
        usage_unique=True,
    )
    reponse_expiree = client_api.post(
        reverse("rejoindre_tontine"),
        {"jeton": invitation.jeton},
        format="json",
    )
    assert reponse_expiree.status_code == 400

    autre_utilisateur = create_user("+237690000444")
    invitation_active = Invitation.objects.create(
        tontine=tontine,
        role_propose="membre",
        jeton="token-actif",
        expire_le=timezone.now() + timedelta(days=1),
        usage_unique=True,
        utilise_par=autre_utilisateur,
    )
    reponse_utilisee = client_api.post(
        reverse("rejoindre_tontine"),
        {"jeton": invitation_active.jeton},
        format="json",
    )
    assert reponse_utilisee.status_code == 400


@pytest.mark.django_db
def test_changer_role_d_un_membre(client_api, create_user, tontine_president):
    utilisateur, tontine = tontine_president
    membre = create_user("+237690000555")
    adhesion = Adhesion.objects.create(utilisateur=membre, tontine=tontine, role="membre", mains=1, statut="actif")

    client_api.force_authenticate(user=utilisateur)
    reponse = client_api.patch(
        reverse("changer_role_membre", args=[tontine.pk, membre.pk]),
        {"role": "tresorier"},
        format="json",
    )

    assert reponse.status_code == 200
    adhesion.refresh_from_db()
    assert adhesion.role == "tresorier"
