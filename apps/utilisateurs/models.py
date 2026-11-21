import re

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import PermissionsMixin
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models


def valider_telephone_international(valeur):
    if not re.fullmatch(r"\+[1-9]\d{7,14}", valeur):
        raise ValidationError("Le numero doit etre au format international, par exemple +237XXXXXXXXX.")


class GestionnaireUtilisateur(BaseUserManager):
    def create_user(self, telephone, password=None, **champs):
        if not telephone:
            raise ValueError("Un numero de telephone est obligatoire.")
        utilisateur = self.model(telephone=telephone.strip(), **champs)
        if password:
            utilisateur.set_password(password)
        else:
            utilisateur.set_unusable_password()
        utilisateur.save(using=self._db)
        return utilisateur

    def create_superuser(self, telephone, password=None, **champs):
        champs.setdefault("is_staff", True)
        champs.setdefault("is_superuser", True)
        champs.setdefault("is_active", True)
        if not champs["is_staff"] or not champs["is_superuser"]:
            raise ValueError("Un superutilisateur doit avoir les droits administrateur.")
        return self.create_user(telephone, password, **champs)


class Utilisateur(AbstractBaseUser, PermissionsMixin):
    class Statut(models.TextChoices):
        ACTIF = "actif", "Actif"
        SUSPENDU = "suspendu", "Suspendu"

    telephone = models.CharField(
        max_length=16,
        unique=True,
        validators=[valider_telephone_international],
    )
    nom = models.CharField(max_length=150, blank=True)
    ville = models.CharField(max_length=100, blank=True)
    langue = models.CharField(max_length=5, default="fr")
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.ACTIF)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_inscription = models.DateTimeField(auto_now_add=True)

    objects = GestionnaireUtilisateur()

    USERNAME_FIELD = "telephone"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.telephone


class CodeOtp(models.Model):
    telephone = models.CharField(
        max_length=16,
        db_index=True,
        validators=[valider_telephone_international],
    )
    code_hash = models.CharField(max_length=128)
    cree_le = models.DateTimeField(auto_now_add=True, db_index=True)
    expiration = models.DateTimeField()
    tentatives = models.PositiveSmallIntegerField(default=0)
    utilise = models.BooleanField(default=False)

    class Meta:
        ordering = ["-cree_le"]


class Consentement(models.Model):
    utilisateur = models.ForeignKey(
        Utilisateur,
        on_delete=models.PROTECT,
        related_name="consentements",
    )
    type_consentement = models.CharField(max_length=50, default="conditions_utilisation")
    version_texte = models.CharField(max_length=50)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["utilisateur", "type_consentement", "version_texte"],
                name="consentement_utilisateur_type_version_unique",
            )
        ]