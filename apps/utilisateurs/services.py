import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from django.utils.module_loading import import_string
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CodeOtp, Consentement, Utilisateur


class ErreurAuthentification(Exception):
    def __init__(self, message, statut_http=400):
        self.message = message
        self.statut_http = statut_http
        super().__init__(message)


def creer_passerelle_sms():
    return import_string(settings.PASSERELLE_SMS)()


def demander_code(telephone):
    maintenant = timezone.now()
    debut_fenetre = maintenant - timedelta(seconds=settings.OTP_FENETRE_ENVOIS_SECONDES)
    nombre_envois = CodeOtp.objects.filter(telephone=telephone, cree_le__gte=debut_fenetre).count()
    if nombre_envois >= settings.OTP_MAX_ENVOIS:
        raise ErreurAuthentification("Trop de demandes. Reessayez plus tard.", 429)

    code = f"{secrets.randbelow(1_000_000):06d}"
    otp = CodeOtp.objects.create(
        telephone=telephone,
        code_hash=make_password(code),
        expiration=maintenant + timedelta(minutes=settings.OTP_DUREE_MINUTES),
    )
    creer_passerelle_sms().envoyer_code(telephone, code)
    return otp


def verifier_code(telephone, code, version_consentement, type_consentement):
    otp = CodeOtp.objects.filter(telephone=telephone, utilise=False).order_by("-expiration").first()
    if otp is None:
        raise ErreurAuthentification("Code invalide ou deja utilise.")

    maintenant = timezone.now()
    if otp.expiration <= maintenant:
        otp.utilise = True
        otp.save(update_fields=["utilise"])
        raise ErreurAuthentification("Le code a expire. Demandez-en un nouveau.")

    if otp.tentatives >= settings.OTP_MAX_ESSAIS:
        otp.utilise = True
        otp.save(update_fields=["utilise"])
        raise ErreurAuthentification("Nombre maximum d'essais atteint.", 429)

    if not check_password(code, otp.code_hash):
        otp.tentatives += 1
        if otp.tentatives >= settings.OTP_MAX_ESSAIS:
            otp.utilise = True
        otp.save(update_fields=["tentatives", "utilise"])
        if otp.utilise:
            raise ErreurAuthentification("Nombre maximum d'essais atteint.", 429)
        raise ErreurAuthentification("Code incorrect.")

    otp.utilise = True
    otp.save(update_fields=["utilise"])
    utilisateur, _ = Utilisateur.objects.get_or_create(telephone=telephone)
    if not utilisateur.is_active or utilisateur.statut != Utilisateur.Statut.ACTIF:
        raise ErreurAuthentification("Ce compte est suspendu.", 403)
    Consentement.objects.get_or_create(
        utilisateur=utilisateur,
        type_consentement=type_consentement,
        version_texte=version_consentement,
    )
    jeton_rafraichissement = RefreshToken.for_user(utilisateur)
    return {
        "acces": str(jeton_rafraichissement.access_token),
        "rafraichissement": str(jeton_rafraichissement),
        "utilisateur": {
            "id": utilisateur.pk,
            "telephone": utilisateur.telephone,
            "nom": utilisateur.nom,
            "ville": utilisateur.ville,
            "langue": utilisateur.langue,
            "statut": utilisateur.statut,
        },
    }