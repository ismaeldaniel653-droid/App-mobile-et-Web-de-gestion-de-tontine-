import uuid
from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from apps.utilisateurs.models import Utilisateur

from .models import Adhesion, Invitation, Tontine


class TontineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tontine
        fields = [
            "id",
            "nom",
            "montant_cotisation",
            "frequence",
            "nombre_mains_total",
            "mode_passage",
            "pourcentage_reserve",
            "date_debut",
            "statut",
            "regles_penalite",
            "cree_par",
        ]
        read_only_fields = ["id", "cree_par"]


class CreationTontineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tontine
        fields = [
            "nom",
            "montant_cotisation",
            "frequence",
            "nombre_mains_total",
            "mode_passage",
            "pourcentage_reserve",
            "date_debut",
        ]


class InvitationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ["id", "tontine", "jeton", "role_propose", "expire_le", "usage_unique", "utilise_par"]
        read_only_fields = ["id", "jeton", "utilise_par"]

    def create(self, validated_data):
        validated_data["jeton"] = str(uuid.uuid4())
        validated_data["expire_le"] = timezone.now() + timedelta(days=7)
        return super().create(validated_data)


class RejoindreTontineSerializer(serializers.Serializer):
    jeton = serializers.CharField(max_length=64)


class ChangerRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=Adhesion.Role.choices)


class AdhesionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Adhesion
        fields = ["id", "utilisateur", "tontine", "role", "mains", "statut"]
        read_only_fields = ["id", "utilisateur", "tontine"]
