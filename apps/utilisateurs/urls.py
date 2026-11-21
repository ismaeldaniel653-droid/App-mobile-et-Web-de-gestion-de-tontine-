from django.urls import path

from .views import VueDemanderCode, VueVerifierCode

urlpatterns = [
    path("demander-code/", VueDemanderCode.as_view(), name="demander_code"),
    path("verifier-code/", VueVerifierCode.as_view(), name="verifier_code"),
]