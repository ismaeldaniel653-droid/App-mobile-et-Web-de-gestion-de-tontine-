from rest_framework import serializers

from .models import valider_telephone_international


class DemandeCodeSerializer(serializers.Serializer):
    telephone = serializers.CharField(max_length=16, validators=[valider_telephone_international])


class VerificationCodeSerializer(serializers.Serializer):
    telephone = serializers.CharField(max_length=16, validators=[valider_telephone_international])
    code = serializers.RegexField(r"^\d{6}$")
    version_consentement = serializers.CharField(max_length=50)
    type_consentement = serializers.CharField(max_length=50, default="conditions_utilisation")