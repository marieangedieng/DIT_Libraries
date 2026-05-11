from django.db import models
from django.utils import timezone


class Emprunt(models.Model):
    class Statut(models.TextChoices):
        EN_COURS = "en_cours", "En cours"
        RETOURNE = "retourne", "Retourné"
        EN_RETARD = "en_retard", "En retard"

    utilisateur_id = models.PositiveIntegerField()
    utilisateur_nom = models.CharField(max_length=255)
    livre_id = models.PositiveIntegerField()
    livre_titre = models.CharField(max_length=255)
    date_emprunt = models.DateField(default=timezone.localdate)
    date_retour_prevue = models.DateField()
    date_retour_effective = models.DateField(null=True, blank=True)
    statut = models.CharField(max_length=20, choices=Statut.choices, default=Statut.EN_COURS)
    commentaire = models.TextField(blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date_emprunt", "-cree_le"]

    def __str__(self):
        return f"{self.utilisateur_nom} -> {self.livre_titre}"
