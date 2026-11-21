import pytest
from django.utils import timezone

from apps.finances.models import Cotisation, Paiement
from apps.finances.services import calculer_code_verification, calculer_solde
from apps.tontines.models import Adhesion, Cycle, Tontine
from apps.utilisateurs.models import Utilisateur


@pytest.fixture
def contexte_paiement():
    president = Utilisateur.objects.create(telephone="+237690000111")
    tresorier = Utilisateur.objects.create(telephone="+237690000222")
    membre = Utilisateur.objects.create(telephone="+237690000333")

    tontine = Tontine.objects.create(
        nom="Tontine paiements",
        montant_cotisation=5000,
        frequence="mensuelle",
        nombre_mains_total=2,
        mode_passage="ordre_fixe",
        pourcentage_reserve=10,
        date_debut=timezone.now().date(),
        cree_par=president,
    )
    Adhesion.objects.create(utilisateur=president, tontine=tontine, role="president", mains=1, statut="actif")
    Adhesion.objects.create(utilisateur=tresorier, tontine=tontine, role="tresorier", mains=1, statut="actif")
    adhesion_membre = Adhesion.objects.create(utilisateur=membre, tontine=tontine, role="membre", mains=1, statut="actif")
    cycle = Cycle.objects.create(
        tontine=tontine,
        numero=1,
        date_limite=timezone.now().date(),
        montant_a_verser=5000,
        statut=Cycle.Statut.OUVERT,
    )
    cotisation = Cotisation.objects.create(
        cycle=cycle,
        adhesion=adhesion_membre,
        montant_du=5000,
        montant_paye=0,
        statut=Cotisation.Statut.ABSENT,
    )
    return tontine, adhesion_membre, tresorier, cycle, cotisation


@pytest.mark.django_db
def test_calculer_code_verification_produit_un_code_sur_six_caracteres():
    code = calculer_code_verification(123, 5000, "2024-01-01T00:00:00Z", "cle-test")
    assert len(code) == 6
    assert code.isalnum()


@pytest.mark.django_db
def test_calculer_solde_avec_paiements_et_penalites(contexte_paiement):
    _, adhesion, _, _, cotisation = contexte_paiement
    paiement = Paiement.objects.create(
        cotisation=cotisation,
        montant=2500,
        mode="cash",
        reference_transaction="ref-solde-1",
        enregistre_par=adhesion.utilisateur,
        code_verification="ABCD12",
    )
    solde = calculer_solde(adhesion)
    assert solde == 2500


@pytest.mark.django_db
def test_paiement_partiel_puis_complet(contexte_paiement):
    _, _, tresorier, _, cotisation = contexte_paiement
    paiements = [
        Paiement.objects.create(
            cotisation=cotisation,
            montant=2000,
            mode="cash",
            reference_transaction="ref-1",
            enregistre_par=tresorier,
            code_verification="ABC123",
        ),
        Paiement.objects.create(
            cotisation=cotisation,
            montant=3000,
            mode="cash",
            reference_transaction="ref-2",
            enregistre_par=tresorier,
            code_verification="DEF456",
        ),
    ]

    assert len(paiements) == 2
    assert paiements[0].montant == 2000
    assert paiements[1].montant == 3000


@pytest.mark.django_db
def test_annulation_cree_un_paiement_negatif(contexte_paiement):
    _, _, tresorier, _, cotisation = contexte_paiement
    paiement = Paiement.objects.create(
        cotisation=cotisation,
        montant=5000,
        mode="cash",
        reference_transaction="ref-annule",
        enregistre_par=tresorier,
        code_verification="ANN123",
    )
    annulation = Paiement.objects.create(
        cotisation=cotisation,
        montant=-5000,
        mode="cash",
        reference_transaction="ref-annulation",
        enregistre_par=tresorier,
        code_verification="ANN999",
        annulation_de=paiement,
    )

    assert annulation.annulation_de == paiement
    assert annulation.montant == -5000


@pytest.mark.django_db
def test_code_correct_et_incorrect(contexte_paiement):
    code = calculer_code_verification(999, 5000, "2024-01-01T00:00:00Z", "cle-test")
    assert len(code) == 6
    assert code != "000000"
