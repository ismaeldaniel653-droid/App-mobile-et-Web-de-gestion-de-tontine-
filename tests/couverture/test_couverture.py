import pytest

from apps.couverture.services import (
    calculer_contribution_reserve,
    calculer_couverture,
)


@pytest.mark.parametrize(
    "montant_encaisse,pourcentage,expected",
    [
        (1000, 10, 100),
        (2500, 20, 500),
        (999, 15, 149),
    ],
)
def test_calculer_contribution_reserve(montant_encaisse, pourcentage, expected):
    assert calculer_contribution_reserve(montant_encaisse, pourcentage) == expected


@pytest.mark.parametrize(
    "montant_manquant,solde_reserve,membres,mode_repartition,expected",
    [
        (1000, 300, [1, 1, 1], "egal", [234, 233, 233]),
        (1000, 0, [2, 1], "selon_mains", [667, 333]),
        (1500, 500, [1, 1], "egal", [500, 500]),
    ],
)
def test_calculer_couverture(montant_manquant, solde_reserve, membres, mode_repartition, expected):
    resultat = calculer_couverture(montant_manquant, solde_reserve, membres, mode_repartition)
    assert resultat == expected


def test_calculer_couverture_reserve_pleine():
    resultat = calculer_couverture(500, 800, [2, 1], "egal")
    assert resultat == [0, 0]


def test_calculer_couverture_tout_est_pris_dans_reserve():
    resultat = calculer_couverture(200, 300, [3, 3], "egal")
    assert resultat == [0, 0]
