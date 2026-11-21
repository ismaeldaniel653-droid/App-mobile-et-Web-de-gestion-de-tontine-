from datetime import timedelta
from unittest.mock import patch

import pytest
from django.core.cache import cache
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework.test import APIClient

from apps.utilisateurs.models import CodeOtp, Consentement, Utilisateur


TELEPHONE = "+237699123456"


@pytest.fixture
def client_api():
    return APIClient()


@pytest.fixture
def passerelle_sms():
    with patch("apps.utilisateurs.services.creer_passerelle_sms") as creer_passerelle:
        passerelle = creer_passerelle.return_value
        yield passerelle


def demander_code(client_api, telephone=TELEPHONE):
    return client_api.post(
        "/api/auth/demander-code/",
        {"telephone": telephone},
        format="json",
    )


def verifier_code(client_api, code, telephone=TELEPHONE):
    return client_api.post(
        "/api/auth/verifier-code/",
        {
            "telephone": telephone,
            "code": code,
            "version_consentement": "v1",
            "type_consentement": "conditions_utilisation",
        },
        format="json",
    )


@pytest.mark.django_db
def test_code_valide_cree_utilisateur_consentement_et_jetons(client_api, passerelle_sms):
    reponse_demande = demander_code(client_api)
    code = passerelle_sms.envoyer_code.call_args.args[1]
    otp = CodeOtp.objects.get(telephone=TELEPHONE)

    assert reponse_demande.status_code == 200
    assert len(code) == 6
    assert code.isdigit()
    assert check_password(code, otp.code_hash)
    assert code not in otp.code_hash

    reponse = verifier_code(client_api, code)

    assert reponse.status_code == 200
    assert reponse.data["acces"]
    assert reponse.data["rafraichissement"]
    assert Utilisateur.objects.filter(telephone=TELEPHONE).exists()
    assert Consentement.objects.filter(
        utilisateur__telephone=TELEPHONE,
        version_texte="v1",
    ).exists()
    assert otp.__class__.objects.get(pk=otp.pk).utilise is True


@pytest.mark.django_db
def test_code_incorrect_incremente_les_tentatives(client_api, passerelle_sms):
    demander_code(client_api)

    reponse = verifier_code(client_api, "000000")

    assert reponse.status_code == 400
    assert reponse.data["erreur"] == "Code incorrect."
    assert CodeOtp.objects.get(telephone=TELEPHONE).tentatives == 1
    assert not Utilisateur.objects.filter(telephone=TELEPHONE).exists()


@pytest.mark.django_db
def test_code_expire_est_refuse(client_api, passerelle_sms):
    demander_code(client_api)
    otp = CodeOtp.objects.get(telephone=TELEPHONE)
    otp.expiration = timezone.now() - timedelta(seconds=1)
    otp.save(update_fields=["expiration"])

    reponse = verifier_code(client_api, passerelle_sms.envoyer_code.call_args.args[1])

    assert reponse.status_code == 400
    assert "expire" in reponse.data["erreur"]
    assert CodeOtp.objects.get(pk=otp.pk).utilise is True


@pytest.mark.django_db
def test_cinquieme_erreur_bloque_le_code(client_api, passerelle_sms):
    demander_code(client_api)

    for numero_essai in range(5):
        reponse = verifier_code(client_api, "000000")

    otp = CodeOtp.objects.get(telephone=TELEPHONE)
    assert numero_essai == 4
    assert reponse.status_code == 429
    assert otp.tentatives == 5
    assert otp.utilise is True


@pytest.mark.django_db
def test_trop_de_demandes_est_limite_par_telephone(
    client_api,
    passerelle_sms,
    settings,
):
    settings.OTP_MAX_ENVOIS = 2
    settings.OTP_FENETRE_ENVOIS_SECONDES = 3600

    assert demander_code(client_api).status_code == 200
    assert demander_code(client_api).status_code == 200
    reponse = demander_code(client_api)

    assert reponse.status_code == 429
    assert reponse.data["erreur"] == "Trop de demandes. Reessayez plus tard."
    assert passerelle_sms.envoyer_code.call_count == 2


@pytest.mark.django_db
def test_format_telephone_invalide_est_refuse(client_api):
    reponse = demander_code(client_api, "699123456")

    assert reponse.status_code == 400
    assert not CodeOtp.objects.exists()


@pytest.mark.django_db
def test_compte_suspendu_ne_recoit_pas_de_jeton(client_api, passerelle_sms):
    Utilisateur.objects.create(telephone=TELEPHONE, statut=Utilisateur.Statut.SUSPENDU)
    demander_code(client_api)
    code = passerelle_sms.envoyer_code.call_args.args[1]

    reponse = verifier_code(client_api, code)

    assert reponse.status_code == 403
    assert "acces" not in reponse.data


@pytest.mark.django_db
def test_demande_code_est_limitee_par_adresse_ip(client_api, settings, passerelle_sms):
    cache.clear()
    configuration = dict(settings.REST_FRAMEWORK)
    configuration["DEFAULT_THROTTLE_RATES"] = {"otp_demande": "1/minute"}
    settings.REST_FRAMEWORK = configuration

    assert demander_code(client_api, "+237690000123").status_code == 200
    reponse = demander_code(client_api, "+237690000124")

    assert reponse.status_code == 429


@pytest.mark.django_db
def test_verification_code_est_limitee_par_adresse_ip(client_api, settings):
    cache.clear()
    configuration = dict(settings.REST_FRAMEWORK)
    configuration["DEFAULT_THROTTLE_RATES"] = {"otp_verification": "1/minute"}
    settings.REST_FRAMEWORK = configuration
    donnees = {
        "telephone": "+237690000125",
        "code": "123456",
        "version_consentement": "v1",
        "type_consentement": "conditions_utilisation",
    }

    assert client_api.post("/api/auth/verifier-code/", donnees, format="json").status_code == 400
    reponse = client_api.post("/api/auth/verifier-code/", donnees, format="json")

    assert reponse.status_code == 429