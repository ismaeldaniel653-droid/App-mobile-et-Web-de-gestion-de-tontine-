from django.conf import settings
from django.db import models

from apps.tontines.models import Adhesion, Cycle, Tontine


class Defaut(models.Model):
    class ModeRepartition(models.TextChoices):
        EGAL = "egal", "Egal"
        SELON_MAINS = "selon_mains", "Selon mains"

    class Statut(models.TextChoices):
        OUVERT = "ouvert", "Ouvert"
        TRAITE = "traite", "Traite"

    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, related_name="defauts")
    adhesion = models.ForeignKey(Adhesion, on_delete=models.CASCADE, related_name="defauts")
    montant_manquant = models.PositiveIntegerField(default=0)
    mode_repartition = models.CharField(max_length=30, choices=ModeRepartition.choices, default=ModeRepartition.EGAL)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.OUVERT)
    date_constat = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_constat"]

    def __str__(self):
        return f"Defaut {self.cycle_id} - {self.adhesion_id}"


class RepartitionDefaut(models.Model):
    defaut = models.ForeignKey(Defaut, on_delete=models.CASCADE, related_name="repartitions")
    adhesion = models.ForeignKey(Adhesion, on_delete=models.CASCADE, related_name="repartitions_defaut")
    montant_du = models.PositiveIntegerField(default=0)
    montant_paye = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["defaut", "adhesion"], name="repartition_defaut_unique"),
        ]

    def __str__(self):
        return f"Repartition {self.defaut_id} - {self.adhesion_id}"


class MouvementReserve(models.Model):
    class Sens(models.TextChoices):
        ENTREE = "entree", "Entree"
        SORTIE = "sortie", "Sortie"

    tontine = models.ForeignKey(Tontine, on_delete=models.CASCADE, related_name="mouvements_reserve")
    cycle = models.ForeignKey(Cycle, on_delete=models.CASCADE, related_name="mouvements_reserve")
    sens = models.CharField(max_length=20, choices=Sens.choices, default=Sens.ENTREE)
    montant = models.PositiveIntegerField(default=0)
    motif = models.CharField(max_length=255, blank=True, default="")
    enregistre_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mouvements_reserve")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Mouvement reserve {self.sens} - {self.montant} FCFA"
