from django.conf import settings
from django.db import models


class JournalAudit(models.Model):
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="journal_audit")
    action = models.CharField(max_length=120)
    objet = models.CharField(max_length=120)
    ancienne_valeur = models.TextField(blank=True, default="")
    nouvelle_valeur = models.TextField(blank=True, default="")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.action} - {self.objet}"


class Contestation(models.Model):
    class Statut(models.TextChoices):
        OUVERTE = "ouverte", "Ouverte"
        TRAITEE = "traitee", "Traitee"

    adhesion = models.ForeignKey("tontines.Adhesion", on_delete=models.CASCADE, related_name="contestations")
    type_objet = models.CharField(max_length=30)
    id_objet = models.PositiveIntegerField()
    motif = models.TextField(blank=True, default="")
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.OUVERTE)
    traitee_par = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="contestations_traitees")
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Contestation {self.type_objet}#{self.id_objet}"
