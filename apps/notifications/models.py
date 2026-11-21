from django.conf import settings
from django.db import models


class Notification(models.Model):
    class Canal(models.TextChoices):
        PUSH = "push", "Push"
        SMS = "sms", "Sms"

    class Statut(models.TextChoices):
        ENVOYEE = "envoyee", "Envoyee"
        ECHEC = "echec", "Echec"

    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    canal = models.CharField(max_length=20, choices=Canal.choices, default=Canal.PUSH)
    message = models.TextField()
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.ENVOYEE)
    cout_estime = models.PositiveIntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"Notification {self.utilisateur} - {self.canal}"
