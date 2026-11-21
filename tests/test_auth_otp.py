from datetime import timedelta

import pytest
from django.contrib.auth.hashers import make_password
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.utilisateurs.models import CodeOtp


class PasserelleSmsFaux:
    derniers_codes = {}

    def envoyer_code(self, telephone, code):
        self.__class__.derniers_codes[telephone] = code


@pytest.fixture(autouse=True)
def configurer_passerelle_sms(settings):
    settings.PASSERELLE_SMS = "tests.test_auth_otp.PasserelleSmsFaux"
    PasserelleSmsFaux.derniers_codes.clear()


@pytest.fixture
def client():
    return APIClient()


@pytest.mark.django_db
def test_demande_et_verification_de_code_valide(client):
    telephone = "+237690000001"

    reponse_demande = client.post(reverse("demander_code"), {"telephone": telephone}, format="json")

    assert reponse_demande.status_code == 200
    assert reponse_demande.json() == {"statut": "code_envoye"}
    assert telephone in PasserelleSmsFaux.derniers_codes

    code = PasserelleSmsFaux.derniers_codes[telephone]
    reponse_verification = client.post(
        reverse("verifier_code"),
        {
            "telephone": telephone,
            "code": code,
            "version_consentement": "v1",
            "type_consentement": "conditions_utilisation",
        },
        format="json",
    )

    assert reponse_verification.status_code == 200
    donnees = reponse_verification.json()
    assert "acces" in donnees
    assert "rafraichissement" in donnees
    assert donnees["utilisateur"]["telephone"] == telephone


@pytest.mark.django_db
def test_verification_avec_mauvais_code(client):
    telephone = "+237690000002"
    client.post(reverse("demander_code"), {"telephone": telephone}, format="json")

    reponse = client.post(
        reverse("verifier_code"),
        {
            "telephone": telephone,
            "code": "000000",
            "version_consentement": "v1",
            "type_consentement": "conditions_utilisation",
        },
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.json() == {"erreur": "Code incorrect."}


@pytest.mark.django_db
def test_verification_avec_code_expire(client):
    telephone = "+237690000003"
    client.post(reverse("demander_code"), {"telephone": telephone}, format="json")
    otp = CodeOtp.objects.get(telephone=telephone)
    otp.expiration = timezone.now() - timedelta(minutes=1)
    otp.save(update_fields=["expiration"])

    reponse = client.post(
        reverse("verifier_code"),
        {
            "telephone": telephone,
            "code": PasserelleSmsFaux.derniers_codes[telephone],
            "version_consentement": "v1",
            "type_consentement": "conditions_utilisation",
        },
        format="json",
    )

    assert reponse.status_code == 400
    assert reponse.json() == {"erreur": "Le code a expire. Demandez-en un nouveau."}


@pytest.mark.django_db
def test_verification_avec_trop_d_essais(client, settings):
    telephone = "+237690000004"
    settings.OTP_MAX_ESSAIS = 3
    otp = CodeOtp.objects.create(
        telephone=telephone,
        code_hash=make_password("123456"),
        expiration=timezone.now() + timedelta(minutes=5),
        tentatives=2,
    )

    reponse = client.post(
        reverse("verifier_code"),
        {
            "telephone": telephone,
            "code": "111111",
            "version_consentement": "v1",
            "type_consentement": "conditions_utilisation",
        },
        format="json",
    )

    otp.refresh_from_db()
    assert reponse.status_code == 429
    assert reponse.json() == {"erreur": "Nombre maximum d'essais atteint."}
    assert otp.utilise is True


@pytest.mark.django_db
def test_demande_code_avec_trop_de_demandes(client, settings):
    telephone = "+237690000005"
    settings.OTP_MAX_ENVOIS = 1
    settings.OTP_FENETRE_ENVOIS_SECONDES = 3600

    premiere_demande = client.post(reverse("demander_code"), {"telephone": telephone}, format="json")
    deuxieme_demande = client.post(reverse("demander_code"), {"telephone": telephone}, format="json")

    assert premiere_demande.status_code == 200
    assert deuxieme_demande.status_code == 429
    assert deuxieme_demande.json() == {"erreur": "Trop de demandes. Reessayez plus tard."}
