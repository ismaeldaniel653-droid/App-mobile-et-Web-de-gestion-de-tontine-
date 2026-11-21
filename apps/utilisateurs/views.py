from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import DemandeCodeSerializer, VerificationCodeSerializer
from .services import ErreurAuthentification, demander_code, verifier_code


class VueDemanderCode(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "otp_demande"

    @extend_schema(
        request=DemandeCodeSerializer,
        responses={
            200: inline_serializer(
                name="ReponseDemandeCode",
                fields={"statut": serializers.CharField()},
            ),
            400: inline_serializer(
                name="ErreurDemandeCode",
                fields={"erreur": serializers.CharField()},
            ),
            429: inline_serializer(
                name="LimiteDemandeCode",
                fields={"erreur": serializers.CharField()},
            ),
        },
        description="Envoie un code de connexion par SMS au numero fourni. Limite par numero et adresse IP.",
        examples=[
            OpenApiExample(
                "Demande de code",
                value={"telephone": "+237690000123"},
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = DemandeCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            demander_code(serializer.validated_data["telephone"])
        except ErreurAuthentification as erreur:
            return Response({"erreur": erreur.message}, status=erreur.statut_http)
        return Response({"statut": "code_envoye"})


class VueVerifierCode(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "otp_verification"

    @extend_schema(
        request=VerificationCodeSerializer,
        responses={
            200: inline_serializer(
                name="ReponseVerificationCode",
                fields={
                    "acces": serializers.CharField(),
                    "rafraichissement": serializers.CharField(),
                    "utilisateur": inline_serializer(
                        name="UtilisateurAuthentifie",
                        fields={
                            "id": serializers.IntegerField(),
                            "telephone": serializers.CharField(),
                            "nom": serializers.CharField(),
                            "ville": serializers.CharField(),
                            "langue": serializers.CharField(),
                            "statut": serializers.CharField(),
                        },
                    ),
                },
            ),
            400: inline_serializer(
                name="ErreurVerificationCode",
                fields={"erreur": serializers.CharField()},
            ),
            429: inline_serializer(
                name="LimiteVerificationCode",
                fields={"erreur": serializers.CharField()},
            ),
            403: inline_serializer(
                name="CompteSuspendu",
                fields={"erreur": serializers.CharField()},
            ),
        },
        description="Verifie le code, enregistre le consentement et renvoie les jetons JWT. Un compte inactif ou suspendu est refuse.",
        examples=[
            OpenApiExample(
                "Verification du code",
                value={
                    "telephone": "+237690000123",
                    "code": "123456",
                    "version_consentement": "v1",
                    "type_consentement": "conditions_utilisation",
                },
                request_only=True,
            )
        ],
    )
    def post(self, request):
        serializer = VerificationCodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            resultat = verifier_code(**serializer.validated_data)
        except ErreurAuthentification as erreur:
            return Response({"erreur": erreur.message}, status=erreur.statut_http)
        return Response(resultat, status=status.HTTP_200_OK)