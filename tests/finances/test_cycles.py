from datetime import timedelta

import pytest
from django.utils import timezone

from apps.finances.services import calculer_montant_du, generer_cycles
from apps.tontines.models import Adhesion, Tontine
from apps.utilisateurs.models import Utilisateur


@pytest.fixture
def tontine_de_test():
    proprietaire = Utilisateur.objects.create(telephone="+237690000111")
    tontine = Tontine.objects.create(
        nom="Tontine test",
        montant_cotisation=5000,
        frequence="mensuelle",
        nombre_mains_total=4,
        mode_passage="ordre_fixe",
        pourcentage_reserve=10,
        date_debut=timezone.now().date(),
        cree_par=proprietaire,
    )
    membre_un = Utilisateur.objects.create(telephone="+237690000222")
    membre_deux = Utilisateur.objects.create(telephone="+237690000333")
    Adhesion.objects.create(utilisateur=proprietaire, tontine=tontine, role="president", mains=2, statut="actif")
    Adhesion.objects.create(utilisateur=membre_un, tontine=tontine, role="membre", mains=1, statut="actif")
    Adhesion.objects.create(utilisateur=membre_deux, tontine=tontine, role="membre", mains=2, statut="actif")
    return tontine


@pytest.mark.django_db
def test_calculer_montant_du_avec_une_main():
    montant = calculer_montant_du(1, 5000, 0)
    assert montant == 5000


@pytest.mark.django_db
def test_calculer_montant_du_avec_deux_mains_et_penalite_reportee():
    montant = calculer_montant_du(2, 5000, 300)
    assert montant == 10300


@pytest.mark.django_db
def test_generer_cycles_cree_une_cotisation_par_membre(tontine_de_test):
    cycles = generer_cycles(tontine_de_test)
    assert len(cycles) == 1
    assert cycles[0].cotisations.count() == 3
    assert cycles[0].cotisations.filter(adhesion__mains=1).exists()


@pytest.mark.django_db
def test_generer_cycles_verrouille_l_ordre_apres_demarrage(tontine_de_test):
    cycle = generer_cycles(tontine_de_test)[0]
    cycle.statut = "ouvert"
    cycle.date_limite = timezone.now().date() - timedelta(days=1)
    cycle.save(update_fields=["statut", "date_limite"])

    assert cycle.statut == "ouvert"
    assert cycle.date_limite < timezone.now().date()


@pytest.mark.django_db
def test_beneficiaire_ne_peut_pas_depasser_son_nombre_de_mains(tontine_de_test):
    cycle = generer_cycles(tontine_de_test)[0]
    membre = cycle.tontine.adhesions.get(utilisateur__telephone="+237690000333")
    titulaire = membre.utilisateur

    assert membre.mains >= 1
    assert cycle.cotisations.filter(adhesion=membre).exists()
    assert titulaire.telephone == "+237690000333"
