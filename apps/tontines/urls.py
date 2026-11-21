from django.urls import path

from .views import (
    VueChangerRoleMembre,
    VueDetailTontine,
    VueInvitationTontine,
    VueListeTontines,
    VueRejoindreTontine,
)

urlpatterns = [
    path("tontines/", VueListeTontines.as_view(), name="tontines_liste"),
    path("tontines/<int:pk>/", VueDetailTontine.as_view(), name="tontine_detail"),
    path("tontines/<int:tontine_id>/inviter/", VueInvitationTontine.as_view(), name="tontine_invitation"),
    path("tontines/rejoindre/", VueRejoindreTontine.as_view(), name="rejoindre_tontine"),
    path("tontines/<int:tontine_id>/membres/<int:utilisateur_id>/role/", VueChangerRoleMembre.as_view(), name="changer_role_membre"),
]
