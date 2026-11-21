import pytest
from django.utils import timezone

from apps.audit.models import Contestation, JournalAudit
from apps.audit.services import creer_contestation, repondre_contestation
from apps.finances.models import Cotisation, Paiement
from apps.tontines.models import Adhesion, Cycle, Tontine
from apps.utilisateurs.models import Utilisateur


@pytest.fixture
def contexte_contestation():
    president = Utilisateur.objects.create(telephone="+237690000111")
    tresorier = Utilisateur.objects.create(telephone="+237690000222")
    membre = Utilisateur.objects.create(telephone="+237690000333")
    tontine = Tontine.objects.create(
        nom="Tontine audit",
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
        statut=Cotisation.Statut.EN_RETARD,
    )
    paiement = Paiement.objects.create(
        cotisation=cotisation,
        montant=5000,
        mode=Paiement.Mode.CASH,
        reference_transaction="ref-audit-1",
        enregistre_par=tresorier,
        code_verification="AUD123",
    )
    return tontine, adhesion_membre, president, tresorier, paiement


@pytest.mark.django_db
def test_un_membre_peut_contester_une_ecriture_qui_le_concerne(contexte_contestation):
    tontine, adhesion_membre, _, _, paiement = contexte_contestation

    contestation = creer_contestation(
        adhesion=adhesion_membre,
        type_objet="paiement",
        id_objet=paiement.id,
        motif="montant incorrect",
        utilisateur=adhesion_membre.utilisateur,
    )

    assert contestation.statut == Contestation.Statut.OUVERTE
    assert contestation.adhesion == adhesion_membre
    assert contestation.type_objet == "paiement"


@pytest.mark.django_db
def test_un_autre_membre_ne_peut_pas_contester(contexte_contestation):
    tontine, _, _, _, paiement = contexte_contestation
    autre_adhesion = Adhesion.objects.create(
        utilisateur=Utilisateur.objects.create(telephone="+237690000444"),
        tontine=tontine,
        role="membre",
        mains=1,
        statut="actif",
    )

    with pytest.raises(PermissionError):
        creer_contestation(
            adhesion=autre_adhesion,
            type_objet="paiement",
            id_objet=paiement.id,
            motif="pas concerne",
            utilisateur=autre_adhesion.utilisateur,
        )


@pytest.mark.django_db
def test_la_contestation_ne_modifie_pas_l_ecriture_origine(contexte_contestation):
    _, adhesion_membre, _, _, paiement = contexte_contestation
    ancien_montant = paiement.montant

    contestation = creer_contestation(
        adhesion=adhesion_membre,
        type_objet="paiement",
        id_objet=paiement.id,
        motif="montant incorrect",
        utilisateur=adhesion_membre.utilisateur,
    )

    paiement.refresh_from_db()
    assert paiement.montant == ancien_montant
    assert contestation.type_objet == "paiement"


@pytest.mark.django_db
def test_l_audit_trace_chaque_action(contexte_contestation):
    _, adhesion_membre, _, tresorier, paiement = contexte_contestation

    contestation = creer_contestation(
        adhesion=adhesion_membre,
        type_objet="paiement",
        id_objet=paiement.id,
        motif="montant incorrect",
        utilisateur=adhesion_membre.utilisateur,
    )
    repondre_contestation(contestation, "ok", tresorier)

    assert JournalAudit.objects.filter(objet="contestation").count() >= 2
