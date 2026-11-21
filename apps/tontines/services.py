from datetime import timedelta

from django.utils import timezone

from .models import Adhesion, Invitation, Tontine


def creer_tontine(utilisateur, donnees):
    tontine = Tontine.objects.create(cree_par=utilisateur, **donnees)
    Adhesion.objects.create(utilisateur=utilisateur, tontine=tontine, role="president", mains=tontine.nombre_mains_total, statut="actif")
    return tontine


def lister_tontines_utilisateur(utilisateur):
    return Tontine.objects.filter(adhesions__utilisateur=utilisateur).distinct()


def creer_invitation_tontine(utilisateur, tontine, role_propose):
    adhesion = Adhesion.objects.filter(utilisateur=utilisateur, tontine=tontine).first()
    if adhesion is None or adhesion.role != "president":
        raise PermissionError("Seul le president peut inviter.")
    return Invitation.objects.create(
        tontine=tontine,
        jeton=str(__import__("uuid").uuid4()),
        role_propose=role_propose,
        expire_le=timezone.now() + timedelta(days=7),
        usage_unique=True,
    )


def rejoindre_tontine_par_jeton(utilisateur, jeton):
    invitation = Invitation.objects.filter(jeton=jeton).first()
    if invitation is None:
        raise ValueError("Lien invalide.")
    if invitation.expire_le <= timezone.now():
        raise ValueError("Lien expire.")
    if invitation.usage_unique and invitation.utilise_par is not None:
        raise ValueError("Lien deja utilise.")
    if Adhesion.objects.filter(utilisateur=utilisateur, tontine=invitation.tontine).exists():
        raise ValueError("Vous etes deja membre.")

    adhesion = Adhesion.objects.create(
        utilisateur=utilisateur,
        tontine=invitation.tontine,
        role=invitation.role_propose,
        mains=1,
        statut="actif",
    )
    if invitation.usage_unique:
        invitation.utilise_par = utilisateur
        invitation.save(update_fields=["utilise_par"])
    return adhesion


def changer_role_membre(tontine, membre, nouveau_role):
    adhesion = Adhesion.objects.get(tontine=tontine, utilisateur=membre)
    adhesion.role = nouveau_role
    adhesion.save(update_fields=["role"])
    return adhesion
