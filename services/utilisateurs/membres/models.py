from django.contrib.auth.hashers import check_password, make_password
from django.db import models


class UtilisateurBibliotheque(models.Model):
    class TypeUtilisateur(models.TextChoices):
        ETUDIANT = "etudiant", "Étudiant"
        PROFESSEUR = "professeur", "Professeur"
        GESTIONNAIRE = "gestionnaire", "Gestionnaire"
        ADMIN = "admin", "Administrateur"

    nom = models.CharField(max_length=120)
    prenom = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=30, blank=True)
    departement = models.CharField(max_length=120, blank=True)
    numero_carte = models.CharField(max_length=60, unique=True)
    mot_de_passe = models.CharField(max_length=128)
    type_utilisateur = models.CharField(
        max_length=20,
        choices=TypeUtilisateur.choices,
        default=TypeUtilisateur.ETUDIANT,
    )
    actif = models.BooleanField(default=True)
    cree_le = models.DateTimeField(auto_now_add=True)
    modifie_le = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nom", "prenom"]

    def __str__(self):
        return f"{self.prenom} {self.nom}"

    def set_password(self, raw_password):
        self.mot_de_passe = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.mot_de_passe)
