import hashlib
import hmac
from datetime import timedelta

from django.utils import timezone

from apps.tontines.models import Adhesion, Cycle

from .models import Cotisation, Paiement, Penalite


def calculer_montant_du(mains, montant_cotisation, penalite_reportee):
    """Calcule le montant total dû pour un membre.

    Le montant dû est le nombre de mains multiplié par le montant de la cotisation de la
    tontine, puis ajoute la pénalité reportée du cycle précédent. La formule est pure : elle
    ne dépend que des paramètres fournis et est facile à tester.
    """
    if mains < 0:
        raise ValueError("Le nombre de mains ne peut pas etre negatif.")
    if montant_cotisation < 0:
        raise ValueError("Le montant de cotisation ne peut pas etre negatif.")
    if penalite_reportee < 0:
        raise ValueError("La penalite reportee ne peut pas etre negative.")
    return int(mains) * int(montant_cotisation) + int(penalite_reportee)


def calculer_penalite_retard(jours_retard, regle):
    """Retourne le montant de la pénalité pour un retard donné."""
    jours_grace = int(regle.get("jours_de_grace", 0))
    if jours_retard <= jours_grace:
        return 0

    if regle.get("type") == "pourcentage":
        valeur = float(regle.get("valeur", 0))
        return int(valeur)

    return int(regle.get("montant", 0))


def calculer_penalite_absence(montant_du, regle):
    """Retourne le montant d'une pénalité d'absence."""
    if regle.get("type") == "pourcentage":
        valeur = float(regle.get("valeur", 0))
        return int((montant_du * valeur) / 100)
    return int(regle.get("montant", 0))


def appliquer_penalites(cycle, aujourdhui):
    """Crée les pénalités manquantes pour un cycle sans duplication."""
    regles = cycle.tontine.regles_penalite or {}
    for cotisation in cycle.cotisations.select_related("adhesion").all():
        if cotisation.statut == Cotisation.Statut.PAYE:
            continue

        if cotisation.statut == Cotisation.Statut.ABSENT:
            regle = regles.get("absence", {})
            if not regle:
                continue
            montant = calculer_penalite_absence(cotisation.montant_du, regle)
            Penalite.objects.get_or_create(
                cotisation=cotisation,
                type="absence",
                defaults={
                    "montant": montant,
                    "regle_appliquee": regle,
                    "motif": "absence",
                },
            )
            continue

        if cotisation.statut in {Cotisation.Statut.EN_RETARD, Cotisation.Statut.PARTIEL}:
            regle = regles.get("retard", {})
            if not regle:
                continue
            jours_retard = (aujourdhui - cycle.date_limite).days
            montant = calculer_penalite_retard(jours_retard, regle)
            if montant <= 0:
                continue
            Penalite.objects.get_or_create(
                cotisation=cotisation,
                type="retard",
                defaults={
                    "montant": montant,
                    "regle_appliquee": regle,
                    "motif": "retard",
                },
            )

    return cycle.cotisations.count()


def valider_beneficiaire_possible(adhesion, cycle):
    if adhesion.mains <= 0:
        raise ValueError("Une adhesion doit avoir au moins une main.")
    if cycle.beneficiaire_id is not None and cycle.beneficiaire_id != adhesion.utilisateur_id:
        if cycle.statut in {Cycle.Statut.OUVERT, Cycle.Statut.TERMINE}:
            raise ValueError("L'ordre est verrouille et ne peut plus etre change.")
    if cycle.montant_offert > 0 and cycle.interet_distribue > 0:
        raise ValueError("Un cycle ne peut pas avoir a la fois un beneficiaire d'ordre fixe et une enchere.")
    return True


def calculer_code_verification(identifiant, montant, horodatage, cle_secrete):
    message = f"{identifiant}|{montant}|{horodatage}"
    digest = hmac.new(cle_secrete.encode("utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return digest[:6].upper()


def calculer_solde(adhesion):
    total_cotisations = sum(c.montant_paye for c in adhesion.cotisations.all())
    total_paiements = sum(p.montant for p in Paiement.objects.filter(cotisation__adhesion=adhesion))
    return int(total_cotisations + total_paiements)


def generer_cycles(tontine, nombre_cycles=1):
    """Crée les cycles et les cotisations pour une tontine."""
    cycles = []
    for numero in range(1, nombre_cycles + 1):
        cycle, cree = Cycle.objects.get_or_create(
            tontine=tontine,
            numero=numero,
            defaults={
                "date_limite": tontine.date_debut + (timedelta(days=30) if tontine.frequence == "mensuelle" else timedelta(days=7)),
                "montant_a_verser": tontine.montant_cotisation,
                "statut": Cycle.Statut.OUVERT,
            },
        )
        if cree:
            cycle.montant_a_verser = tontine.montant_cotisation
            cycle.save(update_fields=["montant_a_verser", "statut", "date_limite"])

        for adhesion in tontine.adhesions.filter(statut="actif"):
            valider_beneficiaire_possible(adhesion, cycle)
            Cotisation.objects.get_or_create(
                cycle=cycle,
                adhesion=adhesion,
                defaults={
                    "montant_du": calculer_montant_du(adhesion.mains, tontine.montant_cotisation, 0),
                    "montant_paye": 0,
                    "statut": Cotisation.Statut.ABSENT,
                },
            )
        cycles.append(cycle)
    return cycles
