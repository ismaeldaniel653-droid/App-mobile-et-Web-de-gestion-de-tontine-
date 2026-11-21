from datetime import timedelta

import pytest
from django.utils import timezone

from apps.finances.models import Cotisation, Penalite
from apps.finances.services import (
    appliquer_penalites,
    calculer_penalite_absence,
    calculer_penalite_retard,
)
from apps.tontines.models import Adhesion, Cycle, Tontine
from apps.utilisateurs.models import Utilisateur


@pytest.fixture
def contexte_penalites():
    president = Utilisateur.objects.create(telephone="+237690000111")
    tontine = Tontine.objects.create(
        nom="Tontine penalites",
        montant_cotisation=5000,
        frequence="mensuelle",
        nombre_mains_total=2,
        mode_passage="ordre_fixe",
        pourcentage_reserve=10,
        date_debut=timezone.now().date(),
        cree_par=president,
        regles_penalite={
            "retard": {"jours_de_grace": 1, "type": "fixe", "montant": 500},
            "absence": {"type": "pourcentage", "valeur": 10},
        },
    )
    adhesion = Adhesion.objects.create(utilisateur=president, tontine=tontine, role="president", mains=1, statut="actif")
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
    return tontine, cycle, cotisation


@pytest.mark.django_db
@pytest.mark.parametrize(
    "jours_retard,regle,expected",
    [
        (0, {"jours_de_grace": 1, "type": "fixe", "montant": 500}, 0),
        (1, {"jours_de_grace": 1, "type": "fixe", "montant": 500}, 0),
        (2, {"jours_de_grace": 1, "type": "fixe", "montant": 500}, 500),
        (7, {"jours_de_grace": 3, "type": "fixe", "montant": 200}, 200),
    ],
)
def test_calculer_penalite_retard(jours_retard, regle, expected):
    montant = calculer_penalite_retard(jours_retard, regle)
    assert montant == expected


@pytest.mark.django_db
@pytest.mark.parametrize(
    "montant_du,regle,expected",
    [
        (5000, {"type": "pourcentage", "valeur": 10}, 500),
        (5000, {"type": "fixe", "montant": 300}, 300),
        (10000, {"type": "pourcentage", "valeur": 12}, 1200),
    ],
)
def test_calculer_penalite_absence(montant_du, regle, expected):
    montant = calculer_penalite_absence(montant_du, regle)
    assert montant == expected


@pytest.mark.django_db
def test_appliquer_penalites_cree_une_penalite_manquante(contexte_penalites):
    _, cycle, cotisation = contexte_penalites
    assert Penalite.objects.filter(cotisation=cotisation).count() == 0

    appliquer_penalites(cycle, timezone.now().date())

    assert Penalite.objects.filter(cotisation=cotisation, type="retard").count() == 1


@pytest.mark.django_db
def test_appliquer_penalites_est_idempotent(contexte_penalites):
    _, cycle, _ = contexte_penalites

    appliquer_penalites(cycle, timezone.now().date())
    appliquer_penalites(cycle, timezone.now().date())

    assert Penalite.objects.filter(cotisation__cycle=cycle).count() == 1


@pytest.mark.django_db
def test_appliquer_penalites_copie_la_regle_utilisee(contexte_penalites):
    _, cycle, cotisation = contexte_penalites

    appliquer_penalites(cycle, timezone.now().date())

    penalite = Penalite.objects.get(cotisation=cotisation, type="retard")
    assert penalite.regle_appliquee == {"jours_de_grace": 1, "type": "fixe", "montant": 500}


@pytest.mark.django_db
def test_appliquer_penalites_ne_modifie_pas_une_penalite_ancienne(contexte_penalites):
    _, cycle, cotisation = contexte_penalites
    ancienne = Penalite.objects.create(
        cotisation=cotisation,
        type="retard",
        montant=100,
        regle_appliquee={"jours_de_grace": 0, "type": "fixe", "montant": 100},
        motif="ancienne_regle",
    )

    cycle.tontine.regles_penalite = {"retard": {"jours_de_grace": 1, "type": "fixe", "montant": 500}}
    cycle.tontine.save(update_fields=["regles_penalite"])
    appliquer_penalites(cycle, timezone.now().date())

    ancienne.refresh_from_db()
    assert ancienne.montant == 100
    assert ancienne.regle_appliquee == {"jours_de_grace": 0, "type": "fixe", "montant": 100}


@pytest.mark.django_db
def test_appliquer_penalites_avec_absence_cree_une_penalite_absence(contexte_penalites):
    _, cycle, cotisation = contexte_penalites
    cotisation.statut = Cotisation.Statut.ABSENT
    cotisation.save(update_fields=["statut"])

    appliquer_penalites(cycle, timezone.now().date())

    assert Penalite.objects.filter(cotisation=cotisation, type="absence").count() == 1


@pytest.mark.django_db
def test_appliquer_penalites_avec_cotisation_payee_ne_cree_rien(contexte_penalites):
    _, cycle, cotisation = contexte_penalites
    cotisation.statut = Cotisation.Statut.PAYE
    cotisation.save(update_fields=["statut"])

    appliquer_penalites(cycle, timezone.now().date())

    assert Penalite.objects.filter(cotisation__cycle=cycle).count() == 0
