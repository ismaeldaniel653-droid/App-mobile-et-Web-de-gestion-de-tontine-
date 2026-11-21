from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from apps.tontines.models import Adhesion, Cycle


class Cotisation(models.Model):
    class Statut(models.TextChoices):
        PAYE = "paye", "Paye"
        PARTIEL = "partiel", "Partiel"
        EN_RETARD = "en_retard", "En retard"
        ABSENT = "absent", "Absent"

    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, related_name="cotisations")
    adhesion = models.ForeignKey(Adhesion, on_delete=models.CASCADE, related_name="cotisations")
    montant_du = models.PositiveIntegerField(default=0)
    montant_paye = models.PositiveIntegerField(default=0)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.ABSENT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cycle", "adhesion"], name="cotisation_cycle_adhesion_unique")
        ]
        ordering = ["adhesion__utilisateur__telephone"]

    def clean(self):
        super().clean()
        if self.adhesion.tontine_id != self.cycle.tontine_id:
            raise ValidationError("La cotisation doit appartenir a la meme tontine que le cycle.")

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.adhesion} - {self.cycle}"


class Penalite(models.Model):
    cotisation = models.ForeignKey(Cotisation, on_delete=models.CASCADE, related_name="penalites")
    type = models.CharField(max_length=30, default="retard")
    montant = models.PositiveIntegerField(default=0)
    regle_appliquee = models.JSONField(default=dict, blank=True)
    motif = models.CharField(max_length=255, blank=True, default="")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["cotisation", "type"], name="penalite_cotisation_type_unique")
        ]
        ordering = ["-date"]

    def __str__(self):
        return f"Penalite {self.type} - {self.montant} FCFA"


class Paiement(models.Model):
    class Mode(models.TextChoices):
        CASH = "cash", "Cash"
        MOMO = "momo", "MoMo"
        ORANGE_MONEY = "orange_money", "Orange Money"

    cotisation = models.ForeignKey(Cotisation, on_delete=models.PROTECT, related_name="paiements")
    montant = models.IntegerField()
    mode = models.CharField(max_length=30, choices=Mode.choices, default=Mode.CASH)
    reference_transaction = models.CharField(max_length=120, unique=True)
    enregistre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="paiements_enregistres")
    date = models.DateTimeField(auto_now_add=True)
    preuve = models.CharField(max_length=255, blank=True, default="")
    code_verification = models.CharField(max_length=6)
    annulation_de = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="annulations")
    motif_annulation = models.CharField(max_length=255, blank=True, default="")

    class Meta:
        ordering = ["-date"]

    def save(self, *args, **kwargs):
        if self.pk:
            ancien = Paiement.objects.filter(pk=self.pk).first()
            if ancien and (
                ancien.cotisation_id != self.cotisation_id
                or ancien.montant != self.montant
                or ancien.mode != self.mode
                or ancien.reference_transaction != self.reference_transaction
                or ancien.enregistre_par_id != self.enregistre_par_id
                or ancien.code_verification != self.code_verification
                or ancien.annulation_de_id != self.annulation_de_id
            ):
                raise ValueError("Un paiement ne peut pas etre modifie. Une annulation doit creer une nouvelle ecriture.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise models.ProtectedError("Un paiement ne peut pas etre supprime. Une annulation doit creer une nouvelle ecriture.", self)

    def __str__(self):
        return f"Paiement {self.reference_transaction} - {self.montant} FCFA"
