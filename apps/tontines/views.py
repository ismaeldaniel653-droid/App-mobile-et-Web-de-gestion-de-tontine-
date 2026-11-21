from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import UserRateThrottle
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.utilisateurs.models import Utilisateur

from .models import Adhesion, Invitation, Tontine
from .permissions import PermissionRoleTontine
from .serializers import (
    AdhesionSerializer,
    ChangerRoleSerializer,
    CreationTontineSerializer,
    InvitationSerializer,
    RejoindreTontineSerializer,
    TontineSerializer,
)
from .services import (
    changer_role_membre,
    creer_invitation_tontine,
    creer_tontine,
    lister_tontines_utilisateur,
    rejoindre_tontine_par_jeton,
)


from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers


class VueListeTontines(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    throttle_scope = "tontine_liste"

    @extend_schema(
        summary="Liste vos tontines",
        description="Retourne la liste de toutes les tontines dont vous êtes membre. L'isolation est garantie : vous ne voyez que vos tontines personnelles.",
        responses={
            200: TontineSerializer(many=True),
        }
    )
    def get(self, request):
        tontines = lister_tontines_utilisateur(request.user)
        serializer = TontineSerializer(tontines, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary="Créer une tontine",
        description="Le créateur de la tontine devient automatiquement président. La tontine est créée avec un cycle initial.",
        request=CreationTontineSerializer,
        responses={
            201: TontineSerializer,
            403: {"description": "Seul le président peut créer une tontine"},
        }
    )
    def post(self, request):
        serializer = CreationTontineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        tontine = creer_tontine(request.user, serializer.validated_data)
        return Response(TontineSerializer(tontine).data, status=status.HTTP_201_CREATED)


class VueDetailTontine(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    throttle_scope = "tontine_detail"

    @extend_schema(
        summary="Détail d'une tontine",
        description="Retourne les détails d'une tontine. Accessible uniquement si vous êtes membre de cette tontine. Test d'isolation : utilisateur d'une autre tontine reçoit 404.",
        responses={
            200: TontineSerializer,
            404: {"description": "Tontine non trouvée ou utilisateur non membre"},
        }
    )
    def get(self, request, pk):
        tontine = get_object_or_404(Tontine.objects.filter(adhesions__utilisateur=request.user), pk=pk)
        return Response(TontineSerializer(tontine).data)


class VueInvitationTontine(APIView):
    permission_classes = [IsAuthenticated, PermissionRoleTontine]
    role_requis = "president"
    throttle_classes = [UserRateThrottle]
    throttle_scope = "tontine_invitation"

    @extend_schema(
        summary="Inviter un membre",
        description="Le président d'une tontine peut inviter un nouveau membre. L'invitation contient un jeton valide pendant une période limitée. Test : un membre ne peut pas inviter (403).",
        request=InvitationSerializer,
        responses={
            201: InvitationSerializer,
            403: {"description": "Seul le président peut inviter"},
            400: {"description": "L'utilisateur est déjà membre ou l'invitation est invalide"},
        }
    )
    def post(self, request, tontine_id):
        tontine = get_object_or_404(Tontine, pk=tontine_id)
        self.check_object_permissions(request, tontine)
        try:
            invitation = creer_invitation_tontine(request.user, tontine, request.data.get("role_propose", "membre"))
        except PermissionError as erreur:
            return Response({"erreur": str(erreur)}, status=status.HTTP_403_FORBIDDEN)
        return Response(InvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)


class VueRejoindreTontine(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    throttle_scope = "tontine_rejoindre"

    @extend_schema(
        summary="Rejoindre une tontine",
        description="Rejoindre une tontine via un lien d'invitation valide. Le jeton doit être valide et non utilisé. Test : lien expiré ou déjà utilisé est refusé (400/404).",
        request=RejoindreTontineSerializer,
        responses={
            200: AdhesionSerializer,
            400: {"description": "Jeton expiré, déjà utilisé ou invalide"},
            404: {"description": "Tontine introuvable"},
        }
    )
    def post(self, request):
        serializer = RejoindreTontineSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            adhesion = rejoindre_tontine_par_jeton(request.user, serializer.validated_data["jeton"])
        except ValueError as erreur:
            return Response({"erreur": str(erreur)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(AdhesionSerializer(adhesion).data, status=status.HTTP_200_OK)


class VueChangerRoleMembre(APIView):
    permission_classes = [IsAuthenticated, PermissionRoleTontine]
    role_requis = "president"
    throttle_classes = [UserRateThrottle]
    throttle_scope = "tontine_changer_role"

    @extend_schema(
        summary="Changer le rôle d'un membre",
        description="Le président d'une tontine peut changer le rôle d'un autre membre (president, tresorier, membre). Le membre cible doit appartenir à la même tontine. Test : membre d'une autre tontine reçoit 403.",
        request=ChangerRoleSerializer,
        responses={
            200: AdhesionSerializer,
            403: {"description": "Membre cible n'appartient pas à la tontine ou rôle interdit"},
        }
    )
    def patch(self, request, tontine_id, utilisateur_id):
        tontine = get_object_or_404(Tontine, pk=tontine_id)
        self.check_object_permissions(request, tontine)
        membre = get_object_or_404(Utilisateur, pk=utilisateur_id)
        serializer = ChangerRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        adhesion = get_object_or_404(Adhesion, tontine=tontine, utilisateur=membre)
        adhesion = changer_role_membre(tontine, membre, serializer.validated_data["role"])
        return Response(AdhesionSerializer(adhesion).data, status=status.HTTP_200_OK)
