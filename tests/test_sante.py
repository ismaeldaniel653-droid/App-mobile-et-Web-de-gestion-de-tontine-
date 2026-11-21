import pytest
from django.urls import reverse
from rest_framework.test import APIClient


@pytest.mark.django_db
def test_sante_renvoie_statut_ok():
    client = APIClient()

    reponse = client.get(reverse("sante"))

    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}