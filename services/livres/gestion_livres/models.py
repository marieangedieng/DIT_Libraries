from django.db import models


class Livre(models.Model):
    titre = models.CharField(max_length=255)
    auteur = models.CharField(max_length=255)
    isbn = models.CharField(max_length=32, unique=True)
    categorie = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    langue = models.CharField(max_length=50, default="Français")
    date_publication = models.DateField(null=True, blank=True)
    image_url = models.URLField(blank=True)
    quantite_totale = models.PositiveIntegerField(default=1)
    quantite_disponible = models.PositiveIntegerField(default=1)
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["titre"]

    def __str__(self):
        return f"{self.titre} - {self.auteur}"


class DemandeLivre(models.Model):
    class Statut(models.TextChoices):
        EN_COURS_TRAITEMENT = "en_cours_traitement", "En cours de traitement"
        EN_ATTENTE_LIVRE = "en_attente_livre", "En attente du livre"
        REFUSE = "refuse", "Refusé"
        LIVRE_DISPONIBLE = "livre_disponible", "Livre disponible"
        CLOTUREE = "cloturee", "Clôturée"

    utilisateur_id = models.PositiveIntegerField()
    utilisateur_nom = models.CharField(max_length=255)
    titre = models.CharField(max_length=255)
    auteur = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=32, blank=True)
    categorie_suggeree = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    commentaire_gestionnaire = models.TextField(blank=True)
    statut = models.CharField(
        max_length=32,
        choices=Statut.choices,
        default=Statut.EN_COURS_TRAITEMENT,
    )
    fermee_le = models.DateTimeField(null=True, blank=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-cree_le"]

    def __str__(self):
        return f"{self.titre} ({self.utilisateur_nom})"
