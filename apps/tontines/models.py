from django.conf import settings
from django.db import models


class Tontine(models.Model):
    class Frequence(models.TextChoices):
        HEBDOMADAIRE = "hebdomadaire", "Hebdomadaire"
        MENSUELLE = "mensuelle", "Mensuelle"

    class ModePassage(models.TextChoices):
        ORDRE_FIXE = "ordre_fixe", "Ordre fixe"
        ENCHERES = "encheres", "Encheres"

    class Statut(models.TextChoices):
        ACTIVE = "active", "Active"
        FERMEE = "fermee", "Fermee"

    nom = models.CharField(max_length=150)
    montant_cotisation = models.PositiveIntegerField()
    frequence = models.CharField(max_length=20, choices=Frequence.choices, default=Frequence.HEBDOMADAIRE)
    nombre_mains_total = models.PositiveSmallIntegerField(default=1)
    mode_passage = models.CharField(max_length=20, choices=ModePassage.choices, default=ModePassage.ORDRE_FIXE)
    pourcentage_reserve = models.PositiveSmallIntegerField(default=0)
    date_debut = models.DateField()
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.ACTIVE)
    regles_penalite = models.JSONField(default=dict, blank=True)
    cree_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="tontines_creees")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return self.nom


class Adhesion(models.Model):
    class Role(models.TextChoices):
        PRESIDENT = "president", "President"
        TRESORIER = "tresorier", "Tresorier"
        MEMBRE = "membre", "Membre"

    class Statut(models.TextChoices):
        ACTIF = "actif", "Actif"
        SUSPENDU = "suspendu", "Suspendu"

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="adhesions")
    tontine = models.ForeignKey(Tontine, on_delete=models.CASCADE, related_name="adhesions")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBRE)
    mains = models.PositiveSmallIntegerField(default=1)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.ACTIF)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["utilisateur", "tontine"], name="adhesion_unique_par_utilisateur_et_tontine")
        ]

    def __str__(self):
        return f"{self.utilisateur} - {self.tontine}"


class Invitation(models.Model):
    tontine = models.ForeignKey(Tontine, on_delete=models.CASCADE, related_name="invitations")
    jeton = models.CharField(max_length=64, unique=True)
    role_propose = models.CharField(max_length=20, choices=Adhesion.Role.choices, default=Adhesion.Role.MEMBRE)
    expire_le = models.DateTimeField()
    usage_unique = models.BooleanField(default=True)
    utilise_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="invitations_utilisees")

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        return f"Invitation {self.jeton[:8]}"


class Cycle(models.Model):
    class Statut(models.TextChoices):
        A_VENIR = "a_venir", "A venir"
        OUVERT = "ouvert", "Ouvert"
        TERMINE = "termine", "Termine"

    tontine = models.ForeignKey(Tontine, on_delete=models.CASCADE, related_name="cycles")
    numero = models.PositiveSmallIntegerField(default=1)
    date_limite = models.DateField()
    montant_a_verser = models.PositiveIntegerField(default=0)
    montant_encaisse = models.PositiveIntegerField(default=0)
    beneficiaire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="cycles_beneficiaires",
    )
    montant_offert = models.PositiveIntegerField(default=0)
    interet_distribue = models.PositiveIntegerField(default=0)
    regle_penalite_appliquee = models.JSONField(default=dict, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.A_VENIR)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["tontine", "numero"], name="cycle_tontine_numero_unique"),
        ]
        ordering = ["numero"]

    def clean(self):
        super().clean()
        if self.beneficiaire_id and (self.montant_offert > 0 or self.interet_distribue > 0):
            raise ValueError("Un cycle ne peut pas avoir a la fois un beneficiaire d'ordre fixe et une enchere.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"Cycle {self.numero} - {self.tontine}"