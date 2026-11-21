from django.db import transaction

from apps.finances.models import Paiement
from apps.tontines.models import Adhesion

from .models import Contestation, JournalAudit


def journaliser(action, objet, utilisateur=None, ancienne_valeur="", nouvelle_valeur=""):
    JournalAudit.objects.create(
        utilisateur=utilisateur,
        action=action,
        objet=objet,
        ancienne_valeur=str(ancienne_valeur),
        nouvelle_valeur=str(nouvelle_valeur),
    )


def creer_contestation(adhesion, type_objet, id_objet, motif, utilisateur):
    if adhesion.utilisateur_id != utilisateur.id:
        raise PermissionError("Seul le membre concerné peut contester une écriture.")

    objet = None
    if type_objet == "paiement":
        objet = Paiement.objects.filter(pk=id_objet, cotisation__adhesion__tontine=adhesion.tontine).first()

    if objet is None:
        raise ValueError("Objet de contestation introuvable.")

    if type_objet == "paiement" and objet.cotisation.adhesion_id != adhesion.id:
        raise PermissionError("Seul le membre concerné peut contester une écriture.")

    contestation = Contestation.objects.create(
        adhesion=adhesion,
        type_objet=type_objet,
        id_objet=id_objet,
        motif=motif,
        statut=Contestation.Statut.OUVERTE,
    )
    journaliser(
        "creation_contestation",
        "contestation",
        utilisateur=utilisateur,
        ancienne_valeur="",
        nouvelle_valeur=f"{contestation.id}",
    )
    return contestation


def repondre_contestation(contestation, reponse, utilisateur):
    adhesion = Adhesion.objects.filter(utilisateur=utilisateur, tontine=contestation.adhesion.tontine).first()
    if adhesion is None or adhesion.role not in {"president", "tresorier"}:
        raise PermissionError("Seul le président ou le trésorier peut répondre.")

    with transaction.atomic():
        ancienne = contestation.statut
        contestation.statut = Contestation.Statut.TRAITEE
        contestation.traitee_par = utilisateur
        contestation.save(update_fields=["statut", "traitee_par"])
        journaliser(
            "reponse_contestation",
            "contestation",
            utilisateur=utilisateur,
            ancienne_valeur=ancienne,
            nouvelle_valeur=reponse,
        )
    return contestation
